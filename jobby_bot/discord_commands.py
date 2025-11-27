"""Discord slash commands for Jobby Bot."""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional
import discord
from discord import app_commands

from jobby_bot.database import (
    get_or_create_user,
    get_user_resume,
    save_user_resume,
    get_user_preferences,
    save_user_preferences,
    get_user_email,
    set_user_email,
    is_auto_monitor_enabled,
    set_auto_monitor_enabled,
)


@app_commands.command(name="help", description="Show detailed help information")
async def help_command(interaction: discord.Interaction):
    """Show detailed help information."""
    help_text = """
📚 **Jobby Bot Help**

**What I can do:**
• Find jobs matching your criteria
• Generate ATS-optimized resumes
• Write personalized cover letters
• Track applications in Notion
• Manage your resume and preferences directly from Discord

**Setup Commands:**
• `/upload-resume` - Upload your resume (PDF or TXT)
• `/set-preferences` - Update job search settings
• `/show-resume` - View your current resume summary
• `/show-preferences` - View your current settings
• `/set-email` - Set your email for job notifications
• `/enable-auto-monitor` - Enable automatic job monitoring
• `/disable-auto-monitor` - Disable automatic job monitoring

**Example preference updates:**
Use `/set-preferences` and provide settings like:
• `location: Seattle, WA`
• `remote: true`
• `search_term: Data Scientist`
• `min_salary: 120000`

**Example job search requests:**
Just message or mention the bot:
• "Find me software engineer jobs in San Francisco"
• "Search for 10 remote Python developer positions"
• "Find data analyst jobs posted in the last 24 hours"

**Session Commands:**
• `/start` - Show welcome message
• `/end` - End your current session
• `/help` - Show this help

**Tips:**
• Upload your resume first using `/upload-resume`
• Configure preferences with `/set-preferences`
• Set your email with `/set-email` to receive job alerts
• Be specific about job criteria (location, role, experience level)
• Sessions persist until you use `/end`
"""
    await interaction.response.send_message(help_text, ephemeral=True)


@app_commands.command(name="end", description="End your current Jobby Bot session")
async def end_command(interaction: discord.Interaction):
    """End the current session for the user."""
    bot = interaction.client
    user_id = interaction.user.id

    if user_id in bot.sessions:
        session = bot.sessions[user_id]
        session_dir = getattr(session, 'session_dir', None)
        await session.cleanup()
        del bot.sessions[user_id]
        msg = "👋 **Session Ended!**\n"
        if session_dir:
            msg += f"📁 Your session logs: `{session_dir}`"
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        await interaction.response.send_message(
            "⚠️ No active session found. Use `/start` to begin!",
            ephemeral=True
        )


@app_commands.command(name="upload-resume", description="Upload your resume file (PDF or TXT)")
async def upload_resume_command(
    interaction: discord.Interaction,
    file: discord.Attachment
):
    """Upload a resume file (PDF or text) to set as your base resume."""
    # Check file type
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        await interaction.response.send_message(
            "❌ Unsupported file type. Please upload a PDF or TXT file.",
            ephemeral=True
        )
        return

    # Check file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        await interaction.response.send_message(
            "❌ File too large. Maximum size is 10MB.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        # Download attachment to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            await file.save(tmp.name)
            tmp_path = tmp.name

        # Get session and process
        bot = interaction.client
        session = await bot.get_or_create_session(interaction.user.id)

        # Ensure user exists in DB
        get_or_create_user(interaction.user.id, str(interaction.user))

        # If PDF, use the conversion script; if TXT, process directly
        # The agent will parse and we'll intercept the save to store in DB
        if file.filename.endswith('.pdf'):
            message = f"I've received a PDF resume. Please extract the text and convert it to JSON Resume format. Return the JSON object. The PDF is at: {tmp_path}"
        else:
            message = f"I've received a text resume. Please parse it and convert it to JSON Resume format. Return the JSON object. The text file is at: {tmp_path}"

        # Process through config agent
        response = await session.process_message(message)

        # Try to extract JSON from response and save to DB
        try:
            # Look for JSON in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                resume_dict = json.loads(json_match.group())
                save_user_resume(interaction.user.id, resume_dict, str(interaction.user))
        except (json.JSONDecodeError, AttributeError):
            pass  # If we can't parse JSON, agent may have saved to file

        # Clean up temp file
        os.unlink(tmp_path)

        await interaction.followup.send(
            f"✅ **Resume Uploaded Successfully!**\n\n"
            f"{response[:1500]}\n\n"
            f"Your resume has been saved and will be used for all job applications.\n"
            f"Use `/show-resume` to view it.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Error processing resume: {str(e)}",
            ephemeral=True
        )
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app_commands.command(name="set-preferences", description="Update your job search preferences")
async def set_preferences_command(
    interaction: discord.Interaction,
    setting: str
):
    """Update job search preferences."""
    await interaction.response.defer(ephemeral=True)

    try:
        bot = interaction.client
        session = await bot.get_or_create_session(interaction.user.id)

        # Ensure user exists
        get_or_create_user(interaction.user.id, str(interaction.user))

        # Get current preferences from DB or start fresh
        current_prefs = get_user_preferences(interaction.user.id) or {}

        message = f"Update my job search preferences: {setting}. Current preferences: {json.dumps(current_prefs)}"
        response = await session.process_message(message)

        # Try to extract updated preferences from response
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                updated_prefs = json.loads(json_match.group())
                save_user_preferences(interaction.user.id, updated_prefs, str(interaction.user))
        except (json.JSONDecodeError, AttributeError):
            pass

        await interaction.followup.send(
            f"✅ **Preferences Updated!**\n\n{response[:1500]}",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Error updating preferences: {str(e)}",
            ephemeral=True
        )


@app_commands.command(name="show-preferences", description="View your current job search preferences")
async def show_preferences_command(interaction: discord.Interaction):
    """View current job search preferences."""
    try:
        prefs = get_user_preferences(interaction.user.id)

        if not prefs:
            await interaction.response.send_message(
                "⚠️ No preferences found. Use `/set-preferences` to configure.",
                ephemeral=True
            )
            return

        default_search = prefs.get('default_search', {})
        filters = prefs.get('filters', {})
        blacklist = prefs.get('blacklist', {})

        # Get email and auto-monitor status
        email = get_user_email(interaction.user.id)
        auto_monitor = is_auto_monitor_enabled(interaction.user.id)

        response = "⚙️ **Current Preferences**\n\n"

        # Account settings
        response += "**Account Settings:**\n"
        response += f"• Email: `{email or 'Not set'}`\n"
        response += f"• Auto Monitor: `{'Enabled' if auto_monitor else 'Disabled'}`\n\n"

        response += "**Search Settings:**\n"
        response += f"• Job Title: `{default_search.get('search_term', 'Not set')}`\n"
        response += f"• Location: `{default_search.get('location', 'Not set')}`\n"
        response += f"• Remote: `{default_search.get('is_remote', False)}`\n"
        response += f"• Results: `{default_search.get('results_wanted', 20)}`\n"
        response += f"• Posted within: `{default_search.get('hours_old', 72)} hours`\n\n"

        if filters.get('min_salary'):
            response += f"**Filters:**\n"
            response += f"• Minimum Salary: `${filters['min_salary']:,}`\n\n"

        if blacklist.get('companies'):
            response += f"**Blacklisted Companies:** {len(blacklist['companies'])}\n"
            for company in blacklist['companies'][:5]:
                response += f"  • {company}\n"
            if len(blacklist['companies']) > 5:
                response += f"  ... and {len(blacklist['companies']) - 5} more\n"
            response += "\n"

        if filters.get('preferred_tech_stack'):
            tech_list = filters['preferred_tech_stack'][:10]
            response += f"**Preferred Tech:** {', '.join(tech_list)}"
            if len(filters['preferred_tech_stack']) > 10:
                response += f" + {len(filters['preferred_tech_stack']) - 10} more"

        await interaction.response.send_message(response, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error reading preferences: {str(e)}",
            ephemeral=True
        )


@app_commands.command(name="show-resume", description="View your current resume summary")
async def show_resume_command(interaction: discord.Interaction):
    """View your current base resume summary."""
    try:
        resume = get_user_resume(interaction.user.id)

        if not resume:
            await interaction.response.send_message(
                "⚠️ **No Resume Found**\n\n"
                "Upload your resume using `/upload-resume`",
                ephemeral=True
            )
            return

        basics = resume.get('basics', {})
        work = resume.get('work', [])
        education = resume.get('education', [])
        skills = resume.get('skills', [])

        response = "📄 **Your Resume**\n\n"
        response += f"**Name:** {basics.get('name', 'Not set')}\n"
        response += f"**Email:** {basics.get('email', 'Not set')}\n"
        if basics.get('phone'):
            response += f"**Phone:** {basics['phone']}\n"
        if basics.get('location', {}).get('city'):
            loc = basics['location']
            response += f"**Location:** {loc.get('city', '')}, {loc.get('region', '')}\n"

        response += f"\n**Work Experience:** {len(work)} position(s)\n"
        for i, job in enumerate(work[:3], 1):
            response += f"{i}. {job.get('position', 'Unknown')} at {job.get('company', job.get('name', 'Unknown'))}\n"
        if len(work) > 3:
            response += f"   ... and {len(work) - 3} more\n"

        response += f"\n**Education:** {len(education)} degree(s)\n"
        for edu in education[:2]:
            response += f"• {edu.get('studyType', '')} in {edu.get('area', '')} from {edu.get('institution', '')}\n"

        if skills:
            all_skills = []
            for skill_group in skills:
                all_skills.extend(skill_group.get('keywords', []))
            response += f"\n**Skills:** {', '.join(all_skills[:15])}"
            if len(all_skills) > 15:
                response += f" + {len(all_skills) - 15} more"

        await interaction.response.send_message(response, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error reading resume: {str(e)}",
            ephemeral=True
        )


@app_commands.command(name="set-email", description="Set your email for job notifications")
async def set_email_command(
    interaction: discord.Interaction,
    email: str
):
    """Set the user's email for job notifications."""
    # Basic email validation
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        await interaction.response.send_message(
            "❌ Invalid email format. Please provide a valid email address.",
            ephemeral=True
        )
        return

    try:
        get_or_create_user(interaction.user.id, str(interaction.user))
        set_user_email(interaction.user.id, email, str(interaction.user))

        await interaction.response.send_message(
            f"✅ **Email Set!**\n\n"
            f"Your email has been set to: `{email}`\n\n"
            f"You will receive job notifications at this address when auto-monitor is enabled.\n"
            f"Use `/enable-auto-monitor` to start receiving automatic job alerts.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error setting email: {str(e)}",
            ephemeral=True
        )


@app_commands.command(name="enable-auto-monitor", description="Enable automatic job monitoring")
async def enable_auto_monitor_command(interaction: discord.Interaction):
    """Enable automatic job monitoring for the user."""
    try:
        # Check if user has email set
        email = get_user_email(interaction.user.id)
        if not email:
            await interaction.response.send_message(
                "⚠️ **Email Required**\n\n"
                "You need to set your email first using `/set-email` before enabling auto-monitor.",
                ephemeral=True
            )
            return

        # Check if user has preferences set
        prefs = get_user_preferences(interaction.user.id)
        if not prefs or not prefs.get('default_search', {}).get('search_term'):
            await interaction.response.send_message(
                "⚠️ **Preferences Required**\n\n"
                "You need to set your job search preferences using `/set-preferences` before enabling auto-monitor.\n"
                "At minimum, set a `search_term` like: `/set-preferences search_term: Software Engineer`",
                ephemeral=True
            )
            return

        get_or_create_user(interaction.user.id, str(interaction.user))
        set_auto_monitor_enabled(interaction.user.id, True, str(interaction.user))

        await interaction.response.send_message(
            f"✅ **Auto-Monitor Enabled!**\n\n"
            f"You will now receive automatic job alerts at: `{email}`\n\n"
            f"The bot will search for jobs matching your preferences and send you notifications.\n"
            f"Use `/disable-auto-monitor` to stop receiving alerts.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error enabling auto-monitor: {str(e)}",
            ephemeral=True
        )


@app_commands.command(name="disable-auto-monitor", description="Disable automatic job monitoring")
async def disable_auto_monitor_command(interaction: discord.Interaction):
    """Disable automatic job monitoring for the user."""
    try:
        get_or_create_user(interaction.user.id, str(interaction.user))
        set_auto_monitor_enabled(interaction.user.id, False, str(interaction.user))

        await interaction.response.send_message(
            "✅ **Auto-Monitor Disabled!**\n\n"
            "You will no longer receive automatic job alerts.\n"
            "Use `/enable-auto-monitor` to re-enable.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error disabling auto-monitor: {str(e)}",
            ephemeral=True
        )
