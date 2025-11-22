# Jobby Bot - Windows Service Installation Script
# This script installs Jobby Bot as a Windows service using NSSM
# Run as Administrator: powershell -ExecutionPolicy Bypass -File install_service.ps1

param(
    [string]$ServiceName = "JobbyBot",
    [string]$NssmPath = "C:\nssm\win64\nssm.exe",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Jobby Bot Windows Service Installation Script

USAGE:
    powershell -ExecutionPolicy Bypass -File install_service.ps1 [OPTIONS]

OPTIONS:
    -ServiceName <name>    Service name (default: JobbyBot)
    -NssmPath <path>       Path to nssm.exe (default: C:\nssm\win64\nssm.exe)
    -Help                  Show this help message

EXAMPLES:
    # Install with defaults
    powershell -ExecutionPolicy Bypass -File install_service.ps1

    # Install with custom service name
    powershell -ExecutionPolicy Bypass -File install_service.ps1 -ServiceName "MyJobBot"

REQUIREMENTS:
    - Run as Administrator
    - NSSM installed (download from https://nssm.cc/)
    - Jobby Bot already configured (.env file exists)

"@
    exit 0
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host @"
========================================
Jobby Bot Service Installation
========================================

"@ -ForegroundColor Cyan

# Get project root (script is in scripts/ folder)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray

# Check if .env exists
$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "ERROR: .env file not found at $EnvFile" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and configure it first." -ForegroundColor Yellow
    exit 1
}

# Check if NSSM exists
if (-not (Test-Path $NssmPath)) {
    Write-Host "ERROR: NSSM not found at $NssmPath" -ForegroundColor Red
    Write-Host @"

NSSM (Non-Sucking Service Manager) is required to install the service.

To install NSSM:
1. Download from https://nssm.cc/download
2. Extract to C:\nssm\
3. Run this script again

Alternatively, specify a custom path:
    -NssmPath "C:\path\to\nssm.exe"

"@ -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ NSSM found at $NssmPath" -ForegroundColor Green

# Get Poetry virtualenv path
Write-Host "Finding Poetry virtualenv..." -ForegroundColor Gray
Set-Location $ProjectRoot
$VenvPath = poetry env info --path 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Could not find Poetry virtualenv" -ForegroundColor Red
    Write-Host "Make sure Poetry is installed and you've run 'poetry install'" -ForegroundColor Yellow
    exit 1
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python executable not found at $PythonExe" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python found at $PythonExe" -ForegroundColor Green

# Check if service already exists
$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($ExistingService) {
    Write-Host "WARNING: Service '$ServiceName' already exists!" -ForegroundColor Yellow
    $response = Read-Host "Do you want to remove and reinstall? (y/n)"
    if ($response -eq 'y') {
        Write-Host "Stopping and removing existing service..." -ForegroundColor Gray
        & $NssmPath stop $ServiceName
        & $NssmPath remove $ServiceName confirm
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Create logs directory
$LogsDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
    Write-Host "✓ Created logs directory" -ForegroundColor Green
}

# Create startup batch file
$BatchFile = Join-Path $ProjectRoot "scripts\start_discord_bot_service.bat"
$BatchContent = @"
@echo off
cd /d "$ProjectRoot"
"$PythonExe" -m jobby_bot.discord_bot
"@
Set-Content -Path $BatchFile -Value $BatchContent -Encoding ASCII
Write-Host "✓ Created startup batch file" -ForegroundColor Green

# Install service
Write-Host "`nInstalling service..." -ForegroundColor Cyan
& $NssmPath install $ServiceName $BatchFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install service" -ForegroundColor Red
    exit 1
}

# Configure service
Write-Host "Configuring service..." -ForegroundColor Cyan

& $NssmPath set $ServiceName AppDirectory $ProjectRoot
& $NssmPath set $ServiceName DisplayName "Jobby Bot - Discord Job Assistant"
& $NssmPath set $ServiceName Description "Automated job search and application bot with Discord interface and auto-monitoring"
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

# Set up logging
$OutputLog = Join-Path $LogsDir "service_output.log"
$ErrorLog = Join-Path $LogsDir "service_error.log"
& $NssmPath set $ServiceName AppStdout $OutputLog
& $NssmPath set $ServiceName AppStderr $ErrorLog
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateBytes 10485760  # 10MB

# Set restart on failure
& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppRestartDelay 60000  # 60 seconds

Write-Host "✓ Service configured" -ForegroundColor Green

# Ask to start service now
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Service installed successfully!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

$startNow = Read-Host "Start the service now? (y/n)"
if ($startNow -eq 'y') {
    Write-Host "Starting service..." -ForegroundColor Gray
    & $NssmPath start $ServiceName
    Start-Sleep -Seconds 3

    $status = & $NssmPath status $ServiceName
    if ($status -eq "SERVICE_RUNNING") {
        Write-Host "✓ Service is running!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Service status: $status" -ForegroundColor Yellow
        Write-Host "Check logs at: $ErrorLog" -ForegroundColor Gray
    }
}

Write-Host @"

NEXT STEPS:
1. Check service status: nssm status $ServiceName
2. View logs: Get-Content $OutputLog -Tail 50 -Wait
3. Stop service: nssm stop $ServiceName
4. Restart service: nssm restart $ServiceName

The service will automatically start when Windows boots.

"@ -ForegroundColor Cyan

Write-Host "Installation complete! 🎉`n" -ForegroundColor Green
