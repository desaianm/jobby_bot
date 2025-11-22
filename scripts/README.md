# Scripts Directory

This directory contains utility scripts for running and managing Jobby Bot on Windows.

## Windows Batch Scripts

### start_discord_bot.bat
Starts the Discord bot with auto-monitoring enabled.

**Usage:**
```cmd
scripts\start_discord_bot.bat
```

**Requirements:**
- .env file configured
- Poetry virtualenv installed

### start_auto_monitor.bat
Starts the standalone auto job monitor (without Discord interface).

**Usage:**
```cmd
scripts\start_auto_monitor.bat
```

## PowerShell Scripts

### install_service.ps1
Installs Jobby Bot as a Windows service using NSSM (Non-Sucking Service Manager).

**Usage:**
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File scripts\install_service.ps1
```

**Options:**
- `-ServiceName <name>` - Custom service name (default: JobbyBot)
- `-NssmPath <path>` - Path to nssm.exe (default: C:\nssm\win64\nssm.exe)
- `-Help` - Show help message

**Requirements:**
- Run as Administrator
- NSSM installed (download from https://nssm.cc/)
- .env file configured

**Example:**
```powershell
# Install with custom service name
powershell -ExecutionPolicy Bypass -File scripts\install_service.ps1 -ServiceName "MyJobBot"
```

### check_health.ps1
Health check script to monitor service status and automatically restart if needed.

**Usage:**
```powershell
# Manual check
powershell -ExecutionPolicy Bypass -File scripts\check_health.ps1

# Quiet mode (minimal output)
powershell -ExecutionPolicy Bypass -File scripts\check_health.ps1 -Quiet
```

**Scheduling:**
Run this every hour via Task Scheduler to ensure the bot stays running:
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Jobby Bot Health Check"
4. Trigger: Hourly
5. Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\JobbyBot\scripts\check_health.ps1" -Quiet`

### cleanup_logs.ps1
Cleans up old logs and output files to save disk space.

**Usage:**
```powershell
# Preview what will be deleted (dry run)
powershell -ExecutionPolicy Bypass -File scripts\cleanup_logs.ps1 -DryRun

# Clean up files older than 30 days
powershell -ExecutionPolicy Bypass -File scripts\cleanup_logs.ps1

# Clean up files older than 7 days
powershell -ExecutionPolicy Bypass -File scripts\cleanup_logs.ps1 -DaysToKeep 7

# Keep only last 50 job listings
powershell -ExecutionPolicy Bypass -File scripts\cleanup_logs.ps1 -JobListingsToKeep 50
```

**Options:**
- `-DaysToKeep <days>` - Delete files older than N days (default: 30)
- `-JobListingsToKeep <count>` - Number of job listing files to keep (default: 100)
- `-DryRun` - Preview without deleting
- `-Quiet` - Minimal output

**Scheduling:**
Run weekly via Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Jobby Bot Cleanup"
4. Trigger: Weekly (Sunday 3 AM)
5. Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\JobbyBot\scripts\cleanup_logs.ps1"`

## Quick Start

### First Time Setup

1. **Install Python, Poetry, and NSSM** (see [WINDOWS_HOSTING.md](../WINDOWS_HOSTING.md))

2. **Configure the bot**:
   ```cmd
   cd C:\JobbyBot
   copy .env.example .env
   notepad .env
   ```

3. **Test manually**:
   ```cmd
   scripts\start_discord_bot.bat
   ```
   Press Ctrl+C to stop after confirming it works.

4. **Install as service** (Run PowerShell as Administrator):
   ```powershell
   cd C:\JobbyBot
   powershell -ExecutionPolicy Bypass -File scripts\install_service.ps1
   ```

5. **Set up monitoring**:
   - Schedule `check_health.ps1` to run every hour
   - Schedule `cleanup_logs.ps1` to run weekly

### Service Management

```powershell
# Check status
nssm status JobbyBot

# Start service
nssm start JobbyBot

# Stop service
nssm stop JobbyBot

# Restart service
nssm restart JobbyBot

# View logs
Get-Content C:\JobbyBot\logs\service_output.log -Tail 50 -Wait
```

## Troubleshooting

### "Cannot be loaded because running scripts is disabled"

Run this in PowerShell as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Service won't start

1. Check error log:
   ```powershell
   Get-Content C:\JobbyBot\logs\service_error.log -Tail 20
   ```

2. Test manually:
   ```cmd
   scripts\start_discord_bot.bat
   ```

3. Verify Python path in batch file matches your virtualenv

### Script can't find Poetry virtualenv

Find your virtualenv path:
```powershell
cd C:\JobbyBot
poetry env info --path
```

Update the path in the batch files.

## Additional Resources

- [WINDOWS_HOSTING.md](../WINDOWS_HOSTING.md) - Complete hosting guide
- [DISCORD_SETUP.md](../DISCORD_SETUP.md) - Discord bot setup
- [README.md](../README.md) - Main documentation
