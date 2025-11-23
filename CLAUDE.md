# Jobby Bot - Project Documentation

## Project Overview

**Jobby Bot** is an AI-powered job application automation system built with the Claude Agent SDK. It orchestrates multiple specialized agents to handle job searching, resume customization, cover letter generation, and application tracking.

### Core Architecture

- **Multi-Agent System**: Lead orchestrator + specialized subagents
- **Model Strategy**: Sonnet 4.5 for orchestration, Haiku 4.5 for task execution
- **Communication**: File-based via `output/` folders
- **Tracking**: Hooks for complete observability (`logs/session_*/`)

## Development Conventions

### 1. Code Changes
- **Minimal modifications**: Only change what's necessary for the task
- **Root cause fixes**: Identify underlying problems, not symptoms
- **No over-engineering**: Avoid adding features not explicitly requested
- **Security first**: No vulnerabilities, use production-ready patterns

### 2. Agent Design Principles
- **Single responsibility**: Each agent has ONE specific job
- **Tool restrictions**: Lead agent ONLY uses `Task` tool
- **Model selection**: Use Haiku for cost-effective subagents
- **No cross-contamination**: Agents don't perform other agents' tasks
- **Temporary scripts**: ALL agents use tmp/ folder for scripts, clean up before returning
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

### Lead Agent (Orchestrator)
- **Model**: claude-sonnet-4-5
- **Tools**: `Task` ONLY (spawns subagents)
- **Role**: Workflow coordination, no direct execution
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
- **Model**: claude-haiku-4-5
- **Tools**: `Bash`, `Read`, `Write`, `Glob`
- **Role**: Scrape jobs via JobSpy (LinkedIn, Indeed, Google)
- **Output**: `output/job_listings/jobs_TIMESTAMP.csv`
- **Prompt**: `prompts/job_finder.txt`

### Resume Writer Agent
- **Model**: claude-haiku-4-5
- **Tools**: `Read`, `Write`, `Bash`
- **Input**: `user_data/base_resume.json` (JSON Resume format)
- **Output**: `output/resumes/job_N_resume.{pdf,md,txt}` - ATS optimization with keyword extraction
- **Prompt**: `prompts/resume_writer.txt`

### Cover Letter Agent
- **Model**: claude-haiku-4-5
- **Tools**: `Read`, `Write`, `Bash`
- **Output**: `output/cover_letters/job_N_cover_letter.{pdf,txt}` - 3-paragraph professional letter
- **Prompt**: `prompts/cover_letter.txt`

### Email Agent
- **Model**: claude-haiku-4-5
- **Tools**: `Bash`, `Read`
- **Role**: Send individual job emails + daily summary via SMTP with PDF attachments
- **Requires**: `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`, `RECIPIENT_EMAIL`
- **Prompt**: `prompts/email_agent.txt`

### Config Agent
- **Model**: claude-haiku-4-5
- **Tools**: `Read`, `Write`
- **Role**: Update preferences.json and base_resume.json when user provides config changes
- **Prompt**: `prompts/config_agent.txt`

### Notion Agent
- **Model**: claude-haiku-4-5
- **Tools**: `Bash`, `Read`, `Write`
- **Role**: Track applications in Notion database
- **Requires**: `NOTION_API_KEY`, `NOTION_DATABASE_ID`
- **Prompt**: `prompts/notion_agent.txt`

## Common Development Patterns

### Adding a New Agent

1. **Create prompt file**: `jobby_bot/prompts/new_agent.txt`
2. **Define agent** in `agent.py`:
```python
agents = {
    "new-agent": AgentDefinition(
        description="Clear description of when to use this agent",
        tools=["Read", "Write"],  # Minimal tools needed
        prompt=load_prompt("new_agent.txt"),
        model="haiku"  # Use haiku unless complexity requires sonnet
    )
}
```
3. **Update lead agent prompt** to reference new capability

### Creating Custom Tools

1. **Implement tool** in `jobby_bot/tools/`:
```python
class NewTool(Tool):
    name: Literal["NewTool"]
    description: str = "What this tool does"

    def execute(self, context: ToolContext) -> ToolResult:
        # Implementation
        return ToolResult(output="result")
```

2. **Register in tools/__init__.py**
3. **Add to agent's allowed tools** in agent definition

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

All tool calls are automatically tracked via hooks:

```python
# Pre-execution hook
tracker.pre_tool_use_hook(agent_id, tool_name, params)

# Post-execution hook
tracker.post_tool_use_hook(agent_id, tool_name, result)
```

Logs saved to: `logs/session_TIMESTAMP/tool_calls.jsonl`

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
- `claude-agent-sdk ^0.1.0` - Multi-agent framework
- `anthropic ^0.39.0` - Claude API client

### Job Search
- `python-jobspy` - Scrapes LinkedIn, Indeed, Google jobs

### Integration
- `discord.py ^2.3.0` - Discord bot interface
- `notion-client ^2.2.1` - Notion database integration

### Document Generation
- `selenium ^4.38.0` - Chrome CDP for pixel-perfect PDF rendering (AIHawk approach)
- `webdriver-manager ^4.0.2` - Automated ChromeDriver management
- `pdfplumber ^0.11.0` - PDF text extraction for resume conversion

### Utilities
- `pydantic ^2.0.0` - Data validation
- `python-dotenv ^1.0.0` - Environment management
- `pandas ^2.0.0` - Data manipulation
- `jinja2 ^3.1.0` - Template rendering

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

- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk), [Discord.py](https://discordpy.readthedocs.io/), [Notion API](https://developers.notion.com/)

## Maintenance Notes

- Keep agent prompts concise and focused
- Update this documentation when adding new agents/features
- Monitor costs via API usage dashboard
- Review session logs periodically for improvement opportunities
- when update claude.md do it very condensely and concise, with max 2 lines for doc references and features.