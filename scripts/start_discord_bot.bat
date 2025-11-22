@echo off
REM Jobby Bot Discord Startup Script for Windows
REM This script starts the Discord bot with auto-monitoring

echo ========================================
echo Starting Jobby Bot Discord Integration
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

REM Find Python executable in Poetry virtualenv
REM You need to replace this path with your actual virtualenv path
REM Run 'poetry env info --path' to find it
set PYTHON_PATH=C:\Users\%USERNAME%\AppData\Local\pypoetry\Cache\virtualenvs\jobby-bot-py3.11\Scripts\python.exe

REM If the above doesn't work, try using Poetry directly
if not exist "%PYTHON_PATH%" (
    echo Using Poetry to run the bot...
    poetry run python -m jobby_bot.discord_bot
) else (
    echo Using virtualenv Python at: %PYTHON_PATH%
    "%PYTHON_PATH%" -m jobby_bot.discord_bot
)

REM If script exits, show error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Bot exited with error code %ERRORLEVEL%
    echo Check logs in logs\ directory for details.
    pause
)
