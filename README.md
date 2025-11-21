# 🤖 Jobby Bot

> AI-powered job application automation using Claude Agent SDK

Jobby Bot is a multi-agent system that automates job searching, resume customization, cover letter generation, and application tracking. Built with the Claude Agent SDK, it coordinates specialized AI agents to handle every step of your job application process.

## ✨ Features

- 🔍 **Job Search**: Scrape jobs from LinkedIn, Indeed, and Google with advanced filtering
- 📄 **Resume Customization**: Generate ATS-optimized resumes tailored to each job
- ✍️ **Cover Letters**: Create personalized, professional cover letters
- 📊 **Notion Tracking**: Track all applications in a Notion database
- 🚀 **Parallel Processing**: Generate materials for multiple jobs simultaneously
- 📝 **Session Logs**: Complete tracking of all agent actions and tool calls
- 🔄 **PDF Conversion**: Convert existing PDF resumes to JSON format automatically

## 🏗️ Architecture

Jobby Bot uses a **multi-agent architecture** with a lead orchestrator and specialized subagents:

- **Lead Agent** (Claude Sonnet 4.5): Coordinates workflow and spawns subagents
- **Job Finder** (Claude Haiku 4.5): Searches and filters job listings
- **Resume Writer** (Claude Haiku 4.5): Customizes resumes with ATS optimization
- **Cover Letter Writer** (Claude Haiku 4.5): Generates personalized cover letters
- **Notion Agent** (Claude Haiku 4.5): Tracks applications in Notion

All agents communicate through the file system (`output/` folders) and are tracked via hooks for complete observability.

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (Python package manager)
- Anthropic API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jobby_bot
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```bash
   # Required
   ANTHROPIC_API_KEY=sk-ant-xxx

   # Optional (for Notion tracking)
   NOTION_API_KEY=secret_xxx
   NOTION_DATABASE_ID=xxx
   ```

   Get your Anthropic API key: https://console.anthropic.com/settings/keys

4. **Set up your resume**

   **Option A: Edit JSON directly**

   Edit `user_data/base_resume.json` with your information (follows [JSON Resume](https://jsonresume.org/) format)

   **Option B: Convert from PDF**

   If you have a PDF resume, use the conversion script:
   ```bash
   poetry run python scripts/pdf_to_json_resume.py path/to/your_resume.pdf
   ```

   This will use Claude to extract and structure your resume into JSON format automatically. Review and edit the generated `user_data/base_resume.json` file.

5. **Configure preferences** (optional)

   Edit `user_data/preferences.json` to set:
   - Default search criteria
   - Blacklisted companies/keywords
   - Salary filters
   - Preferred tech stack

## 🔄 PDF Resume Conversion

If you have your resume in PDF format, Jobby Bot includes a utility to automatically convert it to JSON Resume format.

### Usage

```bash
# Convert PDF to JSON Resume (saves to user_data/base_resume.json)
poetry run python scripts/pdf_to_json_resume.py my_resume.pdf

# Save to custom location
poetry run python scripts/pdf_to_json_resume.py my_resume.pdf --output custom.json

# Preview extracted text without converting
poetry run python scripts/pdf_to_json_resume.py my_resume.pdf --preview-text
```

### How it works

1. **Extract Text**: Uses `pdfplumber` to extract all text from your PDF
2. **AI Conversion**: Uses Claude (Sonnet 4.5) to intelligently parse and structure the content
3. **JSON Output**: Generates a valid JSON Resume with all sections properly formatted
4. **Review**: You can review and edit the output before using it

### What gets extracted

- ✅ Contact information (name, email, phone, location)
- ✅ Professional summary
- ✅ Work experience with detailed bullet points
- ✅ Education history
- ✅ Skills organized by category
- ✅ Projects (if present)
- ✅ Certifications (if present)
- ✅ Social profiles (LinkedIn, GitHub)

### Tips

- Make sure your PDF is text-based (not a scanned image)
- Review the generated JSON for accuracy
- Edit any missing or incorrect information
- The AI is smart but may need manual corrections for complex layouts

## 🚀 Usage

### Start the bot

```bash
poetry run python -m jobby_bot.agent
```

### Example queries

**Basic job search:**
```
Find 10 remote Python jobs
```

**Full workflow:**
```
Find 20 software engineer jobs in San Francisco, generate resumes and cover letters, and track in Notion
```

**Search only:**
```
Search for data analyst jobs in New York, don't generate materials yet
```

**Custom criteria:**
```
Find 15 remote backend engineer jobs posted in the last 48 hours
```

### What happens

1. **Job Search**: The job-finder agent scrapes jobs from multiple sites and filters based on your preferences
2. **Resume Generation**: For each job, the resume-writer creates an ATS-optimized resume
3. **Cover Letters**: The cover-letter agent generates personalized letters
4. **Notion Tracking**: All jobs are added to your Notion database with links to materials
5. **Output Files**: Everything is saved to `output/` folders

### Output structure

```
output/
├── job_listings/
│   └── jobs_20250115_123045.csv
├── resumes/
│   ├── job_0_resume.md
│   ├── job_0_resume.txt
│   └── ...
└── cover_letters/
    ├── job_0_cover_letter.txt
    └── ...

logs/
└── session_20250115_123045/
    ├── transcript.txt
    └── tool_calls.jsonl
```

## 📊 Notion Setup (Optional)

To track applications in Notion:

1. **Create a Notion integration**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Copy the "Internal Integration Token"

2. **Create a database**
   - Create a new Notion page
   - Add a database with these properties:
     - Job Title (Title)
     - Company (Text)
     - Job URL (URL)
     - Status (Select): To Apply, Applied, Interview, Offer, Rejected
     - Description (Text)
     - Location (Text)
     - Salary (Text)
     - Resume Path (Text)
     - Cover Letter Path (Text)
     - Applied Date (Date)

3. **Connect integration to database**
   - Open your database page
   - Click "..." menu → "Add connections"
   - Select your integration

4. **Get database ID**
   - Copy the database URL
   - Extract the ID (part between workspace name and `?v=`)
   - Example: `https://notion.so/workspace/DATABASE_ID?v=...`

5. **Update .env**
   ```bash
   NOTION_API_KEY=secret_xxx
   NOTION_DATABASE_ID=DATABASE_ID
   ```

## 🎯 How It Works

### Multi-Agent Coordination

```
User Query
    ↓
Lead Agent (orchestrator)
    ↓
    ├─→ Job Finder Agent
    │       ├─ Scrapes LinkedIn, Indeed, Google
    │       ├─ Applies filters
    │       └─ Saves to CSV
    │
    ├─→ Resume Writer Agents (parallel)
    │       ├─ Reads base resume
    │       ├─ Extracts ATS keywords
    │       └─ Generates customized resume
    │
    ├─→ Cover Letter Agents (parallel)
    │       ├─ Analyzes job requirements
    │       └─ Writes personalized letter
    │
    └─→ Notion Agent
            ├─ Creates database entries
            └─ Links all materials
```

### Agent Tools

Each agent has access to specific tools:

- **Lead Agent**: `Task` (spawns subagents only)
- **Job Finder**: `JobSpyTool`, `Write`, `Read`, `Glob`, `Bash`
- **Resume Writer**: `Read`, `Write`
- **Cover Letter**: `Read`, `Write`
- **Notion Agent**: `NotionTool`, `Read`, `Write`, `Bash`

### Session Tracking

All agent actions are tracked via hooks:
- `PreToolUse`: Captures tool invocations with inputs
- `PostToolUse`: Captures tool results and errors
- Logs saved to `logs/session_*/tool_calls.jsonl`

## 🔧 Configuration

### Resume Format

Jobby Bot uses the [JSON Resume](https://jsonresume.org/) format for maximum compatibility. Your `base_resume.json` should include:

- `basics`: Name, contact, summary
- `work`: Work experience with highlights
- `education`: Education history
- `skills`: Technical and soft skills
- `projects`: Optional projects
- `certificates`: Optional certifications

### Preferences

Configure `user_data/preferences.json` to customize:

```json
{
  "default_search": {
    "search_term": "software engineer",
    "location": "San Francisco, CA",
    "is_remote": false,
    "results_wanted": 20
  },
  "blacklist": {
    "companies": ["Company A"],
    "keywords": ["unpaid", "commission-only"]
  },
  "filters": {
    "min_salary": 100000,
    "preferred_tech_stack": ["Python", "Django"]
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**"ANTHROPIC_API_KEY not found"**
- Make sure `.env` file exists in project root
- Check that the API key is correctly set
- Try `export ANTHROPIC_API_KEY=sk-ant-xxx` in your shell

**"Could not read base_resume.json"**
- Create `user_data/base_resume.json` with your resume data
- Follow JSON Resume schema
- Validate JSON syntax

**"Notion database not accessible"**
- Verify NOTION_API_KEY and NOTION_DATABASE_ID in `.env`
- Make sure integration has access to database
- Check database has required properties (Job Title, Status)

**Job search returns no results**
- Try broader search terms
- Reduce `hours_old` filter (try 168 for 1 week)
- Check if sites are blocking requests (rate limiting)

### Debug Mode

View detailed logs in `logs/session_*/`:
- `transcript.txt`: Human-readable conversation
- `tool_calls.jsonl`: Structured tool call records

## 📈 Performance

Typical execution times (20 jobs):

- **Job Search**: 30-60 seconds
- **Resume Generation**: 2-3 minutes (parallel)
- **Cover Letters**: 2-3 minutes (parallel)
- **Notion Tracking**: 10-20 seconds
- **Total**: ~4-5 minutes for complete workflow

Cost per 20 applications: ~$0.50-$1.00 (using Haiku for subagents)

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional job sites (ZipRecruiter, Glassdoor)
- Resume PDF generation (currently markdown/text only)
- Email integration for application submission
- Interview prep agent
- Application status monitoring

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- Job scraping powered by [python-jobspy](https://github.com/Bunsly/JobSpy)
- Notion integration via [notion-client](https://github.com/ramnes/notion-sdk-py)

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the `claude_plan.md` for architecture details

---

**Happy job hunting! 🎯**
