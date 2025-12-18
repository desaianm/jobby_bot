# Jobby Bot - Core Idea

## The Problem
Job hunting is exhausting. You spend hours searching for jobs, tailoring resumes, writing cover letters, and filling out repetitive application forms—often for hundreds of positions.

## The Solution
An AI agent that handles the entire job application workflow end-to-end.

## MVP: Assisted Application Flow
1. **Submit once** - Upload your resume and set job preferences
2. **AI finds jobs** - Agent scrapes LinkedIn, Indeed, Google for matching positions
3. **Smart customization** - ATS-optimized resumes and personalized cover letters generated per job
4. **Email delivery** - Receive job matches with ready-to-submit materials
5. **You decide** - Review and approve which applications to pursue

## Future Goal: Full Automation
The ultimate vision is a fully autonomous agent that:
- Automatically fills out job application forms (via browser automation)
- Attaches customized resume and cover letter
- Submits applications on your behalf
- Tracks all applications in Notion
- Sends daily summaries of applications submitted

**You focus on interviews. The bot handles the grind.**

## Technical Approach
- **Multi-Agent Architecture**: Specialized agents for each task (job search, resume writing, cover letters)
- **Browser Automation**: Playwright/Selenium for form filling (future)
- **ATS Optimization**: Keyword extraction and resume tailoring
- **Multi-User Support**: Discord bot with per-user data isolation
