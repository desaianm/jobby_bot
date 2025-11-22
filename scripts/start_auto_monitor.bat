@echo off
REM Jobby Bot Auto Monitor Startup Script for Windows
REM This script starts the standalone auto job monitor

echo ========================================
echo Starting Jobby Bot Auto Job Monitor
echo ========================================
echo.

REM Change to project directory
cd /d "%~dp0\.."

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

REM Check if email is configured
findstr /C:"RECIPIENT_EMAIL=" .env > nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: RECIPIENT_EMAIL not configured in .env
    echo Auto monitor will search for jobs but won't send emails.
    echo.
)

REM Find Python executable in Poetry virtualenv
set PYTHON_PATH=C:\Users\%USERNAME%\AppData\Local\pypoetry\Cache\virtualenvs\jobby-bot-py3.11\Scripts\python.exe

REM If the above doesn't work, try using Poetry directly
if not exist "%PYTHON_PATH%" (
    echo Using Poetry to run the monitor...
    poetry run python -m jobby_bot.auto_job_monitor
) else (
    echo Using virtualenv Python at: %PYTHON_PATH%
    "%PYTHON_PATH%" -m jobby_bot.auto_job_monitor
)

REM If script exits, show error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Monitor exited with error code %ERRORLEVEL%
    echo Check logs in logs\ directory for details.
    pause
)
