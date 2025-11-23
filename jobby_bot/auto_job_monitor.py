"""Automated job monitoring and matching system."""

import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Set
import json
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition, HookMatcher
from jobby_bot.utils.subagent_tracker import SubagentTracker
from jobby_bot.utils.transcript import setup_session, TranscriptWriter

# Load environment variables
load_dotenv()

# Paths
PROMPTS_DIR = Path(__file__).parent / "prompts"
USER_DATA_DIR = Path(__file__).parent / "user_data"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
MONITOR_STATE_FILE = USER_DATA_DIR / "monitor_state.json"


def load_prompt(filename: str) -> str:
    """Load a prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


class JobMonitorState:
    """Manages state for job monitoring (which jobs we've already processed)."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.processed_jobs: Set[str] = set()
        self.last_check: Optional[datetime] = None
        self.load_state()

    def load_state(self):
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.processed_jobs = set(data.get('processed_jobs', []))
                    last_check_str = data.get('last_check')
                    if last_check_str:
                        self.last_check = datetime.fromisoformat(last_check_str)
            except Exception as e:
                print(f"⚠️ Error loading monitor state: {e}")
                self.processed_jobs = set()
                self.last_check = None

    def save_state(self):
        """Save state to disk."""
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'processed_jobs': list(self.processed_jobs),
                'last_check': self.last_check.isoformat() if self.last_check else None
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving monitor state: {e}")

    def is_processed(self, job_id: str) -> bool:
        """Check if a job has already been processed."""
        return job_id in self.processed_jobs

    def mark_processed(self, job_id: str):
        """Mark a job as processed."""
        self.processed_jobs.add(job_id)
        self.save_state()

    def update_check_time(self):
        """Update the last check time."""
        self.last_check = datetime.now()
        self.save_state()


class AutoJobMonitor:
    """Automated job monitoring and matching system."""

    def __init__(self, check_interval_minutes: int = 30):
        self.check_interval = check_interval_minutes * 60  # Convert to seconds
        self.state = JobMonitorState(MONITOR_STATE_FILE)
        self.is_running = False
        self.client: Optional[ClaudeSDKClient] = None

    async def initialize_agent(self):
        """Initialize the Claude agent for job processing."""
        # Setup session directory and transcript
        transcript_file, session_dir = setup_session()

        # Create transcript writer
        transcript = TranscriptWriter(transcript_file)

        # Load prompts
        lead_agent_prompt = load_prompt("lead_agent.txt")
        job_finder_prompt = load_prompt("job_finder.txt")
        resume_writer_prompt = load_prompt("resume_writer.txt")
        cover_letter_prompt = load_prompt("cover_letter.txt")
        email_agent_prompt = load_prompt("email_agent.txt")
        notion_agent_prompt = load_prompt("notion_agent.txt")

        # Initialize subagent tracker
        tracker = SubagentTracker(
            transcript_writer=transcript,
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
            )
        }

        # Set up hooks for tracking
        hooks = {
            'PreToolUse': [
                HookMatcher(
                    matcher=None,
                    hooks=[tracker.pre_tool_use_hook]
                )
            ],
            'PostToolUse': [
                HookMatcher(
                    matcher=None,
                    hooks=[tracker.post_tool_use_hook]
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
        self.transcript = transcript
        self.tracker = tracker

    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.__aexit__(None, None, None)
        if hasattr(self, 'transcript'):
            self.transcript.close()
        if hasattr(self, 'tracker'):
            self.tracker.close()

    async def check_for_jobs(self) -> int:
        """
        Check for new jobs matching user preferences and process them.
        Returns the number of new jobs found and processed.
        """
        print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new jobs...")

        # Load user preferences
        preferences_file = USER_DATA_DIR / "preferences.json"
        if not preferences_file.exists():
            print("⚠️ No preferences.json found. Skipping check.")
            return 0

        try:
            with open(preferences_file, 'r') as f:
                preferences = json.load(f)
        except Exception as e:
            print(f"❌ Error loading preferences: {e}")
            return 0

        # Get search parameters
        default_search = preferences.get('default_search', {})
        search_term = default_search.get('search_term', 'software engineer')
        location = default_search.get('location', '')
        is_remote = default_search.get('is_remote', False)
        results_wanted = default_search.get('results_wanted', 10)

        # For monitoring, only look at jobs posted in the last check interval + buffer
        # Default to last 60 minutes (30 min interval + 30 min buffer)
        hours_old = max(1, int(self.check_interval / 3600) + 1)

        # Build search query
        query = (
            f"Search for {results_wanted} {search_term} jobs "
            f"posted in the last {hours_old} hours"
        )

        if location:
            query += f" in {location}"
        if is_remote:
            query += " (remote positions only)"

        query += ". Generate resumes and cover letters for matches, then send individual emails for each job."

        print(f"📋 Query: {query}")

        # Execute search through agent
        try:
            await self.client.query(prompt=query)

            # Collect response
            response_parts = []
            async for msg in self.client.receive_response():
                if type(msg).__name__ == 'AssistantMessage':
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            response_parts.append(block.text)

            response = "\n".join(response_parts)

            # Parse response to count new jobs (simple heuristic)
            # Look for "Found X jobs" pattern
            import re
            match = re.search(r'Found (\d+)', response)
            if match:
                jobs_found = int(match.group(1))
                print(f"✅ Processed {jobs_found} new job(s)")
                self.state.update_check_time()
                return jobs_found
            else:
                print("✅ Job check completed")
                self.state.update_check_time()
                return 0

        except Exception as e:
            print(f"❌ Error during job check: {e}")
            return 0

    async def run_monitoring_loop(self):
        """Run the continuous monitoring loop."""
        self.is_running = True

        print("\n" + "="*60)
        print("🤖 AUTO JOB MONITOR - Starting")
        print("="*60)
        print(f"⏱️  Check interval: {self.check_interval // 60} minutes")
        print(f"📧 Email recipient: {os.getenv('RECIPIENT_EMAIL', 'Not configured')}")
        print(f"💾 State file: {MONITOR_STATE_FILE}")
        print("="*60 + "\n")

        # Initialize agent
        await self.initialize_agent()

        # Run first check immediately
        await self.check_for_jobs()

        # Then run on interval
        while self.is_running:
            try:
                # Wait for next check
                print(f"⏳ Next check in {self.check_interval // 60} minutes...")
                await asyncio.sleep(self.check_interval)

                # Run check
                if self.is_running:  # Check again in case we stopped during sleep
                    await self.check_for_jobs()

            except asyncio.CancelledError:
                print("\n🛑 Monitoring cancelled")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                # Continue running despite errors
                await asyncio.sleep(60)  # Wait a minute before retrying

        # Cleanup
        await self.cleanup()
        print("\n👋 Auto Job Monitor stopped\n")

    async def stop(self):
        """Stop the monitoring loop."""
        self.is_running = False


async def main():
    """Run the auto job monitor as a standalone service."""
    # Check for required API keys
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found.")
        print("Set it in a .env file or export it in your shell.")
        print("Get your key at: https://console.anthropic.com/settings/keys\n")
        return

    if not os.environ.get("RECIPIENT_EMAIL"):
        print("\n⚠️ Warning: RECIPIENT_EMAIL not configured.")
        print("Jobs will be found but emails won't be sent.")
        print("Add RECIPIENT_EMAIL to your .env file to enable email notifications.\n")

    # Get check interval from environment or use default (30 minutes)
    check_interval = int(os.getenv("JOB_CHECK_INTERVAL_MINUTES", "30"))

    # Create and run monitor
    monitor = AutoJobMonitor(check_interval_minutes=check_interval)

    try:
        await monitor.run_monitoring_loop()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping monitor...")
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
