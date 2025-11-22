# Jobby Bot Log Cleanup Script
# Cleans up old logs and output files to save disk space
# Run periodically via Task Scheduler (e.g., weekly)

param(
    [int]$DaysToKeep = 30,
    [int]$JobListingsToKeep = 100,
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")

    if ($Quiet -and $Level -eq "INFO") {
        return
    }

    $Color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "Cyan" }
    }

    Write-Host $Message -ForegroundColor $Color
}

# Get project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogsPath = Join-Path $ProjectRoot "logs"
$OutputPath = Join-Path $ProjectRoot "output"

Write-Log "`n========================================" "SUCCESS"
Write-Log "Jobby Bot Cleanup Script" "SUCCESS"
Write-Log "========================================`n" "SUCCESS"

if ($DryRun) {
    Write-Log "DRY RUN MODE - No files will be deleted" "WARNING"
}

# Calculate cutoff date
$CutoffDate = (Get-Date).AddDays(-$DaysToKeep)
Write-Log "Cleaning up files older than $DaysToKeep days (before $($CutoffDate.ToString('yyyy-MM-dd')))" "INFO"

# Clean up session logs
Write-Log "`n--- Cleaning Session Logs ---" "SUCCESS"
if (Test-Path $LogsPath) {
    $OldSessions = Get-ChildItem $LogsPath -Directory | Where-Object {
        $_.Name -match '^session_\d{8}_\d{6}$' -and $_.CreationTime -lt $CutoffDate
    }

    if ($OldSessions.Count -gt 0) {
        Write-Log "Found $($OldSessions.Count) old session(s) to delete" "INFO"

        foreach ($Session in $OldSessions) {
            $Size = (Get-ChildItem $Session.FullName -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
            Write-Log "  - $($Session.Name) ($([Math]::Round($Size, 2)) MB)" "INFO"

            if (-not $DryRun) {
                Remove-Item $Session.FullName -Recurse -Force
            }
        }

        if (-not $DryRun) {
            Write-Log "✓ Deleted $($OldSessions.Count) old session log(s)" "SUCCESS"
        }
    } else {
        Write-Log "No old session logs to delete" "INFO"
    }
} else {
    Write-Log "Logs directory not found: $LogsPath" "WARNING"
}

# Clean up service logs (keep last 10MB only)
Write-Log "`n--- Cleaning Service Logs ---" "SUCCESS"
$ServiceOutputLog = Join-Path $LogsPath "service_output.log"
$ServiceErrorLog = Join-Path $LogsPath "service_error.log"

foreach ($LogFile in @($ServiceOutputLog, $ServiceErrorLog)) {
    if (Test-Path $LogFile) {
        $Size = (Get-Item $LogFile).Length / 1MB
        if ($Size -gt 10) {
            Write-Log "Service log is large ($([Math]::Round($Size, 2)) MB): $($LogFile | Split-Path -Leaf)" "WARNING"
            Write-Log "  Keeping last 1000 lines..." "INFO"

            if (-not $DryRun) {
                $LastLines = Get-Content $LogFile -Tail 1000
                Set-Content -Path $LogFile -Value $LastLines
                Write-Log "✓ Trimmed log file" "SUCCESS"
            }
        }
    }
}

# Clean up old job listings
Write-Log "`n--- Cleaning Job Listings ---" "SUCCESS"
$JobListingsPath = Join-Path $OutputPath "job_listings"

if (Test-Path $JobListingsPath) {
    $AllJobFiles = Get-ChildItem $JobListingsPath -File | Sort-Object CreationTime -Descending
    $FilesToDelete = $AllJobFiles | Select-Object -Skip $JobListingsToKeep

    if ($FilesToDelete.Count -gt 0) {
        Write-Log "Found $($FilesToDelete.Count) old job listing file(s) (keeping newest $JobListingsToKeep)" "INFO"

        $TotalSize = ($FilesToDelete | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Log "  Total size: $([Math]::Round($TotalSize, 2)) MB" "INFO"

        if (-not $DryRun) {
            $FilesToDelete | Remove-Item -Force
            Write-Log "✓ Deleted $($FilesToDelete.Count) old job listing file(s)" "SUCCESS"
        }
    } else {
        Write-Log "No old job listings to delete" "INFO"
    }
} else {
    Write-Log "Job listings directory not found: $JobListingsPath" "WARNING"
}

# Clean up old resumes
Write-Log "`n--- Cleaning Old Resumes ---" "SUCCESS"
$ResumesPath = Join-Path $OutputPath "resumes"

if (Test-Path $ResumesPath) {
    $OldResumes = Get-ChildItem $ResumesPath -File | Where-Object {
        $_.CreationTime -lt $CutoffDate
    }

    if ($OldResumes.Count -gt 0) {
        $TotalSize = ($OldResumes | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Log "Found $($OldResumes.Count) old resume file(s) ($([Math]::Round($TotalSize, 2)) MB)" "INFO"

        if (-not $DryRun) {
            $OldResumes | Remove-Item -Force
            Write-Log "✓ Deleted $($OldResumes.Count) old resume file(s)" "SUCCESS"
        }
    } else {
        Write-Log "No old resumes to delete" "INFO"
    }
}

# Clean up old cover letters
Write-Log "`n--- Cleaning Old Cover Letters ---" "SUCCESS"
$CoverLettersPath = Join-Path $OutputPath "cover_letters"

if (Test-Path $CoverLettersPath) {
    $OldCoverLetters = Get-ChildItem $CoverLettersPath -File | Where-Object {
        $_.CreationTime -lt $CutoffDate
    }

    if ($OldCoverLetters.Count -gt 0) {
        $TotalSize = ($OldCoverLetters | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Log "Found $($OldCoverLetters.Count) old cover letter file(s) ($([Math]::Round($TotalSize, 2)) MB)" "INFO"

        if (-not $DryRun) {
            $OldCoverLetters | Remove-Item -Force
            Write-Log "✓ Deleted $($OldCoverLetters.Count) old cover letter file(s)" "SUCCESS"
        }
    } else {
        Write-Log "No old cover letters to delete" "INFO"
    }
}

# Summary
Write-Log "`n========================================" "SUCCESS"
if ($DryRun) {
    Write-Log "DRY RUN COMPLETE - No files were deleted" "WARNING"
    Write-Log "Run without -DryRun to actually delete files" "WARNING"
} else {
    Write-Log "Cleanup Complete!" "SUCCESS"
}
Write-Log "========================================`n" "SUCCESS"

# Show disk usage
$TotalSize = (Get-ChildItem $ProjectRoot -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Log "Total project size: $([Math]::Round($TotalSize, 2)) GB" "INFO"
