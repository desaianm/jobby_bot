"""Discord bot interface for Jobby Bot multi-agent system."""

import asyncio
import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
import discord
from discord.ext import commands

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition, HookMatcher
from jobby_bot.utils.subagent_tracker import SubagentTracker
from jobby_bot.utils.transcript import setup_session, TranscriptWriter
from jobby_bot.utils.message_handler import process_assistant_message
from jobby_bot.auto_job_monitor import AutoJobMonitor

# Load environment variables
load_dotenv()

# Paths
PROMPTS_DIR = Path(__file__).parent / "prompts"


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
        notion_agent_prompt = load_prompt("notion_agent.txt")

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
            command_prefix="!jobby ",
            intents=intents,
            help_command=None
        )

        self.sessions: Dict[int, JobbySession] = {}
        self.enable_auto_monitor = enable_auto_monitor
        self.auto_monitor: Optional[AutoJobMonitor] = None
        self.monitor_task: Optional[asyncio.Task] = None

    async def setup_hook(self):
        """Called when the bot is ready."""
        print(f"🤖 Jobby Bot logged in as {self.user}")

        # Start auto job monitoring if enabled
        if self.enable_auto_monitor:
            check_interval = int(os.getenv("JOB_CHECK_INTERVAL_MINUTES", "30"))
            print(f"🔄 Starting auto job monitor (interval: {check_interval} minutes)...")
            self.auto_monitor = AutoJobMonitor(check_interval_minutes=check_interval)
            self.monitor_task = asyncio.create_task(self.auto_monitor.run_monitoring_loop())
            print("✅ Auto job monitor started")

    async def get_or_create_session(self, user_id: int) -> JobbySession:
        """Get existing session or create a new one for a user."""
        if user_id not in self.sessions:
            session = JobbySession(user_id)
            await session.initialize()
            self.sessions[user_id] = session
        return self.sessions[user_id]

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


# Define commands
@commands.command(name="start")
async def start_session(ctx: commands.Context):
    """Start a new Jobby Bot session."""
    await ctx.send(
        "👋 **Welcome to Jobby Bot!**\n\n"
        "I can help you with:\n"
        "🔍 Search for jobs across LinkedIn, Indeed, and Google\n"
        "📄 Generate customized ATS-optimized resumes\n"
        "✍️ Write personalized cover letters\n"
        "📊 Track applications in Notion\n\n"
        "**How to use:**\n"
        "• Send me a DM with your request\n"
        "• Or mention me in a channel: `@Jobby Bot your message`\n\n"
        "**Commands:**\n"
        "• `!jobby start` - Show this message\n"
        "• `!jobby end` - End your current session\n"
        "• `!jobby help` - Get detailed help\n\n"
        "Just start chatting with me to begin!"
    )


@commands.command(name="end")
async def end_session(ctx: commands.Context):
    """End the current session for the user."""
    bot = ctx.bot
    user_id = ctx.author.id

    if user_id in bot.sessions:
        session = bot.sessions[user_id]
        await session.cleanup()
        del bot.sessions[user_id]
        await ctx.send(
            f"👋 Session ended!\n"
            f"📁 Your session logs: `{session.session_dir}`"
        )
    else:
        await ctx.send("No active session found. Use `!jobby start` to begin!")


@commands.command(name="help")
async def help_command(ctx: commands.Context):
    """Show detailed help information."""
    help_text = """
📚 **Jobby Bot Help**

**What I can do:**
• Find jobs matching your criteria
• Generate ATS-optimized resumes
• Write personalized cover letters
• Track applications in Notion

**Example requests:**
• "Find me software engineer jobs in San Francisco"
• "Create a resume for this job posting: [URL]"
• "Write a cover letter for the Data Scientist position at Google"
• "Track this application in Notion"

**Setup Requirements:**
• Base resume in `user_data/base_resume.json` (JSON Resume format)
• For Notion tracking: Set `NOTION_API_KEY` and `NOTION_DATABASE_ID`

**Commands:**
• `!jobby start` - Start a new session
• `!jobby end` - End your current session
• `!jobby help` - Show this help

**Tips:**
• Be specific about job criteria (location, role, experience level)
• Provide job descriptions for best resume/cover letter results
• Sessions persist until you use `!jobby end`
"""
    await ctx.send(help_text)


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

    # Register commands
    bot.add_command(start_session)
    bot.add_command(end_session)
    bot.add_command(help_command)

    print("\n" + "="*60)
    print("🤖 JOBBY BOT - Discord Integration")
    print("="*60)
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
