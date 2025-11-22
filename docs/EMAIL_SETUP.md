# Email Automation Setup Guide

## Overview

Jobby Bot can automatically send your job applications via email with customized resumes and cover letters attached. This guide covers setup for different email providers.

## Quick Start

1. Add email credentials to `.env`
2. Run `python test_email.py` to verify
3. Start using the bot - emails sent automatically

## Email Providers

### Gmail (Recommended)

**Requirements**:
- Google account with 2FA enabled
- App password generated

**Setup Steps**:

1. **Enable 2-Factor Authentication**
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Jobby Bot"
   - Copy the 16-character password

3. **Add to .env**
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@gmail.com
   SENDER_PASSWORD=abcd efgh ijkl mnop  # 16-char app password
   RECIPIENT_EMAIL=your_email@gmail.com  # Can be same or different
   ```

**Common Issues**:
- ❌ "Authentication failed" → Use app password, not regular password
- ❌ "Less secure apps" error → Enable 2FA and use app password instead

### Outlook/Hotmail

**Setup Steps**:

1. **Add to .env**
   ```bash
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@outlook.com
   SENDER_PASSWORD=your_password
   RECIPIENT_EMAIL=your_email@outlook.com
   ```

2. **Optional: Generate App Password**
   - If you have 2FA enabled, generate app password at:
   - https://account.live.com/proofs/manage/additional

**Common Issues**:
- ❌ Connection refused → Ensure SMTP access is enabled in Outlook settings

### Yahoo Mail

**Setup Steps**:

1. **Generate App Password**
   - Go to: https://login.yahoo.com/myaccount/security
   - Click "Generate app password"
   - Select "Other App" and name it "Jobby Bot"

2. **Add to .env**
   ```bash
   SMTP_SERVER=smtp.mail.yahoo.com
   SMTP_PORT=587
   SENDER_EMAIL=your_email@yahoo.com
   SENDER_PASSWORD=your_app_password
   RECIPIENT_EMAIL=your_email@yahoo.com
   ```

### Custom SMTP Server

**For other providers** (ProtonMail, custom domain, etc.):

1. **Find SMTP Settings**
   - Contact your email provider for:
     - SMTP server address
     - Port number (usually 587 for TLS, 465 for SSL)
     - Authentication requirements

2. **Add to .env**
   ```bash
   SMTP_SERVER=smtp.yourprovider.com
   SMTP_PORT=587
   SENDER_EMAIL=you@yourdomain.com
   SENDER_PASSWORD=your_password
   RECIPIENT_EMAIL=you@yourdomain.com
   ```

## Testing Your Configuration

Run the test script:
```bash
python test_email.py
```

**Expected Output**:
```
==================================================
  JOBBY BOT - Email Configuration Test
==================================================
🔍 Testing Email Configuration...
==================================================

1. Checking environment variables...
✅ All required environment variables are set
   SMTP Server: smtp.gmail.com:587
   Sender: your_email@gmail.com
   Recipient: your_email@gmail.com

2. Initializing email sender...
✅ Email sender initialized successfully

3. Sending test email...
   Created test PDFs in test_email_output/
✅ Test email sent successfully to your_email@gmail.com

==================================================
🎉 Email configuration is working correctly!
```

**Check your inbox** for test email with subject:
```
Job Application: Senior Software Engineer (TEST) at Test Company Inc
```

## Email Features

### Individual Job Emails

Sent for each job application with:
- **Subject**: "Job Application: [Job Title] at [Company]"
- **Content**:
  - Job title, company, location
  - Salary range (if available)
  - Brief job description
  - "Apply Now" button with direct link
- **Attachments**:
  - Customized resume PDF
  - Cover letter PDF

**Example Email**:
```
Subject: Job Application: Senior AI Engineer at Tech Innovations Inc

[HTML formatted email with job details]

📎 Attached:
- job_123_resume.pdf
- job_123_cover_letter.pdf
```

### Summary Email

Sent at the end of session with:
- **Subject**: "Job Application Summary - [Date] ([X] Applications)"
- **Content**:
  - Statistics (jobs found, applications sent, docs created)
  - List of all jobs with match scores
  - Links to each job posting
- **Attachments**:
  - ALL resumes and cover letters as PDFs

**Example Summary**:
```
Subject: Job Application Summary - January 21, 2025 (3 Applications)

📊 Statistics:
- 45 jobs found
- 3 applications sent
- 6 documents created

📋 Applications:
1. Senior AI Engineer at Tech Innovations Inc (Match: 92%)
2. ML Engineer at AI Startup Co (Match: 88%)
3. Data Scientist at Analytics Corp (Match: 85%)

📎 Attached: 6 PDFs (all resumes and cover letters)
```

## Troubleshooting

### Authentication Errors

**Error**: "Authentication failed" or "Username and Password not accepted"

**Solutions**:
1. ✅ Use app password for Gmail (not regular password)
2. ✅ Check email and password are correct (no typos)
3. ✅ Ensure 2FA is enabled if using Gmail
4. ✅ Verify SMTP settings match your provider

### Connection Errors

**Error**: "Connection refused" or "Timeout"

**Solutions**:
1. ✅ Check SMTP_SERVER and SMTP_PORT are correct
2. ✅ Verify firewall allows outbound connections on port 587/465
3. ✅ Try alternate port (587 vs 465)
4. ✅ Check internet connectivity

### Email Not Received

**Solutions**:
1. ✅ Check spam/junk folder
2. ✅ Wait 1-2 minutes (some providers delay delivery)
3. ✅ Verify RECIPIENT_EMAIL is correct
4. ✅ Check sent folder of SENDER_EMAIL account

### SSL/TLS Errors

**Error**: "SSL: CERTIFICATE_VERIFY_FAILED"

**Solutions**:
1. ✅ Use port 587 with TLS (most compatible)
2. ✅ Update Python SSL certificates
3. ✅ Check system date/time is correct

## Environment Variable Reference

### Required Variables
```bash
SMTP_SERVER=smtp.gmail.com      # SMTP server address
SMTP_PORT=587                    # Port (587=TLS, 465=SSL, 25=plain)
SENDER_EMAIL=from@email.com     # Email to send from
SENDER_PASSWORD=app_password     # Password or app password
RECIPIENT_EMAIL=to@email.com    # Where to receive emails
```

### Common SMTP Servers
```bash
# Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Outlook/Hotmail
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587

# Yahoo
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587

# iCloud
SMTP_SERVER=smtp.mail.me.com
SMTP_PORT=587
```

## Security Best Practices

1. **Use App Passwords**
   - Never use your main account password
   - Generate app-specific passwords when available

2. **Environment Variables**
   - Never commit `.env` to version control
   - `.env` is already in `.gitignore`

3. **Email Permissions**
   - Use dedicated email for job hunting
   - Consider separate email from personal account

4. **Test Safely**
   - Test with your own email first
   - Verify emails look correct before full run

## Disabling Email

To disable email automation:
1. Remove email variables from `.env`, OR
2. Comment them out with `#`

The bot will skip email steps automatically if not configured.

## Support

If issues persist:
1. Check logs in `logs/session_*/transcript.txt`
2. Review email provider's SMTP documentation
3. Verify account security settings
4. Try different port (587 vs 465)
