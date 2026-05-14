"""Discord bot interface for Jobby Bot multi-agent system using Agno."""

import asyncio
import os
from pathlib import Path
from typing import Dict, Optional, List
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
    track_application,
    update_application_status,
    send_email,
    validate_job_url,
    apply_to_job,
    load_prompt,
)
from jobby_bot.database import (
    init_db,
    get_or_create_user,
    get_user_resume,
    get_user_preferences,
    save_user_preferences,
    get_auto_monitor_users,
    get_monitor_state,
    save_monitor_state,
)

# Load environment variables
load_dotenv()

# Paths - user_data is inside the jobby_bot module (kept for backward compatibility)
USER_DATA_DIR = Path(__file__).parent / "user_data"
# Output directory for per-user files
OUTPUT_DIR = Path(__file__).parent.parent / "output"


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

        tracker_agent = Agent(
            name="Tracker Agent",
            role="Track job applications in the local database with status updates",
            model=Claude(id="claude-haiku-4-5-20251001"),
            tools=[track_application, update_application_status, read_file],
            instructions="""You track job applications in the local SQLite database.

Use track_application to save new applications with their status, resume/cover letter paths.
Use update_application_status to change a job's status (discovered, ready, applied, interview, rejected, offer).

When tracking multiple jobs, process them one by one and report results.""",
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

        web_agent = Agent(
            name="Web Agent",
            role="Automate job application form filling and submission via browser",
            model=Claude(id="claude-haiku-4-5-20251001"),
            tools=[apply_to_job, read_file],
            instructions="""You are a browser automation agent for job applications.

When asked to apply to a job:
1. Extract user info from the resume JSON provided in context
2. Use the apply_to_job tool with:
   - job_url: The application URL
   - resume_json: The user's resume data from <base_resume_json>
   - resume_path: Path to the generated PDF resume
   - additional_info: Any extra info like citizenship, sponsorship needs

Report back success or failure with details about what was filled out.""",
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
                tracker_agent,
                email_agent,
                web_agent,
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
        """Load user preferences and resume info from database."""
        context_parts = []
        debug_mode = os.getenv("AGNO_DEBUG", "false").lower() == "true"

        # Load preferences from database
        prefs = get_user_preferences(self.user_id)
        if debug_mode:
            print(f"DEBUG: Loading preferences for user {self.user_id}")
            print(f"DEBUG: Preferences found: {prefs is not None}")

        if prefs:
            if debug_mode:
                print(f"DEBUG: Loaded prefs keys: {list(prefs.keys())}")
            default_search = prefs.get('default_search', {})
            if debug_mode:
                print(f"DEBUG: default_search: {default_search}")
            context_parts.append(f"""<user_preferences>
Search Term: {default_search.get('search_term', 'not set')}
Location: {default_search.get('location', 'not set')}
Remote: {default_search.get('is_remote', False)}
Results Wanted: {default_search.get('results_wanted', 20)}
</user_preferences>""")
        else:
            if debug_mode:
                print(f"DEBUG: No preferences found for user {self.user_id}")

        # Load resume from database and include FULL JSON for agents to use
        resume = get_user_resume(self.user_id)
        if debug_mode:
            print(f"DEBUG: Loading resume for user {self.user_id}")
            print(f"DEBUG: Resume found: {resume is not None}")

        if resume:
            import json
            basics = resume.get('basics', {})
            # Include the FULL resume JSON so agents can use it directly
            context_parts.append(f"""<user_resume>
Name: {basics.get('name', 'not set')}
Email: {basics.get('email', 'not set')}

IMPORTANT: Use the resume data below. Do NOT read from user_data/base_resume.json file.

<base_resume_json>
{json.dumps(resume, indent=2)}
</base_resume_json>
</user_resume>""")
        else:
            if debug_mode:
                print(f"DEBUG: No resume found for user {self.user_id}")

        # Add user output directory info
        user_output_dir = OUTPUT_DIR / str(self.user_id)
        context_parts.append(f"""<user_output_directory>
Output path: {user_output_dir}
Resumes: {user_output_dir}/resumes/
Cover Letters: {user_output_dir}/cover_letters/
Job Listings: {user_output_dir}/job_listings/
</user_output_directory>""")

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

    def seed_conversation_history(self, history_entries):
        """Replace in-memory conversation history with recent channel messages."""
        if not history_entries:
            return
        # Store only the most recent entries to cap context size
        self.conversation_history = history_entries[-10:]

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
        # Initialize database
        init_db()
        print("✅ Database initialized")

        await self.tree.sync()
        print(f"🤖 Jobby Bot logged in as {self.user}")
        print(f"✅ Slash commands synced")

        if self.enable_auto_monitor:
            print(f"🔄 Starting auto job monitor (interval: {self.check_interval_minutes} minutes)...")
            self.auto_job_check.start()
            print("✅ Auto job monitor started (multi-user mode)")

    async def get_or_create_session(self, user_id: int) -> JobbySession:
        """Get existing session or create a new one for a user."""
        if user_id not in self.sessions:
            session = JobbySession(user_id)
            await session.initialize()
            self.sessions[user_id] = session
        return self.sessions[user_id]

    @tasks.loop(minutes=30)
    async def auto_job_check(self):
        """Automatically check for new jobs for all opted-in users."""
        try:
            print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running auto job check...")

            # Get all users who have opted in to auto-monitoring
            users = get_auto_monitor_users()

            if not users:
                print("⚠️ No users have auto-monitoring enabled. Skipping check.")
                return

            print(f"📊 Found {len(users)} user(s) with auto-monitoring enabled")

            for user_data in users:
                discord_user_id = user_data['discord_user_id']
                discord_username = user_data.get('discord_username', 'Unknown')
                email = user_data['email']
                preferences = user_data['preferences']

                print(f"\n👤 Processing user: {discord_username} (ID: {discord_user_id})")

                try:
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

                    query += f". Generate resumes and cover letters for matches, then send individual emails for each job to {email}."

                    print(f"📋 Query for {discord_username}: {query[:100]}...")

                    # Create or get session for this user
                    session = await self.get_or_create_session(discord_user_id)
                    response = await session.process_message(query)

                    print(f"✅ Completed job check for {discord_username}")
                    print(f"Response summary: {response[:200]}...")

                    # Update monitor state for this user
                    save_monitor_state(discord_user_id, [], datetime.now())

                except Exception as user_error:
                    print(f"❌ Error processing user {discord_username}: {user_error}")
                    continue

            print(f"\n✅ Auto job check completed for all users")

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

        user_id = message.author.id
        username = str(message.author)

        # Ensure user exists in database
        get_or_create_user(user_id, username)

        # Check if user has preferences set up
        prefs = get_user_preferences(user_id)
        resume = get_user_resume(user_id)

        # Check if this is a setup response (user answering setup questions)
        is_setup_response = await self._handle_setup_flow(message, user_id, prefs, resume, content)
        if is_setup_response:
            return

        # Check if user has completed setup (both preferences AND resume required)
        has_prefs = prefs and prefs.get('default_search', {}).get('search_term')
        has_resume = resume is not None

        # If missing preferences or resume, prompt user to set up
        if not has_prefs or not has_resume:
            await self._prompt_initial_setup(message, prefs, resume)
            return

        async with message.channel.typing():
            try:
                session = await self.get_or_create_session(user_id)
                recent_history = await self._build_recent_channel_history(message)
                if recent_history:
                    session.seed_conversation_history(recent_history)
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
                print(f"Error in session {user_id}: {e}")

    async def _prompt_initial_setup(self, message: discord.Message, prefs: dict, resume: dict):
        """Prompt user to set up their preferences."""
        setup_msg = "👋 **Welcome to Jobby Bot!**\n\n"
        setup_msg += "Before I can help you find jobs, I need some information:\n\n"

        # Check what's missing
        has_resume = resume is not None
        has_prefs = prefs and prefs.get('default_search', {}).get('search_term')

        if not has_resume:
            setup_msg += "❌ **Step 1 - Resume**: Not uploaded yet\n"
            setup_msg += "   → Use `/upload-resume` to upload your resume (PDF or TXT)\n\n"

        if not has_prefs:
            step_num = "2" if not has_resume else "1"
            setup_msg += f"❌ **Step {step_num} - Job Preferences**: Not configured\n"
            setup_msg += "   → Let's set them up now!\n\n"
            setup_msg += "**Please tell me:**\n"
            setup_msg += "1️⃣ What job title are you looking for? (e.g., Software Engineer, Data Analyst)\n"
            setup_msg += "2️⃣ What location? (e.g., San Francisco, CA or 'remote')\n\n"
            setup_msg += "💡 *Just reply with something like:*\n"
            setup_msg += "`Software Engineer in San Francisco, remote preferred`\n\n"
            setup_msg += "Or use `/set-preferences` for more detailed settings."
        elif not has_resume:
            # Has preferences but no resume
            setup_msg += "✅ **Job Preferences**: Configured\n\n"
            setup_msg += "⚠️ **Please upload your resume first** using `/upload-resume`\n"
            setup_msg += "I need your resume to create customized applications for each job."

        await message.reply(setup_msg)

    async def _build_recent_channel_history(self, message: discord.Message, limit: int = 5) -> List[Dict[str, str]]:
        """Fetch the previous messages in the channel to provide context."""
        history_entries: List[Dict[str, str]] = []

        try:
            async for msg in message.channel.history(limit=limit, before=message, oldest_first=False):
                entry = self._format_history_entry(msg)
                if entry:
                    history_entries.append(entry)
        except (discord.Forbidden, discord.HTTPException) as history_error:
            print(f"⚠️ Unable to fetch channel history for {message.channel}: {history_error}")
            return []

        history_entries.reverse()  # Oldest first for natural reading order
        return history_entries

    def _format_history_entry(self, msg: discord.Message) -> Optional[Dict[str, str]]:
        """Convert a Discord message into a conversation history entry."""
        content = (msg.clean_content or msg.content or "").strip()

        if msg.attachments:
            attachments_text = ", ".join(att.url for att in msg.attachments)
            attachment_line = f"Attachments: {attachments_text}"
            content = f"{content}\n{attachment_line}".strip()

        if not content:
            return None

        role = "assistant" if self.user and msg.author.id == self.user.id else "user"

        # Include author name for non-bot speakers to preserve context in busy channels
        if role == "user":
            display_name = getattr(msg.author, "display_name", str(msg.author))
            content = f"{display_name}: {content}"

        # Trim to avoid sending excessively long history entries
        return {"role": role, "content": content[:1000]}

    async def _handle_setup_flow(self, message: discord.Message, user_id: int, prefs: dict, resume: dict, content: str) -> bool:
        """Handle setup flow responses. Returns True if this was a setup response."""
        # Only handle setup if user doesn't have preferences yet
        if prefs and prefs.get('default_search', {}).get('search_term'):
            return False

        # Check if this looks like a setup response (job title + location pattern)
        content_lower = content.lower()

        # Skip if it looks like a regular command or question
        skip_patterns = ['help', 'what can you', 'how do', '/']
        if any(pattern in content_lower for pattern in skip_patterns):
            return False

        # Try to parse job preferences from natural language
        parsed_prefs = self._parse_preferences_from_message(content)

        if parsed_prefs.get('search_term'):
            # Save the parsed preferences
            new_prefs = prefs or {}
            if 'default_search' not in new_prefs:
                new_prefs['default_search'] = {}

            new_prefs['default_search']['search_term'] = parsed_prefs['search_term']
            if parsed_prefs.get('location'):
                new_prefs['default_search']['location'] = parsed_prefs['location']
            if parsed_prefs.get('is_remote') is not None:
                new_prefs['default_search']['is_remote'] = parsed_prefs['is_remote']

            # Set defaults
            new_prefs['default_search'].setdefault('results_wanted', 20)
            new_prefs['default_search'].setdefault('hours_old', 72)

            save_user_preferences(user_id, new_prefs, str(message.author))

            # Confirm and prompt for next steps
            confirm_msg = "✅ **Preferences Saved!**\n\n"
            confirm_msg += f"🔍 **Job Title**: {parsed_prefs['search_term']}\n"
            if parsed_prefs.get('location'):
                confirm_msg += f"📍 **Location**: {parsed_prefs['location']}\n"
            if parsed_prefs.get('is_remote'):
                confirm_msg += f"🏠 **Remote**: Yes\n"
            confirm_msg += "\n"

            if not resume:
                confirm_msg += "📄 **Next step**: Upload your resume using `/upload-resume`\n"
                confirm_msg += "This helps me create tailored resumes for each job.\n\n"

            confirm_msg += "🚀 **Ready to search!** Just say something like:\n"
            confirm_msg += "`Find me 10 jobs` or `Search for remote positions`"

            await message.reply(confirm_msg)
            return True

        return False

    def _parse_preferences_from_message(self, content: str) -> dict:
        """Parse job preferences from natural language message."""
        result = {
            'search_term': None,
            'location': None,
            'is_remote': False
        }

        content_lower = content.lower()

        # Check for remote preference
        remote_keywords = ['remote', 'work from home', 'wfh', 'virtual']
        result['is_remote'] = any(kw in content_lower for kw in remote_keywords)

        # Common location prepositions
        location_preps = [' in ', ' at ', ' near ', ' around ']

        # Try to split by location preposition
        for prep in location_preps:
            if prep in content_lower:
                parts = content.split(prep, 1)
                if len(parts) == 2:
                    result['search_term'] = parts[0].strip()
                    # Clean up location (remove "remote" if present)
                    location = parts[1].strip()
                    for kw in remote_keywords:
                        location = location.replace(kw, '').strip()
                    # Remove trailing punctuation and common words
                    location = location.rstrip('.,!?')
                    location = location.replace(' preferred', '').replace(' only', '').strip()
                    if location and location.lower() not in ['', 'remote']:
                        result['location'] = location
                    break

        # If no location preposition found, treat whole thing as search term
        if not result['search_term']:
            # Remove remote keywords and clean up
            clean_content = content
            for kw in remote_keywords:
                clean_content = clean_content.replace(kw, '').strip()
            clean_content = clean_content.replace(' preferred', '').replace(' only', '').strip()
            clean_content = clean_content.rstrip('.,!?')
            if clean_content:
                result['search_term'] = clean_content

        return result


# Import slash commands
from jobby_bot.discord_commands import (
    help_command,
    end_command,
    upload_resume_command,
    set_preferences_command,
    show_preferences_command,
    show_resume_command,
    set_email_command,
    enable_auto_monitor_command,
    disable_auto_monitor_command,
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
        "🤖 Auto-apply to jobs via browser automation\n"
        "📊 Track applications in Notion\n"
        "📧 Automatic job alerts via email\n\n"
        "**How to use:**\n"
        "• Use `/` slash commands for setup and configuration\n"
        "• Send me a DM or mention me for job searches and requests\n"
        "• Say 'auto apply' or 'apply to job' for browser automation\n\n"
        "**Setup Commands:**\n"
        "• `/upload-resume` - Upload your resume (PDF/TXT)\n"
        "• `/set-preferences` - Update job search settings\n"
        "• `/set-email` - Set your email for job alerts\n"
        "• `/enable-auto-monitor` - Enable automatic job alerts\n"
        "• `/disable-auto-monitor` - Disable automatic job alerts\n\n"
        "**View Commands:**\n"
        "• `/show-resume` - View your current resume\n"
        "• `/show-preferences` - View your settings\n"
        "• `/help` - Get detailed help\n"
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
    bot.tree.add_command(set_email_command)
    bot.tree.add_command(enable_auto_monitor_command)
    bot.tree.add_command(disable_auto_monitor_command)

    print("\n" + "="*60)
    print("🤖 JOBBY BOT - Discord Integration (Agno Framework)")
    print("="*60)
    print(f"📁 User data directory: {USER_DATA_DIR}")
    print(f"   preferences.json exists: {(USER_DATA_DIR / 'preferences.json').exists()}")
    print(f"   base_resume.json exists: {(USER_DATA_DIR / 'base_resume.json').exists()}")
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
