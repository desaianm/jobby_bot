"""Discord slash commands for Jobby Bot."""

import os
import json
import tempfile
from pathlib import Path
from typing import Optional
import discord
from discord import app_commands

# Paths
USER_DATA_DIR = Path(__file__).parent.parent / "user_data"


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
        session_dir = session.session_dir
        await session.cleanup()
        del bot.sessions[user_id]
        await interaction.response.send_message(
            f"👋 **Session Ended!**\n"
            f"📁 Your session logs: `{session_dir}`",
            ephemeral=True
        )
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

        # If PDF, use the conversion script; if TXT, process directly
        if file.filename.endswith('.pdf'):
            message = f"I've received a PDF resume. Please extract the text and convert it to JSON Resume format, saving it to user_data/base_resume.json. The PDF is at: {tmp_path}"
        else:
            message = f"I've received a text resume. Please parse it and convert it to JSON Resume format, saving it to user_data/base_resume.json. The text file is at: {tmp_path}"

        # Process through config agent
        response = await session.process_message(message)

        # Clean up temp file
        os.unlink(tmp_path)

        await interaction.followup.send(
            f"✅ **Resume Uploaded Successfully!**\n\n"
            f"{response}\n\n"
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

        message = f"Update my job search preferences: {setting}"
        response = await session.process_message(message)

        await interaction.followup.send(
            f"✅ **Preferences Updated!**\n\n{response}",
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
        prefs_file = USER_DATA_DIR / "preferences.json"
        if not prefs_file.exists():
            await interaction.response.send_message(
                "⚠️ No preferences file found. Use `/set-preferences` to configure.",
                ephemeral=True
            )
            return

        with open(prefs_file, 'r') as f:
            prefs = json.load(f)

        default_search = prefs.get('default_search', {})
        filters = prefs.get('filters', {})
        blacklist = prefs.get('blacklist', {})

        response = "⚙️ **Current Preferences**\n\n"
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
        resume_file = USER_DATA_DIR / "base_resume.json"
        if not resume_file.exists():
            await interaction.response.send_message(
                "⚠️ **No Resume Found**\n\n"
                "Upload your resume using `/upload-resume`\n"
                "Or manually create `user_data/base_resume.json`",
                ephemeral=True
            )
            return

        with open(resume_file, 'r') as f:
            resume = json.load(f)

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
            response += f"{i}. {job.get('position', 'Unknown')} at {job.get('company', 'Unknown')}\n"
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
