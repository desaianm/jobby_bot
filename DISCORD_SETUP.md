# Discord Bot Setup Guide

This guide will help you set up and run Jobby Bot on Discord.

## Prerequisites

1. **Anthropic API Key** - Get from [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. **Discord Account** - For creating the bot

## Step 1: Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Jobby Bot")
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot" and confirm
5. Under "Privileged Gateway Intents", enable:
   - ✅ **Message Content Intent** (Required!)
6. Click "Reset Token" and copy your bot token
7. Save this token - you'll need it for the `.env` file

## Step 2: Configure Bot Permissions

1. Go to the "OAuth2" → "URL Generator" section
2. Select scopes:
   - ✅ `bot`
3. Select bot permissions:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
   - ✅ Read Message History
   - ✅ Mention Everyone (optional)
4. Copy the generated URL at the bottom
5. Open the URL in your browser to invite the bot to your server

## Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your tokens:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   DISCORD_BOT_TOKEN=your_discord_bot_token_here

   # Optional: For Notion integration
   NOTION_API_KEY=secret_xxxxx
   NOTION_DATABASE_ID=xxxxx
   ```

## Step 4: Install Dependencies

```bash
poetry install
```

Or if you added discord.py separately:
```bash
poetry add "discord.py"
```

## Step 5: Run the Discord Bot

```bash
poetry run python -m jobby_bot.discord_bot
```

You should see:
```
🤖 JOBBY BOT - Discord Integration
Starting Discord bot...
🤖 Jobby Bot logged in as Jobby Bot#1234
```

## How to Use

### In Discord DMs

1. Send a direct message to Jobby Bot
2. Just type your request naturally:
   ```
   Find me software engineer jobs in San Francisco
   ```

### In a Server Channel

1. Mention the bot in any channel:
   ```
   @Jobby Bot find me data science jobs in New York
   ```

### Commands

- `!jobby start` - Show welcome message and capabilities
- `!jobby help` - Get detailed help
- `!jobby end` - End your current session

### Example Interactions

**Job Search:**
```
@Jobby Bot Find me Python developer jobs in Seattle with salary over $100k
```

**Resume Generation:**
```
Create a resume for this job: https://www.linkedin.com/jobs/view/123456789
```

**Cover Letter:**
```
Write a cover letter for the Senior Engineer position at Google
```

**Track Application:**
```
Track this application in Notion: [job details]
```

## Features

- ✅ Multi-user support - Each user gets their own session
- ✅ Persistent sessions - Your conversation continues until you use `!jobby end`
- ✅ Session logging - All interactions are logged for review
- ✅ Long message handling - Responses over 2000 characters are automatically split
- ✅ Typing indicators - Shows when the bot is processing
- ✅ Auto job monitoring - Automatically checks for new jobs every 30 minutes and sends matching ones via email

## File Structure

Your setup requires:
```
user_data/
├── base_resume.json    # Your resume in JSON Resume format
└── preferences.json    # Optional job search preferences

output/
├── job_listings/       # Generated job search results
├── resumes/           # Generated resumes
└── cover_letters/     # Generated cover letters

logs/
└── session_TIMESTAMP/ # Per-session logs (one per Discord user)
```

## Troubleshooting

### Bot doesn't respond to messages

1. Check "Message Content Intent" is enabled in Discord Developer Portal
2. Verify `DISCORD_BOT_TOKEN` is correct in `.env`
3. Make sure bot is online (check Discord server member list)

### "ANTHROPIC_API_KEY not found" error

Add your API key to `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### Bot crashes on startup

Check that all required files exist:
- `jobby_bot/prompts/lead_agent.txt`
- `jobby_bot/prompts/job_finder.txt`
- `jobby_bot/prompts/resume_writer.txt`
- `jobby_bot/prompts/cover_letter.txt`
- `jobby_bot/prompts/notion_agent.txt`

### Permission errors

Ensure the bot has these permissions in your Discord server:
- Read Messages
- Send Messages
- Read Message History

## Session Management

Each Discord user gets their own isolated session:
- Sessions persist across messages
- Use `!jobby end` to clean up and view session logs
- Logs are saved in `logs/session_TIMESTAMP/`

## Cost Considerations

- Uses Sonnet 4.5 for orchestration (lead agent)
- Uses Haiku 4.5 for task execution (subagents)
- Each user session maintains its own Claude client
- Sessions are cleaned up with `!jobby end` command

## Security Notes

- Never commit `.env` file to version control
- Bot token grants full access to your Discord bot
- Keep your Anthropic API key secure
- Session logs may contain sensitive job search data

## Auto Job Monitoring

The Discord bot can automatically check for new jobs every 30 minutes (configurable) and send matching ones to your email.

### Enable Auto Monitoring

Add to your `.env` file:
```bash
ENABLE_AUTO_JOB_MONITOR=true
JOB_CHECK_INTERVAL_MINUTES=30  # Optional, defaults to 30
```

### How It Works

1. **Periodic Checks**: Bot searches for jobs based on your `user_data/preferences.json` every N minutes
2. **Smart Filtering**: Only looks at jobs posted since the last check (no duplicates)
3. **Resume Matching**: Generates customized resumes for matching jobs
4. **Email Notifications**: Sends individual emails with resumes and cover letters attached
5. **State Tracking**: Remembers which jobs have been processed in `user_data/monitor_state.json`

### Configuration

The monitor uses your preferences from `user_data/preferences.json`:
- `default_search.search_term` - Job title to search for
- `default_search.location` - Location preference
- `default_search.is_remote` - Remote job filter
- `filters.preferred_tech_stack` - Technologies to match
- `blacklist` - Companies and keywords to avoid

### Monitoring Logs

All automated job checks are logged to `logs/session_TIMESTAMP/` just like regular interactions.

## Test Your Setup

Before running the full bot, test your Discord configuration:

```bash
poetry run python test_discord.py
```

This will verify:
- Discord bot token is valid
- Bot can connect to Discord
- All required permissions are set
- Optional features are configured

## Support

For issues or questions:
1. Check session logs in `logs/session_TIMESTAMP/`
2. Review the transcript and tool calls
3. Verify all environment variables are set correctly
4. Run `poetry run python test_discord.py` to diagnose issues

## Next Steps

Once your bot is running:
1. Add your resume to `user_data/base_resume.json`
2. Configure job preferences in `user_data/preferences.json`
3. Set up Notion integration (optional)
4. Enable auto monitoring (optional)
5. Run test script: `poetry run python test_discord.py`
6. Start chatting with your bot!
