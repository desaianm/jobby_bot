# Jobby Bot Health Check Script
# Run this periodically to ensure the service is running
# Can be scheduled via Task Scheduler

param(
    [string]$ServiceName = "JobbyBot",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")

    if ($Quiet -and $Level -eq "INFO") {
        return
    }

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }

    Write-Host "[$Timestamp] $Level: $Message" -ForegroundColor $Color
}

# Check if service exists
$Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if (-not $Service) {
    Write-Log "Service '$ServiceName' not found!" "ERROR"
    Write-Log "Install the service first using install_service.ps1" "ERROR"
    exit 1
}

# Check service status
if ($Service.Status -ne 'Running') {
    Write-Log "Service is not running (Status: $($Service.Status))" "ERROR"
    Write-Log "Attempting to start service..." "WARNING"

    try {
        Start-Service $ServiceName -ErrorAction Stop
        Start-Sleep -Seconds 5

        $Service = Get-Service -Name $ServiceName
        if ($Service.Status -eq 'Running') {
            Write-Log "Service started successfully" "SUCCESS"
            exit 0
        } else {
            Write-Log "Failed to start service. Current status: $($Service.Status)" "ERROR"

            # Get project root
            $ProjectRoot = Split-Path -Parent $PSScriptRoot
            $ErrorLog = Join-Path $ProjectRoot "logs\service_error.log"

            if (Test-Path $ErrorLog) {
                Write-Log "Recent errors from log:" "ERROR"
                Get-Content $ErrorLog -Tail 10 | ForEach-Object {
                    Write-Host "  $_" -ForegroundColor Red
                }
            }

            exit 1
        }
    }
    catch {
        Write-Log "Error starting service: $($_.Exception.Message)" "ERROR"
        exit 1
    }
}
else {
    Write-Log "Service is running healthy" "SUCCESS"

    # Optional: Check if Discord bot is actually responsive
    # You could add additional checks here like:
    # - Check if log file is being updated
    # - Ping Discord API
    # - Check last job check time in monitor_state.json

    # Get project root
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
    $MonitorState = Join-Path $ProjectRoot "user_data\monitor_state.json"

    if (Test-Path $MonitorState) {
        try {
            $State = Get-Content $MonitorState -Raw | ConvertFrom-Json
            if ($State.last_check) {
                $LastCheck = [DateTime]::Parse($State.last_check)
                $TimeSinceCheck = (Get-Date) - $LastCheck

                if ($TimeSinceCheck.TotalHours -gt 2) {
                    Write-Log "WARNING: No job check in $([Math]::Round($TimeSinceCheck.TotalHours, 1)) hours" "WARNING"
                } else {
                    Write-Log "Last job check: $([Math]::Round($TimeSinceCheck.TotalMinutes, 0)) minutes ago" "INFO"
                }
            }
        }
        catch {
            # Ignore JSON parse errors
        }
    }

    exit 0
}
