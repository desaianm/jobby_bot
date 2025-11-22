# Windows PC Hosting Guide

This guide will help you set up Jobby Bot to run 24/7 on a Windows PC at home, with automatic startup and Discord integration.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Running as a Background Service](#running-as-a-background-service)
- [Auto-Start on Boot](#auto-start-on-boot)
- [Network Configuration](#network-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements
- **Windows PC** (Windows 10/11 or Windows Server)
- **Minimum 4GB RAM** (8GB recommended)
- **5GB free disk space** (for Python, dependencies, and logs)
- **Stable internet connection** (for API calls and job scraping)
- **Always-on capability** (PC should stay powered on)

### Software Requirements
- Windows 10/11 or Windows Server 2016+
- Administrator access
- Internet connection

## Initial Setup

### 1. Install Python

1. **Download Python 3.11 or higher**:
   - Go to https://www.python.org/downloads/windows/
   - Download Python 3.11.x (64-bit recommended)

2. **Run the installer**:
   - ✅ **IMPORTANT**: Check "Add Python to PATH"
   - ✅ Check "Install for all users" (if you have admin access)
   - Click "Install Now"

3. **Verify installation**:
   ```cmd
   python --version
   pip --version
   ```

### 2. Install Git (Optional but Recommended)

1. Download from https://git-scm.com/download/win
2. Run installer with default settings
3. Verify: `git --version`

### 3. Install Poetry

Open PowerShell as Administrator and run:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Add Poetry to PATH:
1. Open "Environment Variables" (Win + S, search "environment")
2. Edit "Path" under User variables
3. Add: `C:\Users\YourUsername\AppData\Roaming\Python\Scripts`
4. Restart PowerShell

Verify:
```powershell
poetry --version
```

### 4. Clone and Setup Jobby Bot

```powershell
# Navigate to where you want to install (e.g., C:\JobbyBot)
cd C:\
mkdir JobbyBot
cd JobbyBot

# Clone or copy your project here
# If using Git:
git clone <your-repo-url> .

# Install dependencies
poetry install
```

### 5. Configure Environment Variables

1. Create `.env` file in the project root:
   ```powershell
   copy .env.example .env
   notepad .env
   ```

2. Fill in your credentials:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   DISCORD_BOT_TOKEN=xxxxx
   ENABLE_AUTO_JOB_MONITOR=true
   JOB_CHECK_INTERVAL_MINUTES=30

   # Email settings
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@gmail.com
   SENDER_PASSWORD=your_app_password
   RECIPIENT_EMAIL=your_email@gmail.com

   # Optional: Notion
   NOTION_API_KEY=secret_xxxxx
   NOTION_DATABASE_ID=xxxxx
   ```

3. Setup your resume and preferences:
   ```powershell
   # Edit your resume
   notepad user_data\base_resume.json

   # Edit job preferences
   notepad user_data\preferences.json
   ```

### 6. Test the Setup

```powershell
# Test Discord connection
poetry run python test_discord.py

# Run the bot manually (Ctrl+C to stop)
poetry run python -m jobby_bot.discord_bot
```

If everything works, proceed to set up as a service.

## Running as a Background Service

### Option 1: Using NSSM (Non-Sucking Service Manager) - RECOMMENDED

NSSM is the easiest way to run Python scripts as Windows services.

#### Install NSSM

1. Download from https://nssm.cc/download
2. Extract to `C:\nssm\`
3. Add to PATH or use full path

#### Create the Service

1. **Create a startup batch file** (`C:\JobbyBot\start_discord_bot.bat`):
   ```batch
   @echo off
   cd /d C:\JobbyBot
   C:\Users\YourUsername\AppData\Local\pypoetry\Cache\virtualenvs\jobby-bot-xxxxx-py3.11\Scripts\python.exe -m jobby_bot.discord_bot
   ```

   To find your virtualenv path:
   ```powershell
   poetry env info --path
   ```

2. **Install the service** (Run PowerShell as Administrator):
   ```powershell
   cd C:\nssm\win64

   # Install service
   .\nssm.exe install JobbyBot "C:\JobbyBot\start_discord_bot.bat"

   # Configure service
   .\nssm.exe set JobbyBot AppDirectory "C:\JobbyBot"
   .\nssm.exe set JobbyBot DisplayName "Jobby Bot - Discord Job Assistant"
   .\nssm.exe set JobbyBot Description "Automated job search and application bot with Discord interface"
   .\nssm.exe set JobbyBot Start SERVICE_AUTO_START

   # Set up logging
   .\nssm.exe set JobbyBot AppStdout "C:\JobbyBot\logs\service_output.log"
   .\nssm.exe set JobbyBot AppStderr "C:\JobbyBot\logs\service_error.log"

   # Rotate logs (10MB limit)
   .\nssm.exe set JobbyBot AppRotateFiles 1
   .\nssm.exe set JobbyBot AppRotateBytes 10485760
   ```

3. **Start the service**:
   ```powershell
   .\nssm.exe start JobbyBot
   ```

4. **Check service status**:
   ```powershell
   .\nssm.exe status JobbyBot
   ```

#### Service Management Commands

```powershell
# Start service
nssm start JobbyBot

# Stop service
nssm stop JobbyBot

# Restart service
nssm restart JobbyBot

# Remove service
nssm remove JobbyBot confirm
```

### Option 2: Using Task Scheduler (Alternative)

If you prefer not to use NSSM:

1. **Create PowerShell script** (`C:\JobbyBot\run_bot.ps1`):
   ```powershell
   Set-Location "C:\JobbyBot"
   & "C:\Users\YourUsername\AppData\Local\pypoetry\Cache\virtualenvs\jobby-bot-xxxxx-py3.11\Scripts\python.exe" -m jobby_bot.discord_bot
   ```

2. **Open Task Scheduler** (Win + S, search "Task Scheduler")

3. **Create Basic Task**:
   - Name: `Jobby Bot Discord`
   - Trigger: `When the computer starts`
   - Action: `Start a program`
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\JobbyBot\run_bot.ps1"`
   - ✅ Run with highest privileges
   - ✅ Run whether user is logged on or not

4. **Configure additional settings**:
   - Conditions tab: Uncheck "Start only if on AC power"
   - Settings tab:
     - ✅ "Allow task to be run on demand"
     - ✅ "Run task as soon as possible after a scheduled start is missed"
     - "If the task fails, restart every": `1 minute`, up to `3 times`

## Auto-Start on Boot

If using NSSM (Option 1), auto-start is already configured!

Verify:
1. Open Services (`services.msc`)
2. Find "Jobby Bot - Discord Job Assistant"
3. Confirm "Startup Type" is "Automatic"

Test:
```powershell
# Restart your PC and check if service starts
Restart-Computer

# After reboot, check status
nssm status JobbyBot
```

## Network Configuration

### Port Forwarding (Not Required)

Jobby Bot only makes **outbound** connections to:
- Discord API
- Anthropic API
- Job sites (LinkedIn, Indeed, Google)
- Email SMTP server (if configured)
- Notion API (if configured)

**No inbound ports need to be opened.**

### Firewall Configuration

Windows Firewall should allow outbound HTTPS (port 443) by default.

If you have issues, allow Python:
1. Windows Security → Firewall & network protection
2. Advanced settings → Outbound Rules → New Rule
3. Program: `C:\Users\YourUsername\AppData\Local\pypoetry\Cache\virtualenvs\jobby-bot-xxxxx-py3.11\Scripts\python.exe`
4. Allow the connection
5. Apply to all profiles

### Static IP (Recommended)

Set a static local IP for your Windows PC:
1. Settings → Network & Internet → Ethernet/Wi-Fi → Properties
2. IP settings → Edit
3. Manual → IPv4
4. Enter IP: `192.168.1.100` (or any available IP on your network)
5. Subnet: `255.255.255.0`
6. Gateway: Your router IP (usually `192.168.1.1`)
7. DNS: `8.8.8.8`, `8.8.4.4` (Google DNS)

### Keep PC Awake

Prevent sleep mode:
1. Settings → System → Power & sleep
2. When plugged in, PC goes to sleep: **Never**
3. When plugged in, turn off screen: **15 minutes** (or Never)

Advanced power settings:
1. Control Panel → Power Options → Change plan settings
2. Change advanced power settings
3. Hard disk → Turn off hard disk after: **Never**
4. Sleep → Sleep after: **Never**

## Monitoring and Maintenance

### View Service Logs

**NSSM logs**:
```powershell
# View output log
Get-Content C:\JobbyBot\logs\service_output.log -Tail 50 -Wait

# View error log
Get-Content C:\JobbyBot\logs\service_error.log -Tail 50 -Wait
```

**Jobby Bot session logs**:
```powershell
# Navigate to logs directory
cd C:\JobbyBot\logs

# View latest session
Get-ChildItem -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-ChildItem
```

### Monitor Auto Job Checks

Check `user_data\monitor_state.json` to see when the last job check ran:
```powershell
Get-Content C:\JobbyBot\user_data\monitor_state.json | ConvertFrom-Json
```

### Disk Space Management

Create a cleanup script (`C:\JobbyBot\cleanup_logs.ps1`):
```powershell
# Delete session logs older than 30 days
$LogPath = "C:\JobbyBot\logs"
Get-ChildItem $LogPath -Directory | Where-Object {$_.CreationTime -lt (Get-Date).AddDays(-30)} | Remove-Item -Recurse -Force

# Delete old job listings (keep last 100)
$JobsPath = "C:\JobbyBot\output\job_listings"
Get-ChildItem $JobsPath -File | Sort-Object CreationTime -Descending | Select-Object -Skip 100 | Remove-Item -Force
```

Run weekly via Task Scheduler:
1. Create task: `Jobby Bot Cleanup`
2. Trigger: Weekly (Sunday 3 AM)
3. Action: `powershell.exe -File "C:\JobbyBot\cleanup_logs.ps1"`

### Update the Bot

```powershell
# Stop service
nssm stop JobbyBot

# Navigate to project
cd C:\JobbyBot

# Pull latest changes (if using Git)
git pull

# Update dependencies
poetry install

# Restart service
nssm start JobbyBot
```

### Monitor Bot Health

Create a health check script (`C:\JobbyBot\check_health.ps1`):
```powershell
$ServiceName = "JobbyBot"
$Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($Service.Status -ne 'Running') {
    Write-Host "⚠️ Jobby Bot is not running! Attempting to restart..."
    Start-Service $ServiceName
    Start-Sleep -Seconds 5

    if ((Get-Service $ServiceName).Status -eq 'Running') {
        Write-Host "✅ Service restarted successfully"
    } else {
        Write-Host "❌ Failed to restart service - check logs"
        # Optional: Send yourself an email notification
    }
} else {
    Write-Host "✅ Jobby Bot is running healthy"
}
```

Run every hour via Task Scheduler.

## Troubleshooting

### Service Won't Start

1. **Check logs**:
   ```powershell
   Get-Content C:\JobbyBot\logs\service_error.log -Tail 20
   ```

2. **Test manually**:
   ```powershell
   cd C:\JobbyBot
   poetry run python -m jobby_bot.discord_bot
   ```

3. **Verify Python path** in `start_discord_bot.bat`:
   ```powershell
   poetry env info --path
   ```

4. **Check permissions**: Ensure service account has read/write access to `C:\JobbyBot`

### Bot Disconnects Randomly

1. **Check internet connection stability**
2. **Review error logs** for API rate limits
3. **Verify `.env` tokens are valid**
4. **Increase retry settings** in service:
   ```powershell
   nssm set JobbyBot AppExit Default Restart
   nssm set JobbyBot AppRestartDelay 60000  # 60 seconds
   ```

### High CPU/Memory Usage

1. **Check for infinite loops** in logs
2. **Limit concurrent job searches** in `preferences.json`:
   ```json
   {
     "default_search": {
       "results_wanted": 10  // Reduce from 20
     }
   }
   ```
3. **Increase check interval**:
   ```bash
   JOB_CHECK_INTERVAL_MINUTES=60  # Check hourly instead of every 30 min
   ```

### Emails Not Sending

1. **Test SMTP settings**:
   ```powershell
   # Create test script
   poetry run python -c "from jobby_bot.utils.email_sender import send_test_email; send_test_email()"
   ```

2. **Check firewall** allows outbound SMTP (port 587)

3. **Verify app password** (Gmail requires app passwords, not regular password)

4. **Check email logs** in session logs

### Discord Bot Not Responding

1. **Verify bot is online** in Discord server
2. **Check Message Content Intent** is enabled in Discord Developer Portal
3. **Verify token** in `.env` file
4. **Check Discord API status**: https://discordstatus.com/
5. **Review connection logs**:
   ```powershell
   Get-Content C:\JobbyBot\logs\service_output.log | Select-String "Discord"
   ```

### Python Module Not Found

Ensure you're using the correct Poetry virtualenv:
```powershell
# Activate virtualenv
poetry shell

# Or use full path in batch file
poetry env info --path
```

### PC Restarts and Service Doesn't Start

1. **Check Event Viewer**:
   - Windows Logs → System
   - Look for service startup errors

2. **Increase startup delay**:
   ```powershell
   nssm set JobbyBot AppStartDelay 30000  # Wait 30 seconds after boot
   ```

3. **Check dependencies**:
   - Ensure network is up before service starts
   - Service depends on: Network, DNS

## Remote Access (Optional)

### Using TeamViewer

1. Install TeamViewer on Windows PC
2. Set unattended access
3. Access from anywhere to check logs/restart service

### Using Chrome Remote Desktop

1. Install Chrome Remote Desktop: https://remotedesktop.google.com/
2. Set up remote access
3. Connect from any device with Chrome

### Using Windows Remote Desktop (RDP)

If your Windows version supports it:
1. Enable Remote Desktop in Settings
2. Note your PC's IP address
3. Connect using Microsoft Remote Desktop app
4. **Security**: Only allow RDP over VPN or use strong passwords

## Best Practices

1. ✅ **Regular backups**: Backup `user_data/` and `.env` weekly
2. ✅ **Monitor logs**: Check logs weekly for errors
3. ✅ **Update dependencies**: Run `poetry update` monthly
4. ✅ **Test after updates**: Always test manually before restarting service
5. ✅ **Set up email alerts**: Get notified if service fails
6. ✅ **UPS recommended**: Use uninterruptible power supply for 24/7 operation
7. ✅ **Document changes**: Keep notes on configuration changes

## Security Recommendations

1. 🔒 **Strong passwords**: Use unique, strong passwords for all accounts
2. 🔒 **Firewall enabled**: Keep Windows Firewall on
3. 🔒 **Windows updates**: Enable automatic Windows updates
4. 🔒 **Antivirus**: Keep Windows Defender enabled
5. 🔒 **No public access**: Don't expose your home PC to the internet
6. 🔒 **Encrypt credentials**: `.env` file contains sensitive data - keep it secure
7. 🔒 **Regular backups**: Backup important data to external drive or cloud

## Performance Optimization

### For older PCs:

1. **Reduce check frequency**:
   ```bash
   JOB_CHECK_INTERVAL_MINUTES=120  # Every 2 hours
   ```

2. **Limit search results**:
   ```json
   "results_wanted": 5
   ```

3. **Disable unused features**:
   ```bash
   ENABLE_AUTO_JOB_MONITOR=false  # If not needed
   ```

4. **Close unnecessary apps**: Free up RAM for the bot

5. **Disk cleanup**: Run Disk Cleanup regularly

## Cost Considerations

Running 24/7 on a Windows PC:

- **Electricity**: ~50-100W PC = ~$5-10/month (varies by region)
- **API costs**:
  - Auto-monitoring (every 30 min): ~1000 checks/month
  - Estimated cost: $10-20/month (depending on job volume)
- **Total**: ~$15-30/month

To reduce costs:
- Increase `JOB_CHECK_INTERVAL_MINUTES` to 60 or 120
- Reduce `results_wanted` in preferences
- Use energy-efficient PC or laptop

## Support

If you encounter issues:

1. **Check this guide** for troubleshooting steps
2. **Review logs** in `C:\JobbyBot\logs\`
3. **Test manually** outside of service
4. **Check GitHub issues** for similar problems
5. **Ask in Discord** (if you have a support server)

---

**🎉 Congratulations!** Your Jobby Bot is now running 24/7 on your Windows PC, automatically searching for jobs and sending you email updates!
