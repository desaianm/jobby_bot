# Jobby Bot - Project Documentation

## Project Overview

**Jobby Bot** is an AI-powered job application automation system built with **Agno** framework. It orchestrates multiple specialized agents via `Team` to handle job searching, resume customization, cover letter generation, and application tracking.

### Core Architecture

- **Multi-Agent System**: Agno `Team` with specialized `Agent` members
- **Model Strategy**: Sonnet 4.5 for Team orchestration, Haiku 4.5 for member agents
- **Communication**: File-based via `output/` folders + custom `@tool` functions
- **Tracking**: Session transcripts (`logs/session_*/`)

## Development Conventions

### 1. Code Changes
- **Minimal modifications**: Only change what's necessary for the task
- **Root cause fixes**: Identify underlying problems, not symptoms
- **No over-engineering**: Avoid adding features not explicitly requested
- **Security first**: No vulnerabilities, use production-ready patterns

### 2. Agent Design Principles (Agno)
- **Single responsibility**: Each `Agent` has ONE specific role
- **Team orchestration**: `Team` coordinates members via `show_members_responses=True`
- **Model selection**: Use Haiku for cost-effective member agents
- **Custom tools**: Use `@tool` decorator for agent capabilities
- **No summary files**: Agents NEVER create summary.md files, only final task output

### 3. File Organization
```
jobby_bot/
├── agent.py              # CLI orchestrator entry point
├── discord_bot.py        # Discord bot with slash commands + tasks.loop auto-monitor
├── discord_commands.py   # Slash command definitions (upload-resume, set-preferences, etc.)
├── auto_job_monitor.py   # Standalone monitor (deprecated, use Discord tasks.loop)
├── prompts/              # Agent system prompts (txt files)
│   ├── lead_agent.txt
│   ├── job_finder.txt
│   ├── resume_writer.txt
│   ├── cover_letter.txt
│   ├── email_agent.txt
│   ├── notion_agent.txt
│   └── config_agent.txt
├── tools/                # Custom tools for agents
│   ├── jobspy_tool.py
│   └── notion_tool.py
├── utils/                # Shared utilities
│   ├── subagent_tracker.py
│   ├── transcript.py
│   ├── message_handler.py
│   ├── email_sender.py
│   ├── pdf_generator.py         # Main PDF interface
│   ├── chrome_pdf_generator.py  # Chrome CDP rendering (AIHawk method)
│   └── html_content_generator.py # HTML generation with smart formatting
└── tmp/                  # Temporary scripts (auto-cleaned by agents)
    └── .gitkeep
```

### 4. Output Structure
```
output/
├── job_listings/         # CSV files from JobSpy
├── resumes/             # Generated resumes (pdf + md + txt)
└── cover_letters/       # Generated cover letters (pdf + txt)

logs/
└── session_TIMESTAMP/
    ├── transcript.txt   # Human-readable conversation
    └── tool_calls.jsonl # Structured tool invocations
```

## Agent Definitions

### Team (Orchestrator)
- **Model**: claude-sonnet-4-5-20250514
- **Type**: Agno `Team` with member agents
- **Role**: Workflow coordination, delegates to member agents
- **Interactive**: ALWAYS asks user to confirm job selections, emails, Notion tracking
- **Prompt**: `prompts/lead_agent.txt`

**Interactive Workflow:**
1. Search for jobs → Present list to user
2. Ask which jobs to apply to (numbers, ranges, or "all")
3. Answer any user questions about specific jobs
4. Confirm number of applications before generating materials
5. Ask before sending emails (if configured)
6. Ask before tracking in Notion (if configured)
7. Ask before sending summary email (if configured)

### Job Finder Agent
- **Model**: claude-haiku-4-5-20250514
- **Tools**: `search_jobs`, `read_file`, `write_file` (custom @tool functions)
- **Role**: Scrape jobs via JobSpy (LinkedIn, Indeed, Google)
- **Output**: `output/job_listings/jobs_TIMESTAMP.csv`

### Resume Writer Agent
- **Model**: claude-haiku-4-5-20250514
- **Tools**: `read_file`, `write_file`, `generate_pdf`
- **Input**: `user_data/base_resume.json` (JSON Resume format)
- **Output**: `output/resumes/job_N_resume.{pdf,md,txt}` - ATS optimization

### Cover Letter Agent
- **Model**: claude-haiku-4-5-20250514
- **Tools**: `read_file`, `write_file`, `generate_pdf`
- **Output**: `output/cover_letters/job_N_cover_letter.{pdf,txt}`

### Email Agent
- **Model**: claude-haiku-4-5-20250514
- **Tools**: `send_email`, `read_file`
- **Requires**: `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`, `RECIPIENT_EMAIL`

### Notion Agent
- **Model**: claude-haiku-4-5-20250514
- **Tools**: `create_notion_entry`, `read_file`
- **Requires**: `NOTION_API_KEY`, `NOTION_DATABASE_ID`

## Common Development Patterns

### Adding a New Agent (Agno)

1. **Create prompt file**: `jobby_bot/prompts/new_agent.txt`
2. **Define agent** in `agent.py`:
```python
new_agent = Agent(
    name="New Agent",
    role="Clear description of agent role",
    model=Claude(id="claude-haiku-4-5-20251001"),
    tools=[custom_tool_function],
    instructions=load_prompt("new_agent.txt"),
    markdown=True,
)
```
3. **Add to team members** in `create_team()` function

### Creating Custom Tools (Agno)

Use the `@tool` decorator for custom tools:
```python
from agno.tools import tool

@tool
def custom_tool(param: str) -> str:
    """Tool description for the model.

    Args:
        param: Parameter description

    Returns:
        Result description
    """
    # Implementation
    return "result"
```
Add to agent's `tools=[]` list

### PDF Generation (AIHawk Chrome CDP Approach)

The system uses Chrome DevTools Protocol for pixel-perfect PDF rendering:

**Workflow:**
1. Plain text content → HTML generation (`html_content_generator.py`)
2. HTML → Chrome headless browser (`chrome_pdf_generator.py`)
3. Browser renders → `Page.printToPDF` CDP command
4. Base64 PDF output → Save to file

**Key Features:**
- **Calibri font** for professional appearance
- **Smart text normalization**: Converts all-caps paragraphs to sentence case
- **Tech term preservation**: LangChain, Python, React keep proper casing
- **ATS-friendly**: Clean HTML structure, no blue hyperlinks
- **Pixel-perfect**: Exact browser rendering quality

**Usage:**
```python
from jobby_bot.utils.pdf_generator import create_resume_pdf, create_cover_letter_pdf

create_resume_pdf(text_content, "output/resumes/resume.pdf")
create_cover_letter_pdf(text_content, "output/cover_letters/cover_letter.pdf")
```

### Session Tracking

Transcripts saved to: `logs/session_TIMESTAMP/transcript.txt`

## Environment Configuration

### Required Variables
```bash
ANTHROPIC_API_KEY=sk-ant-xxx  # Get from console.anthropic.com
```

### Optional Variables
```bash
DISCORD_BOT_TOKEN=xxx                   # Discord bot token (for Discord mode)
ENABLE_AUTO_JOB_MONITOR=true            # Enable auto job checking (Discord mode)
JOB_CHECK_INTERVAL_MINUTES=30           # How often to check for jobs (default: 30)
NOTION_API_KEY=secret_xxx               # For application tracking
NOTION_DATABASE_ID=xxx                  # Your Notion database ID
SMTP_SERVER=smtp.gmail.com              # Email automation
SMTP_PORT=587                           # Standard TLS port
SENDER_EMAIL=your@email.com             # Email to send from
SENDER_PASSWORD=app_password            # Email password or app password
RECIPIENT_EMAIL=your@email.com          # Where to receive job emails
```

### User Data Files
- `user_data/base_resume.json` - Your resume (JSON Resume format)
- `user_data/preferences.json` - Search filters, blacklists, preferences
- `user_data/monitor_state.json` - Auto-generated state for job monitoring (tracks processed jobs)

## Testing and Debugging

### Running the Bot
```bash
# CLI Mode
poetry run python -m jobby_bot.agent

# Discord Mode (with optional auto-monitoring using tasks.loop)
poetry run python -m jobby_bot.discord_bot

# Standalone Auto Monitor (deprecated - use Discord auto-monitor instead)
poetry run python -m jobby_bot.auto_job_monitor

# Test Discord Setup
poetry run python test_discord.py
```

### Windows Hosting
For running 24/7 on a Windows PC, see [WINDOWS_HOSTING.md](WINDOWS_HOSTING.md) - includes service installation, auto-startup, and maintenance scripts.

### Debug Session Logs
1. Check `logs/session_TIMESTAMP/transcript.txt` for conversation flow
2. Check `tool_calls.jsonl` for tool invocation details
3. Check `output/` folders for generated files

### Common Issues

**Agent not spawning correctly**
- Check agent name matches exactly (case-sensitive)
- Verify tools are registered in AgentDefinition
- Ensure prompt file exists in `prompts/`

**Tool execution fails**
- Check tool is in agent's allowed_tools list
- Verify tool has proper execute() implementation
- Check logs for error details

**No output files**
- Ensure `output/` directories exist (created automatically)
- Check agent has Write permission
- Verify file paths in agent prompt

## Key Dependencies

### Core
- `agno` - Multi-agent framework with Team/Agent pattern
- `anthropic ^0.39.0` - Claude API client

### Job Search
- `python-jobspy` - Scrapes LinkedIn, Indeed, Google jobs

### Integration
- `discord.py ^2.3.0` - Discord bot interface
- `notion-client ^2.2.1` - Notion database integration

### Utilities
- `pydantic ^2.0.0`, `python-dotenv ^1.0.0`, `pandas ^2.0.0`

## Best Practices

### 1. Prompt Engineering
- Be explicit about agent boundaries (what it should NOT do)
- Include examples of expected input/output
- Specify error handling behavior
- Use clear, imperative language

### 2. Error Handling
- Always check for required files before reading
- Validate environment variables at startup
- Provide helpful error messages with remediation steps

### 3. File Management
- Use timestamps in filenames to avoid collisions
- Create output directories if they don't exist
- Clean up temporary files after use

### 4. Performance
- Use Haiku for simple tasks (cost-effective)
- Run parallel agents for independent tasks
- Batch similar operations when possible

### 5. Security
- Never commit `.env` files
- Validate all file paths before operations
- Sanitize user inputs before file operations
- Use read-only queries for database operations

## Future Enhancements

Potential areas for expansion:
- Additional job sites (ZipRecruiter, Glassdoor)
- Interview prep agent
- Application status monitoring
- Automated follow-up scheduling

## Resources

- [Agno Docs](https://docs.agno.com/), [Discord.py](https://discordpy.readthedocs.io/), [Notion API](https://developers.notion.com/)

## Maintenance Notes

- Keep agent prompts concise and focused
- Update this documentation when adding new agents/features
- Monitor costs via API usage dashboard
- Review session logs periodically for improvement opportunities
- when update claude.md do it very condensely and concise, with max 2 lines for doc references and features.