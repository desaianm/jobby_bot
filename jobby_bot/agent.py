"""Entry point for Jobby Bot multi-agent job application system."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition, HookMatcher

from jobby_bot.utils.subagent_tracker import SubagentTracker
from jobby_bot.utils.transcript import setup_session, TranscriptWriter
from jobby_bot.utils.message_handler import process_assistant_message

# Load environment variables
load_dotenv()

# Paths to prompt files
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """Load a prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


async def main():
    """Start the Jobby Bot agent system."""

    # Check API key first, before creating any files
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found.")
        print("Set it in a .env file or export it in your shell.")
        print("Get your key at: https://console.anthropic.com/settings/keys\n")
        return

    # Setup session directory and transcript
    transcript_file, session_dir = setup_session()

    # Create transcript writer
    transcript = TranscriptWriter(transcript_file)

    # Load prompts
    lead_agent_prompt = load_prompt("lead_agent.txt")
    job_finder_prompt = load_prompt("job_finder.txt")
    resume_writer_prompt = load_prompt("resume_writer.txt")
    cover_letter_prompt = load_prompt("cover_letter.txt")
    notion_agent_prompt = load_prompt("notion_agent.txt")

    # Initialize subagent tracker with transcript writer and session directory
    tracker = SubagentTracker(transcript_writer=transcript, session_dir=session_dir)

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
                matcher=None,  # Match all tools
                hooks=[tracker.pre_tool_use_hook]
            )
        ],
        'PostToolUse': [
            HookMatcher(
                matcher=None,  # Match all tools
                hooks=[tracker.post_tool_use_hook]
            )
        ]
    }

    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        setting_sources=["project"],
        system_prompt=lead_agent_prompt,
        allowed_tools=["Task"],  # Lead agent ONLY uses Task tool
        agents=agents,
        hooks=hooks,
        model="sonnet"  # claude-sonnet-4-5 for orchestration
    )

    print("\n" + "="*60)
    print("🤖 JOBBY BOT - AI Job Application Assistant")
    print("="*60)
    print("\nI can help you:")
    print("  🔍 Search for jobs across LinkedIn, Indeed, and Google")
    print("  📄 Generate customized ATS-optimized resumes")
    print("  ✍️  Write personalized cover letters")
    print("  📊 Track applications in Notion")
    print(f"\n📁 Session logs: {session_dir}")
    print(f"🤖 Registered agents: {', '.join(agents.keys())}")
    print("\nType 'exit' or 'quit' to end.\n")
    print("="*60)

    try:
        async with ClaudeSDKClient(options=options) as client:
            while True:
                # Get input
                try:
                    user_input = input("\n💼 You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    break

                if not user_input or user_input.lower() in ["exit", "quit", "q"]:
                    break

                # Write user input to transcript (file only, not console)
                transcript.write_to_file(f"\n💼 You: {user_input}\n")

                # Send to agent
                await client.query(prompt=user_input)

                transcript.write("\n🤖 Agent: ", end="")

                # Stream and process response
                async for msg in client.receive_response():
                    if type(msg).__name__ == 'AssistantMessage':
                        process_assistant_message(msg, tracker, transcript)

                transcript.write("\n")
    finally:
        transcript.write("\n\n👋 Goodbye! Good luck with your job search!\n")
        transcript.close()
        tracker.close()
        print("\n" + "="*60)
        print(f"📁 Session saved to: {session_dir}")
        print(f"  📄 Transcript: {transcript_file}")
        print(f"  🔧 Tool calls: {session_dir / 'tool_calls.jsonl'}")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
