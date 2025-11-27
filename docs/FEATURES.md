# Jobby Bot Features Documentation

## Overview

This document details all features implemented in Jobby Bot, including setup instructions and usage examples.

## Core Features

### 1. Job Search & Filtering

**Capability**: Automated job scraping from multiple platforms
- **Sources**: LinkedIn, Indeed, Google Jobs, Glassdoor, ZipRecruiter
- **Filters**: Location, distance, remote, salary, job type, easy_apply, country
- **Deduplication**: Removes duplicate listings automatically
- **Blacklisting**: Filter out unwanted companies/keywords

**Usage Example**:
```
Find 20 remote AI Engineer jobs in Toronto
```

### 2. Resume Generation (PDF, Markdown, Text)

**Capability**: ATS-optimized resume customization for each job
- **Formats**: PDF (ATS-friendly), Markdown, Plain text
- **Optimization**: Keyword rewording from job descriptions (grounded in actual experience)
- **Strict Grounding**: Only rewords existing content - NEVER fabricates experience/certifications
- **Base Data**: Uses resume from SQLite database (uploaded via `/upload-resume`)

**Files Generated**:
- `output/resumes/{job_id}_resume.pdf`
- `output/resumes/{job_id}_resume.md`
- `output/resumes/{job_id}_resume.txt`

**Usage Example**:
```
Generate resumes for top 5 matches
```

### 3. Cover Letter Generation (PDF, Text)

**Capability**: Personalized, professional cover letters
- **Format**: 3-paragraph professional structure
- **Customization**: Matches job requirements with candidate experience
- **Tone**: Professional, enthusiastic, specific
- **Output**: PDF and plain text versions

**Files Generated**:
- `output/cover_letters/{job_id}_cover_letter.pdf`
- `output/cover_letters/{job_id}_cover_letter.txt`

**Usage Example**:
```
Write cover letters for all jobs found
```

### 4. Email Automation

**Capability**: Automated email delivery of job applications
- **Individual Emails**: One per job with PDF attachments
- **Summary Email**: Daily digest with all applications
- **Content**: HTML formatted with job details and apply links
- **Attachments**: Resume and cover letter PDFs

**Setup Required**:
```bash
# In .env file
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=your_email@gmail.com
```

**Gmail Setup**:
1. Enable 2FA on Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in SENDER_PASSWORD

**Test Email**:
```bash
python test_email.py
```

**Email Features**:
- Professional HTML formatting
- Job details (title, company, location, salary)
- Direct "Apply Now" link
- PDF attachments (resume + cover letter)
- Statistics in summary email

### 5. Notion Integration

**Capability**: Track all applications in Notion database
- **Auto-creation**: Creates entry for each job
- **Fields**: Job title, company, location, status, URLs, salary
- **File Links**: Links to generated resumes/cover letters
- **Status Tracking**: To Apply, Applied, Interview, etc.

**Setup Required**:
```bash
# In .env file
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=xxx
```

**Database Properties** (auto-created by setup script):
- Job Title (title)
- Company (rich_text)
- Location (rich_text)
- Status (select)
- Applied Date (date)
- Job URL (url)
- Resume Link (url)
- Cover Letter Link (url)
- Salary (rich_text)
- Notes (rich_text)

### 6. Configuration Management

**Capability**: Update preferences and resume through Discord slash commands

**Discord Slash Commands**:
| Command | Description |
|---------|-------------|
| `/upload-resume` | Upload resume (PDF/TXT) - extracts text automatically |
| `/set-preferences` | Update job search settings |
| `/show-resume` | View current resume summary |
| `/show-preferences` | View settings and account info |
| `/set-email` | Set email for job notifications |
| `/enable-auto-monitor` | Enable automatic job alerts (default: every 30 min) |
| `/disable-auto-monitor` | Disable automatic job alerts |

**Data Storage**: All user data stored in SQLite database per Discord user ID

### 7. PDF Resume Conversion

**Capability**: Convert PDF resumes to JSON format using AI
- **Input**: Any text-based PDF resume
- **Processing**: Claude extracts and structures content
- **Output**: Valid JSON Resume format
- **Sections**: Contact, summary, work, education, skills, projects

**Usage**:
```bash
python scripts/pdf_to_json_resume.py my_resume.pdf
```

**What Gets Extracted**:
- Contact information (name, email, phone, location)
- Professional summary
- Work experience with bullet points
- Education history
- Skills organized by category
- Projects (if present)
- Certifications (if present)

## Workflow Examples

### Basic Job Search
```
User: Find 10 remote Python jobs
Bot:  Searches jobs → Saves to CSV
```

### Full Application Pipeline
```
User: Find 20 AI Engineer jobs in Toronto
Bot:
  1. Searches jobs (40 found)
  2. Filters and ranks by match score
  3. Selects top 3 matches
  4. Generates 3 resumes (PDF, MD, TXT each)
  5. Generates 3 cover letters (PDF, TXT each)
  6. Sends 3 individual emails with PDFs
  7. Creates 3 Notion entries
  8. Sends 1 summary email with all PDFs
```

### Configuration Update Then Search
```
User: Update my location to New York and set distance to 75 miles
Bot:  ✓ Location updated
      ✓ Distance updated

User: Now find 15 Data Scientist jobs
Bot:  [Uses new preferences for search]
```

## Output Files Structure (Per-User)

```
output/
├── {discord_user_id}/                    # Per-user output folders
│   ├── job_listings/
│   │   └── jobs_20250121_143022.csv      # Raw job search results
│   ├── resumes/
│   │   ├── job_1_resume.pdf              # ATS-friendly PDF
│   │   ├── job_1_resume.md               # Formatted markdown
│   │   ├── job_1_resume.txt              # Plain text
│   │   └── ...
│   └── cover_letters/
│       ├── job_1_cover_letter.pdf        # Professional PDF
│       ├── job_1_cover_letter.txt        # Plain text
│       └── ...
```

## Session Logs

All agent activity is tracked in:
```
logs/
└── session_20250121_143022/
    ├── transcript.txt                     # Human-readable conversation
    └── tool_calls.jsonl                   # Structured tool invocations
```

## Advanced Features

### Parallel Processing
- Multiple agents run simultaneously for speed
- Resume and cover letter generation happens in parallel
- Individual emails sent concurrently

### ATS Optimization
- Keyword extraction from job descriptions
- Exact phrase matching for ATS systems
- Simple, clean PDF formatting (no graphics/tables)
- Standard section headings

### Smart Matching
- Match score calculation based on skills/requirements
- Top candidates selected automatically
- Blacklist filtering applied

### Error Handling
- Graceful degradation (continues if email not configured)
- Validation before saving files
- Clear error messages with troubleshooting tips

## Testing Tools

### Email Configuration Test
```bash
python test_email.py
```
Verifies SMTP settings and sends test email.

### PDF Generation Test
Automatically tested during first resume/cover letter generation.

## Environment Variables Reference

### Required
```bash
ANTHROPIC_API_KEY=sk-ant-xxx
```

### Optional (Features)
```bash
# Email automation
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=app_password
RECIPIENT_EMAIL=your_email@gmail.com

# Notion tracking
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=xxx
```

## Feature Flags

All features are enabled by default if configured. The bot automatically:
- Skips email if SMTP not configured
- Skips Notion if API key not set
- Always generates resumes/cover letters if jobs found

## Future Enhancements

Potential additions:
- Interview prep agent
- Application status monitoring
- Automated follow-up scheduling
- OAuth2 email authentication
