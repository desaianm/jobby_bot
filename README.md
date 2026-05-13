# 🤖 Jobby Bot

> AI-powered job application automation using Agno multi-agent framework

Jobby Bot is a multi-agent system that automates job searching, resume customization, cover letter generation, browser-based auto-apply, and application tracking. Built with the **Agno** framework, it coordinates specialized AI agents via a `Team` to handle every step of your job application process.

## 🎯 Vision

**The Problem:** Job hunting is exhausting. You spend hours searching for jobs, tailoring resumes, writing cover letters, and filling out repetitive application forms—often for hundreds of positions.

**The Solution:** An AI agent that handles the entire job application workflow end-to-end.

### How It Works
1. **Submit once** - Upload your resume and set job preferences
2. **AI finds jobs** - Agent scrapes LinkedIn, Indeed, Google, Glassdoor, ZipRecruiter for matching positions
3. **Smart customization** - ATS-optimized resumes and personalized cover letters generated per job
4. **You decide** - Review jobs and choose which ones to apply to
5. **Auto-apply** - Browser automation fills out application forms and submits them
6. **Track everything** - Applications tracked in Notion, emails sent with materials

**You focus on interviews. The bot handles the grind.**

## ✨ Features

- 🔍 **Job Search**: Scrape jobs from LinkedIn, Indeed, Google, Glassdoor, and ZipRecruiter
- 📄 **Resume Customization**: ATS-optimized resumes tailored to each job (PDF, Markdown, Text)
- ✍️ **Cover Letters**: Personalized cover letters per job (PDF + Text)
- 🤖 **Auto-Apply**: Browser automation fills out and submits job application forms via `browser_use`
- 📧 **Email Automation**: Individual and summary emails with resumes and cover letters attached
- 📊 **Notion Tracking**: Track all applications in a Notion database
- 💬 **Discord Integration**: Multi-user Discord bot with slash commands and auto-monitoring
- 🔄 **Auto Job Monitor**: Periodic background job checks with email alerts (configurable interval)
- 📝 **Session Logs**: Timestamped transcripts for both CLI and Discord sessions
- 🖨️ **PDF Generation**: Chrome CDP-based pixel-perfect PDF rendering with Calibri font

## 🏗️ Architecture

Jobby Bot uses a **multi-agent architecture** powered by the Agno `Team` pattern:

- **Lead Agent / Team** (Claude Sonnet 4.5): Orchestrates workflow, delegates to members
- **Job Finder** (Claude Haiku 4.5): Searches and filters job listings via JobSpy
- **Resume Writer** (Claude Haiku 4.5): Customizes resumes with ATS optimization
- **Cover Letter Writer** (Claude Haiku 4.5): Generates personalized cover letters
- **Email Agent** (Claude Haiku 4.5): Sends application emails with attachments
- **Web Agent** (GPT-5.1 via `browser_use`): Automates job application form filling
- **Notion Agent** (Claude Haiku 4.5): Tracks applications in Notion

Agents communicate through the file system (`output/{user_id}/` folders) and custom `@tool` functions.

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

   # Optional - Discord bot
   DISCORD_BOT_TOKEN=xxx
   ENABLE_AUTO_JOB_MONITOR=true
   JOB_CHECK_INTERVAL_MINUTES=30

   # Optional - Auto-apply (browser automation)
   OPENAI_API_KEY=sk-xxx

   # Optional - Notion tracking
   NOTION_API_KEY=secret_xxx
   NOTION_DATABASE_ID=xxx

   # Optional - Email automation
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@gmail.com
   SENDER_PASSWORD=your_app_password_here
   RECIPIENT_EMAIL=your_email@gmail.com
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

6. **Set up email automation** (optional)

   To enable automated email sending with job applications:

   **For Gmail:**
   - Enable 2-factor authentication on your Google account
   - Generate an App Password: https://myaccount.google.com/apppasswords
   - Use these settings in `.env`:
     ```bash
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     SENDER_EMAIL=your_email@gmail.com
     SENDER_PASSWORD=your_app_password_here  # Use app password, not regular password
     RECIPIENT_EMAIL=your_email@gmail.com
     ```

   **For Outlook/Hotmail:**
   ```bash
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@outlook.com
   SENDER_PASSWORD=your_password
   RECIPIENT_EMAIL=your_email@outlook.com
   ```

   **For other providers:**
   - Contact your email provider for SMTP settings
   - Common ports: 587 (TLS), 465 (SSL)

   **Email features:**
   - 📧 Individual emails per job with customized resume and cover letter attached
   - 📊 Daily summary email with all applications and statistics
   - 🎨 Professional HTML formatting with job details and apply links
   - 📎 All PDFs attached for easy access

   **Test your email configuration:**
   ```bash
   python test_email.py
   ```
   This will verify your SMTP settings and send a test email. Check your inbox to confirm it's working before running the full bot.

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

### CLI Mode

Start the interactive CLI bot:

```bash
poetry run python -m jobby_bot.agent
```

### Discord Mode

Run Jobby Bot on Discord for multi-user access:

```bash
poetry run python -m jobby_bot.discord_bot
```

**Setup Discord Bot:**
1. See [DISCORD_SETUP.md](DISCORD_SETUP.md) for detailed setup instructions
2. Add `DISCORD_BOT_TOKEN` to your `.env` file
3. Interact via DMs or by mentioning the bot in channels
4. Each Discord user gets their own isolated session

**Discord Slash Commands:**
| Command | Description |
|---------|-------------|
| `/upload-resume` | Upload resume (PDF/TXT) |
| `/set-preferences` | Update job search settings |
| `/show-resume` | View current resume summary |
| `/show-preferences` | View settings and account info |
| `/set-email` | Set email for job notifications |
| `/enable-auto-monitor` | Enable automatic job alerts |
| `/disable-auto-monitor` | Disable automatic job alerts |
| `/start` | Show welcome message |
| `/help` | Get detailed help |
| `/end` | End your current session |

**Auto Job Monitoring:**
Enable automatic job checking with auto-apply by setting:
```bash
ENABLE_AUTO_JOB_MONITOR=true
JOB_CHECK_INTERVAL_MINUTES=30
```
The bot will periodically search for new jobs, generate materials, and offer to auto-apply via browser automation.

**Test Discord Setup:**
```bash
poetry run python test_discord.py
```

**Host on Windows PC:**
See [WINDOWS_HOSTING.md](WINDOWS_HOSTING.md) for a complete guide to running Jobby Bot 24/7 on a Windows PC at home with automatic startup.

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

### What happens (Interactive Workflow)

1. **Job Search**: The job-finder agent scrapes jobs and presents them to you
2. **Your Selection**: You choose which jobs to apply to (numbers, ranges, or "all")
3. **Answer Questions**: Ask about any job for details before deciding
4. **Confirm Applications**: Bot confirms the count before generating materials
5. **Resume & Cover Letter Generation**: Creates ATS-optimized resumes and personalized letters for selected jobs
6. **Auto-Apply (Optional)**: Bot offers to fill out and submit applications via browser automation
7. **Email (Optional)**: Bot asks if you want to send individual emails with attachments
8. **Notion Tracking (Optional)**: Bot asks if you want to track applications in Notion
9. **Summary**: Everything saved to `output/` folders, all actions logged

**You're in control:** The bot asks for confirmation at each major step, so you decide what happens!

### Output structure

```
output/
├── {discord_user_id}/          # Per-user output (Discord mode)
│   ├── job_listings/
│   │   └── jobs_TIMESTAMP.csv
│   ├── resumes/
│   │   ├── Company_Role_resume.pdf
│   │   ├── Company_Role_resume.txt
│   │   └── Company_Role_resume_preview.png
│   └── cover_letters/
│       ├── Company_Role_cover_letter.pdf
│       └── Company_Role_cover_letter.txt

logs/
└── session_TIMESTAMP/
    └── transcript.txt          # Timestamped conversation log
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
User Query (CLI / Discord / Auto-Monitor)
    ↓
Team Lead (Sonnet 4.5 — orchestrator)
    ↓
    ├─→ Job Finder (Haiku 4.5)
    │       ├─ Scrapes LinkedIn, Indeed, Google, Glassdoor, ZipRecruiter
    │       └─ Saves to output/{user_id}/job_listings/
    │
    ├─→ Resume Writer (Haiku 4.5) — parallel per job
    │       ├─ ATS keyword optimization
    │       └─ PDF via Chrome CDP
    │
    ├─→ Cover Letter Writer (Haiku 4.5) — parallel per job
    │
    ├─→ Web Agent (GPT-5.1 + browser_use)
    │       ├─ Navigates to application URL
    │       ├─ Fills form fields from resume JSON
    │       └─ Uploads resume PDF and submits
    │
    ├─→ Email Agent (Haiku 4.5)
    │
    └─→ Notion Agent (Haiku 4.5)
```

### Session Tracking

All conversations are logged to `logs/session_TIMESTAMP/transcript.txt` with timestamps, for both CLI and Discord sessions.

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
- **Auto-Apply**: 1-3 minutes per application (sequential, browser-based)
- **Notion Tracking**: 10-20 seconds
- **Total**: ~5-10 minutes for complete workflow

Cost per 20 applications: ~$0.50-$1.00 (using Haiku for subagents)

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Interview prep agent
- OAuth2 email authentication
- Automated follow-up scheduling
- Application status monitoring

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with [Agno](https://docs.agno.com/) multi-agent framework
- Job scraping powered by [python-jobspy](https://github.com/Bunsly/JobSpy)
- Browser automation via [browser-use](https://github.com/browser-use/browser-use)
- Notion integration via [notion-client](https://github.com/ramnes/notion-sdk-py)
- Discord bot via [discord.py](https://discordpy.readthedocs.io/)

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the `claude_plan.md` for architecture details

---

**Happy job hunting! 🎯**
