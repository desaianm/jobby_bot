"""Discord bot interface for Jobby Bot multi-agent system using Agno."""

import asyncio
import os
from pathlib import Path
from typing import Dict, Optional
import json
from datetime import datetime
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands, tasks

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.team import Team

from jobby_bot.agent import (
    search_jobs,
    read_file,
    write_file,
    generate_pdf,
    screenshot_pdf,
    generate_html_from_text,
    generate_pdf_from_html,
    create_notion_entry,
    send_email,
    validate_job_url,
    load_prompt,
)

# Load environment variables
load_dotenv()

# Paths - user_data is inside the jobby_bot module
USER_DATA_DIR = Path(__file__).parent / "user_data"


class JobbySession:
    """Manages a single user's Jobby Bot session using Agno."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.team: Optional[Team] = None
        self.is_processing = False
        self.conversation_history: list = []  # Track recent conversation for context
        self.last_created_files: dict = {}  # Track files created in this session

    async def initialize(self):
        """Initialize the Agno team."""
        # Load prompts
        job_finder_prompt = load_prompt("job_finder.txt")
        resume_writer_prompt = load_prompt("resume_writer.txt")
        cover_letter_prompt = load_prompt("cover_letter.txt")
        notion_agent_prompt = load_prompt("notion_agent.txt")
        lead_agent_prompt = load_prompt("lead_agent.txt")

        # Check if debug mode is enabled via environment variable
        debug_mode = os.getenv("AGNO_DEBUG", "false").lower() == "true"
        debug_level = int(os.getenv("AGNO_DEBUG_LEVEL", "1"))

        # Create specialized agents
        job_finder = Agent(
            name="Job Finder",
            role="Search for jobs using JobSpy across LinkedIn, Indeed, and Google",
            model=Claude(id="claude-haiku-4-5-20251001"),
            tools=[search_jobs, validate_job_url, read_file, write_file],
            instructions=job_finder_prompt,
            markdown=True,
            debug_mode=debug_mode,
            debug_level=debug_level,
        )

        resume_writer = Agent(
            name="Resume Writer",
            role="Create customized ATS-optimized resumes for specific jobs",
            model=Claude(id="claude-haiku-4-5-20251001"),
            tools=[read_file, write_file, generate_pdf, screenshot_pdf, generate_html_from_text, generate_pdf_from_html],
            instructions=resume_writer_prompt,
            markdown=True,
            debug_mode=debug_mode,
            debug_level=debug_level,
        )

        cover_letter_writer = Agent(
            name="Cover Letter Writer",
            role="Generate personalized cover letters for job applications",
            model=Claude(id="claude-haiku-4-5-20251001"),
            tools=[read_file, write_file, generate_pdf, screenshot_pdf, generate_html_from_text, generate_pdf_from_html],
            instructions=cover_letter_prompt,
            markdown=True,
            debug_mode=debug_mode,
            debug_level=debug_level,
        )

        notion_agent = Agent(
            name="Notion Agent",
            role="Track job applications in Notion database",
            model=Claude(id="claude-haiku-4-5-20251001"),
            tools=[create_notion_entry, read_file],
            instructions=notion_agent_prompt,
            markdown=True,
            debug_mode=debug_mode,
            debug_level=debug_level,
        )

        email_agent = Agent(
            name="Email Agent",
            role="Send job application emails with attachments",
            model=Claude(id="claude-haiku-4-5-20251001"),
            tools=[send_email, read_file],
            instructions="Send professional job application emails with resume and cover letter attachments.",
            markdown=True,
            debug_mode=debug_mode,
            debug_level=debug_level,
        )

        # Create team with lead agent
        self.team = Team(
            name="Jobby Bot Team",
            model=Claude(id="claude-sonnet-4-5-20250929"),
            members=[
                job_finder,
                resume_writer,
                cover_letter_writer,
                notion_agent,
                email_agent,
            ],
            instructions=lead_agent_prompt,
            markdown=True,
            show_members_responses=True,  # Show member responses for debugging
            get_member_information_tool=True,
            add_member_tools_to_context=True,
            debug_mode=debug_mode,
            debug_level=debug_level,
        )

    def _load_user_context(self) -> str:
        """Load user preferences and resume info to inject into messages."""
        context_parts = []

        # Load preferences
        prefs_file = USER_DATA_DIR / "preferences.json"
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                default_search = prefs.get('default_search', {})
                context_parts.append(f"""<user_preferences>
Search Term: {default_search.get('search_term', 'not set')}
Location: {default_search.get('location', 'not set')}
Remote: {default_search.get('is_remote', False)}
Results Wanted: {default_search.get('results_wanted', 20)}
</user_preferences>""")
            except Exception:
                pass

        # Load resume info
        resume_file = USER_DATA_DIR / "base_resume.json"
        if resume_file.exists():
            try:
                with open(resume_file, 'r') as f:
                    resume = json.load(f)
                basics = resume.get('basics', {})
                context_parts.append(f"""<user_resume>
Name: {basics.get('name', 'not set')}
Email: {basics.get('email', 'not set')}
Resume file: user_data/base_resume.json (EXISTS)
</user_resume>""")
            except Exception:
                pass

        return "\n".join(context_parts)

    def _build_conversation_context(self) -> str:
        """Build conversation history context for the agent."""
        if not self.conversation_history:
            return ""

        # Keep last 5 exchanges for context
        recent = self.conversation_history[-10:]  # 5 user + 5 assistant messages
        context_lines = ["<conversation_history>"]
        for entry in recent:
            role = entry.get('role', 'user')
            content = entry.get('content', '')[:500]  # Truncate long messages
            context_lines.append(f"{role}: {content}")
        context_lines.append("</conversation_history>")
        return "\n".join(context_lines)

    def _build_files_context(self) -> str:
        """Build context about recently created files."""
        if not self.last_created_files:
            return ""

        lines = ["<recently_created_files>"]
        for file_type, path in self.last_created_files.items():
            lines.append(f"{file_type}: {path}")
        lines.append("</recently_created_files>")
        return "\n".join(lines)

    async def process_message(self, message: str) -> str:
        """Process a user message and return the agent's response."""
        if self.is_processing:
            return "⏳ I'm still processing your previous request. Please wait..."

        self.is_processing = True

        try:
            # Build full context
            user_context = self._load_user_context()
            conversation_context = self._build_conversation_context()
            files_context = self._build_files_context()

            # Combine all context
            context_parts = [p for p in [user_context, conversation_context, files_context] if p]
            full_context = "\n\n".join(context_parts)

            if full_context:
                enhanced_message = f"{full_context}\n\n<user_message>{message}</user_message>"
            else:
                enhanced_message = message

            # Add user message to history
            self.conversation_history.append({"role": "user", "content": message})

            # Run the team synchronously in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.team.run(enhanced_message)
            )

            # Extract text from response
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)

            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response_text})

            # Track created files from response
            self._track_created_files(response_text)

            return response_text

        except Exception as e:
            return f"❌ Error: {str(e)}"
        finally:
            self.is_processing = False

    def _track_created_files(self, response: str):
        """Extract and track file paths mentioned in response."""
        import re
        # Look for resume paths
        resume_match = re.search(r'output/resumes/([^\s]+\.pdf)', response)
        if resume_match:
            self.last_created_files['resume'] = f"output/resumes/{resume_match.group(1)}"

        # Look for cover letter paths
        cover_match = re.search(r'output/cover_letters/([^\s]+\.pdf)', response)
        if cover_match:
            self.last_created_files['cover_letter'] = f"output/cover_letters/{cover_match.group(1)}"

        # Look for job listings
        jobs_match = re.search(r'output/job_listings/([^\s]+\.csv)', response)
        if jobs_match:
            self.last_created_files['job_listings'] = f"output/job_listings/{jobs_match.group(1)}"

    async def cleanup(self):
        """Clean up session resources."""
        self.team = None


class JobbyBot(commands.Bot):
    """Discord bot for Jobby Bot job application assistant using Agno."""

    def __init__(self, enable_auto_monitor: bool = False):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        self.sessions: Dict[int, JobbySession] = {}
        self.enable_auto_monitor = enable_auto_monitor
        self.check_interval_minutes = int(os.getenv("JOB_CHECK_INTERVAL_MINUTES", "30"))
        self.monitor_session: Optional[JobbySession] = None

    async def setup_hook(self):
        """Called when the bot is ready."""
        await self.tree.sync()
        print(f"🤖 Jobby Bot logged in as {self.user}")
        print(f"✅ Slash commands synced")

        if self.enable_auto_monitor:
            print(f"🔄 Starting auto job monitor (interval: {self.check_interval_minutes} minutes)...")
            self.monitor_session = JobbySession(user_id=0)
            await self.monitor_session.initialize()
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

            preferences_file = USER_DATA_DIR / "preferences.json"
            if not preferences_file.exists():
                print("⚠️ No preferences.json found. Skipping check.")
                return

            with open(preferences_file, 'r') as f:
                preferences = json.load(f)

            default_search = preferences.get('default_search', {})
            search_term = default_search.get('search_term', 'software engineer')
            location = default_search.get('location', '')
            is_remote = default_search.get('is_remote', False)
            results_wanted = default_search.get('results_wanted', 10)

            hours_old = max(1, self.check_interval_minutes // 30 + 1)
            query = f"Search for {results_wanted} {search_term} jobs posted in the last {hours_old} hours"

            if location:
                query += f" in {location}"
            if is_remote:
                query += " (remote positions only)"

            query += ". Generate resumes and cover letters for matches, then send individual emails for each job to the configured recipient."

            print(f"📋 Query: {query}")

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
        self.auto_job_check.change_interval(minutes=self.check_interval_minutes)
        print(f"⏱️ Auto job check interval set to {self.check_interval_minutes} minutes")

    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        if message.author == self.user:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.user in message.mentions

        if not (is_dm or is_mentioned):
            await self.process_commands(message)
            return

        content = message.content
        if is_mentioned:
            content = content.replace(f'<@{self.user.id}>', '').strip()

        if not content:
            return

        async with message.channel.typing():
            try:
                session = await self.get_or_create_session(message.author.id)
                response = await session.process_message(content)

                if len(response) <= 2000:
                    await message.reply(response)
                else:
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

    enable_monitor = os.getenv("ENABLE_AUTO_JOB_MONITOR", "false").lower() == "true"

    bot = JobbyBot(enable_auto_monitor=enable_monitor)

    bot.tree.add_command(start_command)
    bot.tree.add_command(help_command)
    bot.tree.add_command(end_command)
    bot.tree.add_command(upload_resume_command)
    bot.tree.add_command(set_preferences_command)
    bot.tree.add_command(show_preferences_command)
    bot.tree.add_command(show_resume_command)

    print("\n" + "="*60)
    print("🤖 JOBBY BOT - Discord Integration (Agno Framework)")
    print("="*60)
    print("✅ Using Agno multi-agent framework")
    print("✅ PDF generation with WeasyPrint (no Chrome needed)")
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
        for session in bot.sessions.values():
            await session.cleanup()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
