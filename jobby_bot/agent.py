"""Entry point for Jobby Bot multi-agent job application system using Agno."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.team import Team
from agno.tools import tool

from jobby_bot.utils.subagent_tracker import SubagentTracker
from jobby_bot.utils.transcript import setup_session, TranscriptWriter

# Load environment variables
load_dotenv()

# Paths to prompt files
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """Load a prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


# Define custom tools for agents

@tool
def search_jobs(
    search_term: str,
    location: str = "",
    is_remote: bool = False,
    results_wanted: int = 20,
    sites: list = None,
    job_type: str = None,
    hours_old: int = 72
) -> str:
    """Search for jobs using JobSpy across multiple job sites.

    Args:
        search_term: Job title or keywords to search for
        location: Location to search in (optional)
        is_remote: Filter for remote jobs only
        results_wanted: Number of results to return (default 20)
        sites: List of sites to search (indeed, linkedin, google)
        job_type: Type of job (fulltime, parttime, internship, contract)
        hours_old: How recent jobs should be in hours (default 72)

    Returns:
        JSON string with job listings
    """
    import json
    from datetime import datetime
    try:
        from jobspy import scrape_jobs
        import pandas as pd

        if sites is None:
            sites = ["indeed", "linkedin", "google"]

        # Scrape jobs
        jobs_df = scrape_jobs(
            site_name=sites,
            search_term=search_term,
            location=location,
            is_remote=is_remote,
            results_wanted=results_wanted,
            job_type=job_type,
            hours_old=hours_old,
        )

        if jobs_df.empty:
            return json.dumps({"success": True, "total_jobs_found": 0, "jobs": []})

        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = f"output/job_listings/jobs_{timestamp}.csv"
        os.makedirs("output/job_listings", exist_ok=True)
        jobs_df.to_csv(csv_path, index=False)

        # Convert to list of dicts
        jobs_list = []
        for idx, row in jobs_df.iterrows():
            jobs_list.append({
                "job_id": f"job_{idx}",
                "title": str(row.get("title", "")),
                "company": str(row.get("company", "")),
                "location": str(row.get("location", "")),
                "job_url": str(row.get("job_url", "")),
                "date_posted": str(row.get("date_posted", "")),
                "description_preview": str(row.get("description", ""))[:200],
                "is_remote": bool(row.get("is_remote", False)),
                "salary": str(row.get("min_amount", "")) + " - " + str(row.get("max_amount", "")) if row.get("min_amount") else ""
            })

        return json.dumps({
            "success": True,
            "total_jobs_found": len(jobs_list),
            "csv_file": csv_path,
            "jobs": jobs_list
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "total_jobs_found": 0, "jobs": []})


@tool
def read_file(file_path: str) -> str:
    """Read contents of a file.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file

    Returns:
        Success or error message
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def generate_pdf(text_path: str, pdf_path: str, doc_type: str = "resume") -> str:
    """Generate a PDF from text file using the PDF generator.

    Args:
        text_path: Path to the source text file
        pdf_path: Path for the output PDF file
        doc_type: Type of document - 'resume' or 'cover_letter'

    Returns:
        Success or error message
    """
    try:
        from jobby_bot.utils.pdf_generator import create_resume_pdf, create_cover_letter_pdf

        with open(text_path, "r", encoding="utf-8") as f:
            content = f.read()

        if doc_type == "resume":
            create_resume_pdf(content, pdf_path)
        else:
            create_cover_letter_pdf(content, pdf_path)

        return f"PDF created successfully: {pdf_path}"
    except Exception as e:
        return f"Error generating PDF: {str(e)}"


@tool
def screenshot_pdf(pdf_path: str, output_image_path: str = None, page_num: int = 0) -> str:
    """Take a screenshot of a PDF page for visual verification.

    Args:
        pdf_path: Path to the PDF file
        output_image_path: Path for the output image (default: same as PDF with .png)
        page_num: Page number to screenshot (0-indexed, default: 0 for first page)

    Returns:
        Path to the generated image or error message
    """
    try:
        import fitz  # PyMuPDF

        if output_image_path is None:
            output_image_path = pdf_path.replace('.pdf', f'_page{page_num}.png')

        # Open the PDF
        doc = fitz.open(pdf_path)

        if page_num >= len(doc):
            return f"Error: PDF only has {len(doc)} pages, requested page {page_num}"

        # Get the page and render to image
        page = doc[page_num]
        # High resolution: 2x zoom for clarity
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)

        # Save the image
        pix.save(output_image_path)
        doc.close()

        return f"Screenshot saved: {output_image_path}"
    except ImportError:
        return "Error: PyMuPDF not installed. Run: pip install PyMuPDF"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


@tool
def generate_html_from_text(text_path: str, html_path: str, doc_type: str = "resume") -> str:
    """Generate HTML from text file without creating PDF. Useful for editing HTML directly.

    Args:
        text_path: Path to the source text file
        html_path: Path for the output HTML file
        doc_type: Type of document - 'resume' or 'cover_letter'

    Returns:
        Success or error message
    """
    try:
        from jobby_bot.utils.html_content_generator import generate_resume_html, generate_cover_letter_html

        with open(text_path, "r", encoding="utf-8") as f:
            content = f.read()

        if doc_type == "resume":
            html_content = generate_resume_html(content)
        else:
            html_content = generate_cover_letter_html(content)

        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return f"HTML created successfully: {html_path}"
    except Exception as e:
        return f"Error generating HTML: {str(e)}"


@tool
def generate_pdf_from_html(html_path: str, pdf_path: str) -> str:
    """Generate PDF from HTML file. Use after editing HTML directly.

    Args:
        html_path: Path to the HTML file
        pdf_path: Path for the output PDF file

    Returns:
        Success or error message
    """
    try:
        from weasyprint import HTML

        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        HTML(filename=html_path).write_pdf(pdf_path)

        return f"PDF created from HTML: {pdf_path}"
    except Exception as e:
        return f"Error generating PDF from HTML: {str(e)}"


@tool
def create_notion_entry(
    job_title: str,
    company: str,
    job_url: str,
    location: str = "",
    description: str = "",
    resume_path: str = "",
    cover_letter_path: str = ""
) -> str:
    """Create a job application entry in Notion database.

    Args:
        job_title: Title of the job position
        company: Company name
        job_url: URL to the job posting
        location: Job location
        description: Job description (truncated to 2000 chars)
        resume_path: Path to generated resume
        cover_letter_path: Path to generated cover letter

    Returns:
        Success message with Notion page URL or error
    """
    try:
        from notion_client import Client

        notion_api_key = os.environ.get("NOTION_API_KEY")
        database_id = os.environ.get("NOTION_DATABASE_ID")

        if not notion_api_key or not database_id:
            return "Error: NOTION_API_KEY or NOTION_DATABASE_ID not configured"

        notion = Client(auth=notion_api_key)

        # Create page properties
        properties = {
            "Job Title": {"title": [{"text": {"content": job_title}}]},
            "Company": {"rich_text": [{"text": {"content": company}}]},
            "Job URL": {"url": job_url},
            "Status": {"select": {"name": "To Apply"}},
        }

        if location:
            properties["Location"] = {"rich_text": [{"text": {"content": location}}]}
        if resume_path:
            properties["Resume Path"] = {"rich_text": [{"text": {"content": resume_path}}]}
        if cover_letter_path:
            properties["Cover Letter Path"] = {"rich_text": [{"text": {"content": cover_letter_path}}]}

        # Create the page
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )

        return f"Created Notion entry: {page['url']}"
    except Exception as e:
        return f"Error creating Notion entry: {str(e)}"


@tool
def validate_job_url(job_url: str) -> str:
    """Validate that a job URL is real and accessible (not hallucinated).

    Args:
        job_url: The job posting URL to validate

    Returns:
        JSON with validation result: {"valid": true/false, "status": "...", "reason": "..."}
    """
    import json
    import requests
    from urllib.parse import urlparse

    if not job_url:
        return json.dumps({"valid": False, "status": "error", "reason": "No URL provided"})

    # Parse URL to check domain
    try:
        parsed = urlparse(job_url)
        domain = parsed.netloc
    except Exception:
        return json.dumps({"valid": False, "status": "error", "reason": "Invalid URL format"})

    # Check if URL is from expected job sites
    valid_domains = ["indeed.com", "linkedin.com", "google.com", "glassdoor.com", "ziprecruiter.com"]
    domain_valid = any(d in domain for d in valid_domains)

    if not domain_valid:
        return json.dumps({"valid": False, "status": "warning", "reason": f"Unexpected domain: {domain}"})

    # Headers to mimic a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        response = requests.head(job_url, headers=headers, timeout=10, allow_redirects=True)
        status_code = response.status_code

        # Try GET if HEAD doesn't work
        if status_code >= 400:
            response = requests.get(job_url, headers=headers, timeout=10, allow_redirects=True)
            status_code = response.status_code

        if status_code == 200:
            return json.dumps({"valid": True, "status": "valid", "reason": f"URL accessible (HTTP {status_code})"})
        elif status_code in [301, 302, 303, 307, 308]:
            return json.dumps({"valid": True, "status": "redirect", "reason": f"URL redirects (HTTP {status_code})"})
        elif status_code == 403:
            return json.dumps({"valid": True, "status": "blocked", "reason": "URL exists but blocks automated access"})
        elif status_code == 404:
            return json.dumps({"valid": False, "status": "not_found", "reason": "Job posting not found (HTTP 404)"})
        else:
            return json.dumps({"valid": True, "status": "uncertain", "reason": f"HTTP {status_code}"})

    except requests.exceptions.Timeout:
        return json.dumps({"valid": True, "status": "timeout", "reason": "URL may be valid but slow"})
    except requests.exceptions.ConnectionError as e:
        return json.dumps({"valid": False, "status": "error", "reason": f"Connection error: {str(e)[:50]}"})
    except Exception as e:
        return json.dumps({"valid": False, "status": "error", "reason": str(e)[:50]})


@tool
def send_email(
    subject: str,
    body: str,
    attachments: list = None,
    recipient_email: str = None
) -> str:
    """Send an email with optional attachments.

    Args:
        subject: Email subject line
        body: Email body content (HTML supported)
        attachments: List of file paths to attach
        recipient_email: Email address to send to (optional, uses RECIPIENT_EMAIL from env if not provided)

    Returns:
        Success or error message
    """
    try:
        from jobby_bot.utils.email_sender import create_email_sender_from_env

        sender = create_email_sender_from_env()
        if not sender:
            return "Error: Email not configured. Please set SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD in .env"

        # Use provided recipient or fall back to env
        recipient = recipient_email or os.environ.get("RECIPIENT_EMAIL")
        if not recipient:
            return "Error: No recipient email provided and RECIPIENT_EMAIL not set in .env"

        # Send email
        success = sender._send_email(
            recipient_email=recipient,
            subject=subject,
            body_html=body,
            attachments=attachments or []
        )

        if success:
            attachment_names = [os.path.basename(a) for a in (attachments or []) if a]
            return f"✅ Email sent successfully to {recipient}\nSubject: {subject}\nAttachments: {', '.join(attachment_names) if attachment_names else 'None'}"
        else:
            return "❌ Failed to send email. Check SMTP configuration."
    except Exception as e:
        return f"Error sending email: {str(e)}"


def create_agents():
    """Create specialized agents for the job application system."""

    # Load prompts
    job_finder_prompt = load_prompt("job_finder.txt")
    resume_writer_prompt = load_prompt("resume_writer.txt")
    cover_letter_prompt = load_prompt("cover_letter.txt")
    notion_agent_prompt = load_prompt("notion_agent.txt")

    # Job Finder Agent
    job_finder = Agent(
        name="Job Finder",
        role="Search for jobs using JobSpy across LinkedIn, Indeed, and Google",
        model=Claude(id="claude-haiku-4-5-20251001"),
        tools=[search_jobs, validate_job_url, read_file, write_file],
        instructions=job_finder_prompt,
        markdown=True,
    )

    # Resume Writer Agent - with visual verification and HTML editing tools
    resume_writer = Agent(
        name="Resume Writer",
        role="Create customized ATS-optimized resumes for specific jobs",
        model=Claude(id="claude-haiku-4-5-20251001"),
        tools=[read_file, write_file, generate_pdf, screenshot_pdf, generate_html_from_text, generate_pdf_from_html],
        instructions=resume_writer_prompt,
        markdown=True,
    )

    # Cover Letter Agent - with visual verification and HTML editing tools
    cover_letter_writer = Agent(
        name="Cover Letter Writer",
        role="Generate personalized cover letters for job applications",
        model=Claude(id="claude-haiku-4-5-20251001"),
        tools=[read_file, write_file, generate_pdf, screenshot_pdf, generate_html_from_text, generate_pdf_from_html],
        instructions=cover_letter_prompt,
        markdown=True,
    )

    # Notion Agent
    notion_agent = Agent(
        name="Notion Agent",
        role="Track job applications in Notion database",
        model=Claude(id="claude-haiku-4-5-20251001"),
        tools=[create_notion_entry, read_file],
        instructions=notion_agent_prompt,
        markdown=True,
    )

    # Email Agent
    email_agent = Agent(
        name="Email Agent",
        role="Send job application emails with attachments",
        model=Claude(id="claude-haiku-4-5-20251001"),
        tools=[send_email, read_file],
        instructions="Send professional job application emails with resume and cover letter attachments.",
        markdown=True,
    )

    return {
        "job_finder": job_finder,
        "resume_writer": resume_writer,
        "cover_letter_writer": cover_letter_writer,
        "notion_agent": notion_agent,
        "email_agent": email_agent,
    }


def create_team(agents: dict) -> Team:
    """Create the orchestration team with lead agent."""

    lead_agent_prompt = load_prompt("lead_agent.txt")

    team = Team(
        name="Jobby Bot Team",
        model=Claude(id="claude-sonnet-4-5-20250929"),
        members=[
            agents["job_finder"],
            agents["resume_writer"],
            agents["cover_letter_writer"],
            agents["notion_agent"],
            agents["email_agent"],
        ],
        instructions=lead_agent_prompt,
        markdown=True,
        show_members_responses=True,
        get_member_information_tool=True,
        add_member_tools_to_context=True,
    )

    return team


async def main():
    """Start the Jobby Bot agent system."""

    # Check API key first
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n Error: ANTHROPIC_API_KEY not found.")
        print("Set it in a .env file or export it in your shell.")
        print("Get your key at: https://console.anthropic.com/settings/keys\n")
        return

    # Setup session directory and transcript
    transcript_file, session_dir = setup_session()

    # Create transcript writer
    transcript = TranscriptWriter(transcript_file)

    # Create agents and team
    agents = create_agents()
    team = create_team(agents)

    print("\n" + "="*60)
    print(" JOBBY BOT - AI Job Application Assistant (Agno)")
    print("="*60)
    print("\nI can help you:")
    print("   Search for jobs across LinkedIn, Indeed, and Google")
    print("   Generate customized ATS-optimized resumes")
    print("   Write personalized cover letters")
    print("   Track applications in Notion")
    print(f"\n Session logs: {session_dir}")
    print(f" Registered agents: {', '.join(agents.keys())}")
    print("\nType 'exit' or 'quit' to end.\n")
    print("="*60)

    try:
        while True:
            # Get input
            try:
                user_input = input("\n You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input or user_input.lower() in ["exit", "quit", "q"]:
                break

            # Write user input to transcript
            transcript.write_to_file(f"\n You: {user_input}\n")

            # Get response from team
            transcript.write("\n Agent: ", end="")

            try:
                # Use streaming response
                team.print_response(user_input, stream=True)
                transcript.write("\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(error_msg)
                transcript.write(f"{error_msg}\n")

    finally:
        transcript.write("\n\n Goodbye! Good luck with your job search!\n")
        transcript.close()
        print("\n" + "="*60)
        print(f" Session saved to: {session_dir}")
        print(f"   Transcript: {transcript_file}")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
