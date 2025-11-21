# Jobby Bot: Multi-Agent Job Application System

## Executive Summary

A Python-based multi-agent system using Claude Agent SDK to automate job searching, resume customization, cover letter generation, and application tracking via Notion. Built following the research-agent architecture pattern.

---

## Architecture Overview

### Multi-Agent System Design

**Lead Orchestrator Agent** (claude-sonnet-4-5)
- Role: Coordinates all subagents and manages workflow
- Tools: ONLY `Task` tool (spawns subagents)
- Responsibilities: Break down user requests, spawn agents in parallel, synthesize results

**Job Finder Agent** (claude-haiku-4-5)
- Role: Search and filter job listings
- Tools: `JobSpyTool`, `Write`
- Responsibilities: Scrape jobs from LinkedIn/Indeed/Google, filter by criteria, save results

**Resume Writer Agent** (claude-haiku-4-5)
- Role: Customize resumes for specific jobs
- Tools: `Read`, `Write`, `PDFGenerator`
- Responsibilities: Extract ATS keywords, optimize resume, generate PDF

**Cover Letter Agent** (claude-haiku-4-5)
- Role: Generate personalized cover letters
- Tools: `Read`, `Write`
- Responsibilities: Create tailored 3-paragraph letters matching job requirements

**Notion Agent** (claude-haiku-4-5)
- Role: Track applications in Notion database
- Tools: `NotionTool`, `Read`
- Responsibilities: Create database entries, update application status

---

## Directory Structure

```
jobby_bot/
├── pyproject.toml              # Poetry dependencies
├── .env.example                # API key template
├── .gitignore                  # Exclude secrets, logs, outputs
├── README.md                   # Setup & usage documentation
├── claude_plan.md              # This file
├── jobby_bot/
│   ├── __init__.py
│   ├── agent.py               # Main entry point - ClaudeSDKClient setup
│   │
│   ├── prompts/               # Agent instruction files
│   │   ├── lead_agent.txt     # Orchestrator (ONLY Task tool)
│   │   ├── job_finder.txt     # JobSpy integration & filtering
│   │   ├── resume_writer.txt  # ATS optimization logic
│   │   ├── cover_letter.txt   # Personalized letter generation
│   │   └── notion_agent.txt   # Notion database operations
│   │
│   ├── utils/                 # Tracking & logging (from research-agent)
│   │   ├── __init__.py
│   │   ├── subagent_tracker.py  # Hooks for tool call tracking
│   │   ├── message_handler.py   # Process streaming messages
│   │   └── transcript.py        # Session management & logging
│   │
│   └── tools/                 # Custom tool wrappers
│       ├── __init__.py
│       ├── jobspy_tool.py     # JobSpy scraping interface
│       └── notion_tool.py     # Notion API interface
│
├── logs/                       # Session logs (auto-created)
│   └── session_YYYYMMDD_HHMMSS/
│       ├── transcript.txt      # Human-readable conversation log
│       └── tool_calls.jsonl    # Structured tool call records
│
├── output/                     # Agent outputs (auto-created)
│   ├── job_listings/          # CSV files with scraped jobs
│   ├── resumes/               # Customized resume PDFs
│   └── cover_letters/         # Generated cover letters (TXT/MD)
│
└── user_data/                  # User configuration
    ├── base_resume.json       # Master resume (JSON Resume format)
    └── preferences.json       # Search criteria & filters
```

---

## Implementation Phases

### Phase 1: Foundation & Core SDK Setup

**Tasks:**
1. ✅ Create `pyproject.toml` with dependencies:
   - `claude-agent-sdk ^0.1.0`
   - `python-jobspy` (job scraping)
   - `notion-client ^2.2.1` (Notion integration)
   - `pydantic ^2.0.0` (data validation)
   - `python-dotenv ^1.0.0` (environment config)
   - `pandas ^2.0.0` (data processing)
   - `weasyprint ^60.0` (PDF generation)
   - `pyyaml ^6.0` (config parsing)

2. ✅ Create directory structure

3. Create configuration files:
   - `.env.example` (API keys template)
   - `.gitignore` (exclude secrets, logs, outputs)

4. Copy utilities from research-agent:
   - `utils/subagent_tracker.py` (hook implementation)
   - `utils/message_handler.py` (streaming message processing)
   - `utils/transcript.py` (session logging)

**Deliverables:**
- Working Poetry project setup
- Directory structure in place
- Tracking utilities adapted for job application context

---

### Phase 2: Custom Tool Wrappers

#### 2.1 JobSpy Tool (`tools/jobspy_tool.py`)

**Purpose:** Wrapper around python-jobspy for job scraping

**Interface:**
```python
class JobSpyTool:
    def search_jobs(
        self,
        search_term: str,
        location: str,
        sites: list[str] = ["indeed", "linkedin", "google"],
        results_wanted: int = 20,
        hours_old: int = 72,
        is_remote: bool = False,
        job_type: str = None  # "fulltime", "parttime", "internship", "contract"
    ) -> pd.DataFrame
```

**Outputs:**
- Saves results to `output/job_listings/jobs_{timestamp}.csv`
- Returns DataFrame with columns: title, company, location, date_posted, job_url, description, etc.

**Error Handling:**
- Rate limiting: Retry with exponential backoff
- Site failures: Continue with available sites
- Network errors: Log and return partial results

#### 2.2 Notion Tool (`tools/notion_tool.py`)

**Purpose:** Wrapper around notion-client for application tracking

**Interface:**
```python
class NotionTool:
    def create_job_entry(
        self,
        job_title: str,
        company: str,
        job_url: str,
        description: str,
        status: str = "To Apply",
        resume_path: str = None,
        cover_letter_path: str = None,
        applied_date: str = None
    ) -> str  # Returns page URL

    def update_status(
        self,
        page_id: str,
        new_status: str  # "To Apply", "Applied", "Interview", "Offer", "Rejected"
    ) -> bool
```

**Database Schema:**
```
Properties:
- Job Title (Title)
- Company (Text)
- Job URL (URL)
- Status (Select): To Apply, Applied, Interview, Offer, Rejected
- Description (Rich Text)
- Resume Path (Text)
- Cover Letter Path (Text)
- Applied Date (Date)
- Date Added (Created Time)
```

**Error Handling:**
- API rate limits: Queue and retry
- Authentication errors: Clear error message
- Missing database: Validation on init

---

### Phase 3: Agent Prompts

#### 3.1 Lead Agent (`prompts/lead_agent.txt`)

**Structure:**
```xml
<role_definition>
You are the LEAD ORCHESTRATOR for the Jobby Bot job application system.

Your ONLY job is to:
1. Understand the user's job search request
2. Break it down into subtasks
3. Spawn appropriate subagents using the Task tool
4. Synthesize results into a summary

You do NOT search for jobs, write resumes, or interact with APIs directly.
</role_definition>

<available_tools>
Task: Spawn subagents (job-finder, resume-writer, cover-letter, notion-agent)
</available_tools>

<workflow>
**STEP 1: Parse User Request**
Extract:
- Job search criteria (role, location, remote preference)
- Number of results wanted
- Whether to customize resumes/cover letters
- Whether to track in Notion

**STEP 2: Spawn Job Finder**
Use Task tool with subagent_type="job-finder"
Pass all search criteria in prompt

**STEP 3: Spawn Processors (Parallel)**
For each job found:
- Spawn resume-writer with job description
- Spawn cover-letter with job description
(Run these in parallel for speed)

**STEP 4: Spawn Notion Agent**
After processing, spawn notion-agent to track all applications

**STEP 5: Summarize**
Return: Number of jobs found, files generated, Notion database updated
</workflow>

<critical_rules>
- NEVER use tools other than Task
- ALWAYS spawn subagents in parallel when possible
- NEVER try to search jobs or write content yourself
- Keep responses SHORT and ACTION-ORIENTED
</critical_rules>

<examples>
GOOD:
User: "Find 10 remote Python jobs and generate resumes"
Assistant: "I'll spawn the job-finder agent to search for remote Python jobs, then spawn resume-writer agents in parallel for each result."
[Spawns agents]

BAD:
User: "Find 10 remote Python jobs"
Assistant: "Let me search Indeed for Python jobs in the US..."
[Tries to search directly - NO Task tool used]
</examples>
```

#### 3.2 Job Finder Agent (`prompts/job_finder.txt`)

**Key Sections:**
- Role: Search and filter job listings using JobSpy
- Tools: `JobSpyTool`, `Write`
- Workflow:
  1. Parse search criteria from lead agent's prompt
  2. Call JobSpyTool with parameters
  3. Filter results (remove duplicates, blacklisted companies)
  4. Save to CSV in `output/job_listings/`
  5. Return list of top N jobs with IDs

- Critical Rules:
  - NEVER return more jobs than requested
  - ALWAYS filter out blacklisted companies from `user_data/preferences.json`
  - ALWAYS save full results to CSV before filtering
  - Return job data in structured format (JSON list)

#### 3.3 Resume Writer Agent (`prompts/resume_writer.txt`)

**Key Sections:**
- Role: Customize base resume for specific job using ATS optimization
- Tools: `Read`, `Write`
- Workflow:
  1. Read `user_data/base_resume.json` (JSON Resume format)
  2. Read job description from lead agent's prompt
  3. Extract key requirements & ATS keywords
  4. Rewrite experience bullet points to include keywords
  5. Generate PDF using WeasyPrint
  6. Save to `output/resumes/{job_id}_resume.pdf`

- ATS Optimization Rules:
  - Include exact keyword matches from job description
  - Prioritize technical skills mentioned in requirements
  - Quantify achievements (e.g., "Improved performance by 40%")
  - Keep formatting simple (ATS-friendly)

#### 3.4 Cover Letter Agent (`prompts/cover_letter.txt`)

**Key Sections:**
- Role: Generate personalized cover letter for job
- Tools: `Read`, `Write`
- Workflow:
  1. Read job description from lead agent's prompt
  2. Read `user_data/base_resume.json` for context
  3. Generate 3-paragraph letter:
     - Opening: Reference specific job & company
     - Body: Match skills to requirements (3-4 key points)
     - Closing: Express enthusiasm & availability
  4. Save to `output/cover_letters/{job_id}_cover_letter.txt`

- Critical Rules:
  - NEVER be generic - personalize for company & role
  - ALWAYS reference specific job requirements
  - Keep under 400 words
  - Professional but enthusiastic tone

#### 3.5 Notion Agent (`prompts/notion_agent.txt`)

**Key Sections:**
- Role: Track job applications in Notion database
- Tools: `NotionTool`, `Read`
- Workflow:
  1. Read job details from lead agent's prompt
  2. Read file paths from `output/` directories
  3. Call NotionTool.create_job_entry() for each job
  4. Return list of created Notion page URLs

- Critical Rules:
  - ALWAYS validate NOTION_DATABASE_ID exists
  - Set status to "To Apply" (user will update manually)
  - Include all file paths for reference
  - Handle API errors gracefully (log and continue)

---

### Phase 4: Main Agent Entry Point (`agent.py`)

**Structure:**
```python
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    HookMatcher
)

from jobby_bot.utils.subagent_tracker import SubagentTracker
from jobby_bot.utils.message_handler import process_assistant_message
from jobby_bot.utils.transcript import setup_session
from jobby_bot.tools.jobspy_tool import JobSpyTool
from jobby_bot.tools.notion_tool import NotionTool

# Load prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    with open(PROMPTS_DIR / filename, "r") as f:
        return f.read().strip()

lead_agent_prompt = load_prompt("lead_agent.txt")
job_finder_prompt = load_prompt("job_finder.txt")
resume_writer_prompt = load_prompt("resume_writer.txt")
cover_letter_prompt = load_prompt("cover_letter.txt")
notion_agent_prompt = load_prompt("notion_agent.txt")

# Define agents
agents = {
    "job-finder": AgentDefinition(
        description="Search for jobs using JobSpy (LinkedIn, Indeed, Google) with filtering",
        tools=["JobSpyTool", "Write"],
        prompt=job_finder_prompt,
        model="haiku"
    ),
    "resume-writer": AgentDefinition(
        description="Customize resume for specific job with ATS optimization",
        tools=["Read", "Write"],
        prompt=resume_writer_prompt,
        model="haiku"
    ),
    "cover-letter": AgentDefinition(
        description="Generate personalized cover letter for job application",
        tools=["Read", "Write"],
        prompt=cover_letter_prompt,
        model="haiku"
    ),
    "notion-agent": AgentDefinition(
        description="Track job applications in Notion database",
        tools=["NotionTool", "Read"],
        prompt=notion_agent_prompt,
        model="haiku"
    )
}

async def main():
    load_dotenv()

    # Setup session logging
    transcript_path, session_dir = setup_session()

    # Initialize tracker
    tracker = SubagentTracker(session_dir)

    # Setup hooks
    hooks = {
        'PreToolUse': [HookMatcher(matcher=None, hooks=[tracker.pre_tool_use_hook])],
        'PostToolUse': [HookMatcher(matcher=None, hooks=[tracker.post_tool_use_hook])]
    }

    # Configure client
    options = ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        setting_sources=["project"],
        system_prompt=lead_agent_prompt,
        allowed_tools=["Task"],  # Lead agent ONLY uses Task
        agents=agents,
        hooks=hooks,
        model="sonnet"  # claude-sonnet-4-5 for orchestration
    )

    # Run agent
    async with ClaudeSDKClient(options=options) as client:
        # Get user query
        user_query = input("What job search would you like to perform? ")

        await client.send_message(user_query)

        # Stream responses
        async for msg in client.receive_response():
            process_assistant_message(msg, tracker, transcript_path)

            # Display to user
            if hasattr(msg, 'content'):
                for block in msg.content:
                    if hasattr(block, 'text'):
                        print(block.text)

        # Print summary
        tracker.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Features:**
- Async context manager for ClaudeSDKClient
- Hook registration for complete tracking
- Session logging with timestamps
- Streaming message processing
- Lead agent restricted to Task tool only

---

### Phase 5: User Data Files

#### 5.1 Base Resume (`user_data/base_resume.json`)

**Format:** JSON Resume Schema (https://jsonresume.org/)

```json
{
  "basics": {
    "name": "John Doe",
    "label": "Software Engineer",
    "email": "john@example.com",
    "phone": "(555) 123-4567",
    "summary": "Experienced software engineer...",
    "location": {
      "city": "San Francisco",
      "region": "CA"
    },
    "profiles": [
      {"network": "LinkedIn", "url": "linkedin.com/in/johndoe"}
    ]
  },
  "work": [
    {
      "name": "Tech Corp",
      "position": "Senior Software Engineer",
      "startDate": "2020-01",
      "endDate": "Present",
      "highlights": [
        "Built microservices handling 1M+ requests/day",
        "Led team of 5 engineers on cloud migration"
      ]
    }
  ],
  "education": [...],
  "skills": [
    {"name": "Python", "level": "Expert"},
    {"name": "AWS", "level": "Advanced"}
  ]
}
```

#### 5.2 Preferences (`user_data/preferences.json`)

```json
{
  "default_search": {
    "search_term": "software engineer",
    "location": "San Francisco, CA",
    "is_remote": false,
    "job_type": "fulltime",
    "results_wanted": 20,
    "hours_old": 72
  },
  "blacklist": {
    "companies": ["Company A", "Company B"],
    "keywords": ["unpaid", "commission-only"]
  },
  "filters": {
    "min_salary": 100000,
    "preferred_tech_stack": ["Python", "Django", "PostgreSQL"],
    "avoid_keywords": ["on-call 24/7", "no remote"]
  }
}
```

---

### Phase 6: Testing & Integration

**Test Scenarios:**

1. **End-to-End Workflow:**
   ```
   Input: "Find 5 remote Python jobs and generate resumes"
   Expected:
   - Job finder searches 3 sites
   - 5 jobs saved to CSV
   - 5 resume PDFs generated
   - 5 cover letters created
   - 5 Notion entries added
   - Session log created with all tool calls
   ```

2. **Parallel Processing:**
   - Verify resume-writer and cover-letter agents spawn in parallel
   - Check logs show overlapping execution times

3. **Error Handling:**
   - JobSpy rate limiting → Graceful retry
   - Notion API error → Log error, continue with other jobs
   - Missing base_resume.json → Clear error message

4. **Hook Tracking:**
   - Verify all tool calls logged with parent_tool_use_id
   - Check JSONL file has complete records
   - Validate subagent attribution in transcript

---

## Key Design Decisions

### ✅ Architectural Choices

1. **File-Based Coordination:**
   - Agents communicate via `output/` folders (matches research-agent pattern)
   - No direct agent-to-agent communication
   - Lead agent orchestrates through file system

2. **Parallel Processing:**
   - Resume + cover letter generated simultaneously per job
   - Reduces total execution time from ~3min to ~1min for 20 jobs

3. **Model Selection:**
   - Sonnet 4.5 for lead agent: Better orchestration & planning
   - Haiku 4.5 for subagents: Cost-effective for specialized tasks
   - Estimated cost: ~$0.50 for 20 job applications

4. **No Auto-Apply:**
   - Skipping Selenium automation (requires stealth setup, high complexity)
   - Focus on preparation (resume, cover letter) + tracking
   - User manually applies with generated materials

5. **JSON Resume Format:**
   - Industry standard (jsonresume.org)
   - Easy to parse and modify
   - Compatible with many resume builders

6. **Simple Configuration:**
   - `.env` for secrets (follows research-agent pattern)
   - JSON for user data (easy to edit)
   - No complex YAML configs

### ✅ Security & Privacy

1. **API Key Storage:**
   - Never commit `.env` to git
   - Provide `.env.example` template
   - Validate keys on startup

2. **Data Handling:**
   - All data stored locally (no cloud uploads)
   - User controls what goes to Notion
   - Clear logs for audit trail

3. **Rate Limiting:**
   - Respect JobSpy rate limits
   - Exponential backoff on failures
   - Don't hammer job sites

---

## Success Criteria

### Functional Requirements

✅ User provides search criteria → system finds jobs via JobSpy
✅ For each job: customized resume + cover letter generated
✅ All applications tracked in Notion database
✅ Complete session logs with tool call attribution
✅ Parallel processing for speed optimization

### Performance Targets

- **Speed:** ~1-2 min for 20 jobs (with parallel processing)
- **Accuracy:** 95%+ ATS keyword match in resumes
- **Reliability:** Graceful handling of API failures
- **Cost:** <$1 per 20 applications

### Quality Standards

- **Code:** Follows research-agent patterns exactly
- **Prompts:** Clear XML structure with examples
- **Logging:** Complete tool call tracking
- **Documentation:** Comprehensive README with setup

---

## Future Enhancements (Out of Scope for v1)

1. **Auto-Apply Automation:**
   - Selenium integration with stealth plugins
   - Form detection & filling
   - CAPTCHA solving (2captcha integration)

2. **Interview Prep Agent:**
   - Generate company research summaries
   - Create role-specific practice questions
   - Track interview schedules

3. **Follow-Up Agent:**
   - Send automated follow-up emails after X days
   - Track application status changes
   - Alert on interview invitations

4. **Analytics Dashboard:**
   - Application success rate by company/role
   - ATS keyword effectiveness
   - Time-to-response metrics

5. **Multi-User Support:**
   - Support multiple resume profiles
   - Team collaboration features
   - Shared Notion workspace

---

## Dependencies Reference

```toml
[tool.poetry.dependencies]
python = "^3.10"
claude-agent-sdk = "^0.1.0"        # Core agent framework
python-jobspy = "*"                 # Job scraping (LinkedIn, Indeed, etc.)
notion-client = "^2.2.1"           # Notion API integration
pydantic = "^2.0.0"                # Data validation
python-dotenv = "^1.0.0"           # Environment variables
pandas = "^2.0.0"                  # Data processing
weasyprint = "^60.0"               # PDF generation
pyyaml = "^6.0"                    # YAML parsing
markdown = "^3.5"                  # Markdown rendering
jinja2 = "^3.1.0"                  # Template engine

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"                  # Testing framework
black = "^23.12.0"                 # Code formatting
isort = "^5.13.0"                  # Import sorting
flake8 = "^6.1.0"                  # Linting
```

---

## Development Timeline

**Phase 1:** Foundation (2-3 hours)
- Project setup, dependencies, directory structure
- Copy utilities from research-agent

**Phase 2:** Tool Wrappers (2-3 hours)
- JobSpy integration
- Notion API wrapper

**Phase 3:** Agent Prompts (3-4 hours)
- Write all 5 agent prompts with XML structure
- Test prompt clarity with sample queries

**Phase 4:** Main Entry Point (1-2 hours)
- agent.py with ClaudeSDKClient setup
- Message streaming & processing

**Phase 5:** User Data & Testing (2-3 hours)
- Example base_resume.json
- End-to-end workflow testing
- Error handling validation

**Total:** ~10-15 hours for complete v1 implementation

---

## Getting Started (Quick Reference)

```bash
# 1. Clone repo
git clone <repo-url>
cd jobby_bot

# 2. Install dependencies
poetry install

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Set up user data
# Edit user_data/base_resume.json with your info
# Edit user_data/preferences.json with search criteria

# 5. Run
poetry run python -m jobby_bot.agent

# 6. Example query
"Find 20 remote Python jobs in San Francisco, generate resumes and cover letters, and track in Notion"
```

---

## Conclusion

This multi-agent system follows proven patterns from the research-agent architecture while being specifically optimized for job application automation. The clear separation of concerns, comprehensive tracking, and parallel processing make it both maintainable and efficient. By focusing on preparation (resume, cover letter) and tracking (Notion) rather than full automation, we avoid complex anti-bot detection while still providing significant time savings for job seekers.