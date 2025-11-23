"""Discord bot interface for Jobby Bot multi-agent system."""

import asyncio
import os
from pathlib import Path
from typing import Dict, Optional
import tempfile
import json
from datetime import datetime
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands, tasks

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition, HookMatcher
from jobby_bot.utils.subagent_tracker import SubagentTracker
from jobby_bot.utils.transcript import setup_session, TranscriptWriter
from jobby_bot.utils.message_handler import process_assistant_message

# Load environment variables
load_dotenv()

# Paths
PROMPTS_DIR = Path(__file__).parent / "prompts"
USER_DATA_DIR = Path(__file__).parent / "user_data"


def load_prompt(filename: str) -> str:
    """Load a prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


class JobbySession:
    """Manages a single user's Jobby Bot session."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client: Optional[ClaudeSDKClient] = None
        self.transcript: Optional[TranscriptWriter] = None
        self.tracker: Optional[SubagentTracker] = None
        self.session_dir: Optional[Path] = None
        self.is_processing = False

    async def initialize(self):
        """Initialize the Claude agent and session tracking."""
        # Setup session directory and transcript
        transcript_file, session_dir = setup_session()
        self.session_dir = session_dir

        # Create transcript writer
        self.transcript = TranscriptWriter(transcript_file)

        # Load prompts
        lead_agent_prompt = load_prompt("lead_agent.txt")
        job_finder_prompt = load_prompt("job_finder.txt")
        resume_writer_prompt = load_prompt("resume_writer.txt")
        cover_letter_prompt = load_prompt("cover_letter.txt")
        email_agent_prompt = load_prompt("email_agent.txt")
        notion_agent_prompt = load_prompt("notion_agent.txt")
        config_agent_prompt = load_prompt("config_agent.txt")

        # Initialize subagent tracker
        self.tracker = SubagentTracker(
            transcript_writer=self.transcript,
            session_dir=session_dir
        )

        # Define specialized subagents
        agents = {
            "job-finder": AgentDefinition(
                description=(
                    "Use this agent when you need to search for jobs. "
                    "The job-finder uses JobSpy to scrape jobs from LinkedIn, Indeed, and Google "
                    "with filtering based on user preferences. Writes results to output/job_listings/ "
                    "for use by other agents. Returns structured job data with titles, companies, URLs, and descriptions."
                ),
                tools=["Bash", "Read", "Write", "Glob"],
                prompt=job_finder_prompt,
                model="haiku"
            ),
            "resume-writer": AgentDefinition(
                description=(
                    "Use this agent when you need to create a customized resume for a specific job. "
                    "The resume-writer reads the base resume from user_data/base_resume.json and optimizes it "
                    "for ATS (Applicant Tracking Systems) by incorporating keywords from the job description. "
                    "Generates both markdown and plain text versions in output/resumes/. "
                    "Does NOT search for jobs - only creates resumes for jobs you provide."
                ),
                tools=["Read", "Write"],
                prompt=resume_writer_prompt,
                model="haiku"
            ),
            "cover-letter": AgentDefinition(
                description=(
                    "Use this agent when you need to generate a personalized cover letter for a job application. "
                    "The cover-letter agent reads the base resume and job description, then creates a compelling "
                    "3-paragraph cover letter that matches the candidate's experience with job requirements. "
                    "Saves to output/cover_letters/. Does NOT search for jobs or create resumes."
                ),
                tools=["Read", "Write"],
                prompt=cover_letter_prompt,
                model="haiku"
            ),
            "email-agent": AgentDefinition(
                description=(
                    "Use this agent when you need to send job application emails. "
                    "The email-agent sends individual emails per job with resume and cover letter attachments, "
                    "or sends a daily summary email with all applications. "
                    "Does NOT search for jobs or create materials - only sends emails."
                ),
                tools=["Bash", "Read"],
                prompt=email_agent_prompt,
                model="haiku"
            ),
            "notion-agent": AgentDefinition(
                description=(
                    "Use this agent when you need to track job applications in Notion. "
                    "The notion-agent creates entries in your Notion database with job details, "
                    "application status, and links to generated resumes/cover letters. "
                    "Requires NOTION_API_KEY and NOTION_DATABASE_ID in environment. "
                    "Does NOT search for jobs or create materials - only tracks them."
                ),
                tools=["Bash", "Read", "Write"],
                prompt=notion_agent_prompt,
                model="haiku"
            ),
            "config-agent": AgentDefinition(
                description=(
                    "Use this agent when you need to update user preferences or save resume data. "
                    "The config-agent updates preferences.json when user wants to change job search settings "
                    "(location, remote preference, blacklist, tech stack, etc.) and updates base_resume.json "
                    "when user provides their resume information. Does NOT search for jobs or create materials."
                ),
                tools=["Read", "Write"],
                prompt=config_agent_prompt,
                model="haiku"
            )
        }

        # Set up hooks for tracking
        hooks = {
            'PreToolUse': [
                HookMatcher(
                    matcher=None,
                    hooks=[self.tracker.pre_tool_use_hook]
                )
            ],
            'PostToolUse': [
                HookMatcher(
                    matcher=None,
                    hooks=[self.tracker.post_tool_use_hook]
                )
            ]
        }

        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=lead_agent_prompt,
            allowed_tools=["Task"],
            agents=agents,
            hooks=hooks,
            model="haiku"
        )

        self.client = ClaudeSDKClient(options=options)
        await self.client.__aenter__()

    async def process_message(self, message: str) -> str:
        """Process a user message and return the agent's response."""
        if self.is_processing:
            return "⏳ I'm still processing your previous request. Please wait..."

        self.is_processing = True
        response_parts = []

        try:
            # Write user input to transcript
            self.transcript.write_to_file(f"\n💼 User ({self.user_id}): {message}\n")

            # Send to agent
            await self.client.query(prompt=message)

            self.transcript.write("🤖 Agent: ", end="")

            # Collect response
            async for msg in self.client.receive_response():
                if type(msg).__name__ == 'AssistantMessage':
                    # Process message and capture text output
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            response_parts.append(block.text)
                            self.transcript.write(block.text, end="")

            self.transcript.write("\n")

            # Return combined response
            return "\n".join(response_parts) if response_parts else "✅ Task completed!"

        finally:
            self.is_processing = False

    async def cleanup(self):
        """Clean up session resources."""
        if self.client:
            await self.client.__aexit__(None, None, None)
        if self.transcript:
            self.transcript.close()
        if self.tracker:
            self.tracker.close()


class JobbyBot(commands.Bot):
    """Discord bot for Jobby Bot job application assistant."""

    def __init__(self, enable_auto_monitor: bool = False):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True

        super().__init__(
            command_prefix="!",  # Keep for legacy support
            intents=intents,
            help_command=None
        )

        self.sessions: Dict[int, JobbySession] = {}
        self.enable_auto_monitor = enable_auto_monitor
        self.check_interval_minutes = int(os.getenv("JOB_CHECK_INTERVAL_MINUTES", "30"))
        self.monitor_session: Optional[JobbySession] = None

    async def setup_hook(self):
        """Called when the bot is ready."""
        # Sync slash commands
        await self.tree.sync()
        print(f"🤖 Jobby Bot logged in as {self.user}")
        print(f"✅ Slash commands synced")

        # Start auto job monitoring if enabled
        if self.enable_auto_monitor:
            print(f"🔄 Starting auto job monitor (interval: {self.check_interval_minutes} minutes)...")
            # Initialize a dedicated session for the monitor
            self.monitor_session = JobbySession(user_id=0)  # Use ID 0 for system monitor
            await self.monitor_session.initialize()
            # Start the loop
            self.auto_job_check.start()
            print("✅ Auto job monitor started")

    async def get_or_create_session(self, user_id: int) -> JobbySession:
        """Get existing session or create a new one for a user."""
        if user_id not in self.sessions:
            session = JobbySession(user_id)
            await session.initialize()
            self.sessions[user_id] = session
        return self.sessions[user_id]

    @tasks.loop(minutes=30)
    async def auto_job_check(self):
        """Automatically check for new jobs every N minutes."""
        try:
            print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running auto job check...")

            # Load user preferences
            preferences_file = USER_DATA_DIR / "preferences.json"
            if not preferences_file.exists():
                print("⚠️ No preferences.json found. Skipping check.")
                return

            with open(preferences_file, 'r') as f:
                preferences = json.load(f)

            # Get search parameters
            default_search = preferences.get('default_search', {})
            search_term = default_search.get('search_term', 'software engineer')
            location = default_search.get('location', '')
            is_remote = default_search.get('is_remote', False)
            results_wanted = default_search.get('results_wanted', 10)

            # Build query for recent jobs
            hours_old = max(1, self.check_interval_minutes // 30 + 1)
            query = f"Search for {results_wanted} {search_term} jobs posted in the last {hours_old} hours"

            if location:
                query += f" in {location}"
            if is_remote:
                query += " (remote positions only)"

            # Add email instruction
            query += ". Generate resumes and cover letters for matches, then send individual emails for each job to the configured recipient."

            print(f"📋 Query: {query}")

            # Execute through the monitor session
            if self.monitor_session:
                response = await self.monitor_session.process_message(query)
                print(f"✅ Auto job check completed")
                print(f"Response summary: {response[:200]}...")

        except Exception as e:
            print(f"❌ Error in auto job check: {e}")

    @auto_job_check.before_loop
    async def before_auto_job_check(self):
        """Wait until the bot is ready before starting the loop."""
        await self.wait_until_ready()
        # Update loop interval dynamically
        self.auto_job_check.change_interval(minutes=self.check_interval_minutes)
        print(f"⏱️  Auto job check interval set to {self.check_interval_minutes} minutes")

    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Ignore bot's own messages
        if message.author == self.user:
            return

        # Only respond to DMs or messages in channels where bot is mentioned
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.user in message.mentions

        if not (is_dm or is_mentioned):
            # Process commands
            await self.process_commands(message)
            return

        # Remove mention from message content
        content = message.content
        if is_mentioned:
            content = content.replace(f'<@{self.user.id}>', '').strip()

        # Ignore empty messages
        if not content:
            return

        # Show typing indicator
        async with message.channel.typing():
            try:
                session = await self.get_or_create_session(message.author.id)
                response = await session.process_message(content)

                # Split long responses to fit Discord's 2000 character limit
                if len(response) <= 2000:
                    await message.reply(response)
                else:
                    # Split into chunks
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)

            except Exception as e:
                error_msg = f"❌ Error processing request: {str(e)}"
                await message.reply(error_msg)
                print(f"Error in session {message.author.id}: {e}")


# Import slash commands
from jobby_bot.discord_commands import (
    help_command,
    end_command,
    upload_resume_command,
    set_preferences_command,
    show_preferences_command,
    show_resume_command
)


# Define start command inline
@app_commands.command(name="start", description="Show welcome message and bot capabilities")
async def start_command(interaction: discord.Interaction):
    """Start a new Jobby Bot session."""
    await interaction.response.send_message(
        "👋 **Welcome to Jobby Bot!**\n\n"
        "I can help you with:\n"
        "🔍 Search for jobs across LinkedIn, Indeed, and Google\n"
        "📄 Generate customized ATS-optimized resumes\n"
        "✍️ Write personalized cover letters\n"
        "📊 Track applications in Notion\n\n"
        "**How to use:**\n"
        "• Use `/` slash commands for setup and configuration\n"
        "• Send me a DM or mention me for job searches and requests\n\n"
        "**Slash Commands:**\n"
        "• `/start` - Show this message\n"
        "• `/help` - Get detailed help\n"
        "• `/upload-resume` - Upload your resume (PDF/TXT)\n"
        "• `/set-preferences` - Update job search settings\n"
        "• `/show-resume` - View your current resume\n"
        "• `/show-preferences` - View your settings\n"
        "• `/end` - End your current session\n\n"
        "Just mention me or DM me to start searching for jobs!",
        ephemeral=True
    )


async def main():
    """Start the Discord bot."""
    # Check for required API keys
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found.")
        print("Set it in a .env file or export it in your shell.")
        print("Get your key at: https://console.anthropic.com/settings/keys\n")
        return

    discord_token = os.environ.get("DISCORD_BOT_TOKEN")
    if not discord_token:
        print("\n❌ Error: DISCORD_BOT_TOKEN not found.")
        print("Set it in a .env file or export it in your shell.")
        print("Create a bot at: https://discord.com/developers/applications\n")
        return

    # Check if auto monitoring should be enabled
    enable_monitor = os.getenv("ENABLE_AUTO_JOB_MONITOR", "false").lower() == "true"

    # Create and run bot
    bot = JobbyBot(enable_auto_monitor=enable_monitor)

    # Register slash commands
    bot.tree.add_command(start_command)
    bot.tree.add_command(help_command)
    bot.tree.add_command(end_command)
    bot.tree.add_command(upload_resume_command)
    bot.tree.add_command(set_preferences_command)
    bot.tree.add_command(show_preferences_command)
    bot.tree.add_command(show_resume_command)

    print("\n" + "="*60)
    print("🤖 JOBBY BOT - Discord Integration (Slash Commands)")
    print("="*60)
    print("✅ Using modern Discord slash commands (/start, /help, etc.)")
    if enable_monitor:
        check_interval = int(os.getenv("JOB_CHECK_INTERVAL_MINUTES", "30"))
        print(f"🔄 Auto job monitoring: ENABLED (every {check_interval} minutes)")
    else:
        print("📊 Auto job monitoring: DISABLED")
        print("   Set ENABLE_AUTO_JOB_MONITOR=true in .env to enable")
    print("\nStarting Discord bot...")
    print("Press Ctrl+C to stop.\n")

    try:
        await bot.start(discord_token)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        # Stop auto monitor if running
        if bot.auto_monitor and bot.monitor_task:
            print("🛑 Stopping auto job monitor...")
            await bot.auto_monitor.stop()
            bot.monitor_task.cancel()
            try:
                await bot.monitor_task
            except asyncio.CancelledError:
                pass
        # Clean up all sessions
        for session in bot.sessions.values():
            await session.cleanup()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
