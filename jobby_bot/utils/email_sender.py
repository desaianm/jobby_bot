"""Email utility for sending job application materials via SMTP."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class EmailSender:
    """Handle email sending via SMTP with attachment support."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        use_tls: bool = True
    ):
        """
        Initialize email sender with SMTP credentials.

        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (usually 587 for TLS, 465 for SSL)
            sender_email: Your email address
            sender_password: Your email password or app password
            use_tls: Whether to use TLS encryption (recommended)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls

    def send_individual_job_email(
        self,
        recipient_email: str,
        job_data: Dict,
        resume_path: Optional[str] = None,
        cover_letter_path: Optional[str] = None
    ) -> bool:
        """
        Send individual email for a single job application.

        Args:
            recipient_email: Recipient's email address
            job_data: Dictionary containing job information
            resume_path: Path to resume PDF
            cover_letter_path: Path to cover letter PDF

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Job Application: {job_data.get('title', 'N/A')} at {job_data.get('company', 'N/A')}"

        # Create email body
        body = self._create_individual_email_body(job_data)

        # Send email with attachments
        return self._send_email(
            recipient_email,
            subject,
            body,
            attachments=[resume_path, cover_letter_path]
        )

    def send_summary_email(
        self,
        recipient_email: str,
        jobs_data: List[Dict],
        total_jobs_found: int
    ) -> bool:
        """
        Send summary email with all job applications for the day.

        Args:
            recipient_email: Recipient's email address
            jobs_data: List of job dictionaries with application details
            total_jobs_found: Total number of jobs found in search

        Returns:
            True if email sent successfully, False otherwise
        """
        today = datetime.now().strftime("%B %d, %Y")
        subject = f"Job Application Summary - {today} ({len(jobs_data)} Applications)"

        # Create summary email body
        body = self._create_summary_email_body(jobs_data, total_jobs_found, today)

        # Collect all attachments
        attachments = []
        for job in jobs_data:
            if job.get('resume_path') and os.path.exists(job['resume_path']):
                attachments.append(job['resume_path'])
            if job.get('cover_letter_path') and os.path.exists(job['cover_letter_path']):
                attachments.append(job['cover_letter_path'])

        # Send email with all attachments
        return self._send_email(recipient_email, subject, body, attachments=attachments)

    def _create_individual_email_body(self, job_data: Dict) -> str:
        """Create HTML email body for individual job application."""

        company = job_data.get('company', 'N/A')
        title = job_data.get('title', 'N/A')
        location = job_data.get('location', 'N/A')
        job_url = job_data.get('job_url', '#')
        salary = job_data.get('interval', 'Not specified')
        description = job_data.get('description', 'No description available')[:300] + "..."

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
                .job-detail {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #555; }}
                .button {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    display: inline-block;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .attachments {{ margin-top: 20px; padding: 15px; background-color: #e8f5e9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Job Application</h1>
                </div>

                <div class="content">
                    <h2>{title}</h2>

                    <div class="job-detail">
                        <span class="label">Company:</span> {company}
                    </div>

                    <div class="job-detail">
                        <span class="label">Location:</span> {location}
                    </div>

                    <div class="job-detail">
                        <span class="label">Salary:</span> {salary}
                    </div>

                    <div class="job-detail">
                        <span class="label">Description:</span><br>
                        {description}
                    </div>

                    <div style="text-align: center;">
                        <a href="{job_url}" class="button">Apply Now →</a>
                    </div>

                    <div class="attachments">
                        <strong>📎 Attached Documents:</strong>
                        <ul>
                            <li>Customized Resume (PDF)</li>
                            <li>Cover Letter (PDF)</li>
                        </ul>
                    </div>
                </div>

                <div style="margin-top: 20px; padding: 15px; background-color: #f0f0f0; font-size: 12px; color: #666;">
                    <p>This is an automated email from Jobby Bot. Your customized resume and cover letter are attached.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _create_summary_email_body(
        self,
        jobs_data: List[Dict],
        total_jobs_found: int,
        date: str
    ) -> str:
        """Create HTML email body for daily summary."""

        # Build job list HTML
        job_list_html = ""
        for i, job in enumerate(jobs_data, 1):
            company = job.get('company', 'N/A')
            title = job.get('title', 'N/A')
            location = job.get('location', 'N/A')
            job_url = job.get('job_url', '#')
            match_score = job.get('match_score', 'N/A')

            job_list_html += f"""
            <div style="margin: 15px 0; padding: 15px; background-color: white; border-left: 4px solid #4CAF50;">
                <h3 style="margin: 0 0 10px 0;">{i}. {title}</h3>
                <div><strong>Company:</strong> {company}</div>
                <div><strong>Location:</strong> {location}</div>
                <div><strong>Match Score:</strong> {match_score}%</div>
                <div style="margin-top: 10px;">
                    <a href="{job_url}" style="color: #4CAF50; text-decoration: none; font-weight: bold;">
                        View Job →
                    </a>
                </div>
            </div>
            """

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 30px; text-align: center; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 8px; }}
                .stat-number {{ font-size: 32px; font-weight: bold; color: #2196F3; }}
                .stat-label {{ font-size: 14px; color: #666; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Job Application Summary</h1>
                    <p style="font-size: 18px; margin: 5px 0;">{date}</p>
                </div>

                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">{total_jobs_found}</div>
                        <div class="stat-label">Jobs Found</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{len(jobs_data)}</div>
                        <div class="stat-label">Applications Sent</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{len(jobs_data) * 2}</div>
                        <div class="stat-label">Documents Created</div>
                    </div>
                </div>

                <div class="content">
                    <h2>📋 Job Applications</h2>
                    {job_list_html}

                    <div style="margin-top: 30px; padding: 20px; background-color: #e3f2fd; border-radius: 8px;">
                        <h3>📎 Attached Documents</h3>
                        <p>All customized resumes and cover letters for today's applications are attached to this email.</p>
                        <p><strong>Total files:</strong> {len(jobs_data) * 2} PDFs</p>
                    </div>
                </div>

                <div style="margin-top: 20px; padding: 15px; background-color: #f0f0f0; font-size: 12px; color: #666; text-align: center;">
                    <p>Generated by Jobby Bot - Your AI Job Application Assistant</p>
                    <p>Keep track of all applications in your Notion database</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _send_email(
        self,
        recipient_email: str,
        subject: str,
        body_html: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email with optional attachments via SMTP.

        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            body_html: HTML email body
            attachments: List of file paths to attach

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Attach HTML body
            msg.attach(MIMEText(body_html, 'html'))

            # Attach files
            if attachments:
                for file_path in attachments:
                    if file_path and os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                            filename = Path(file_path).name

                            attachment = MIMEApplication(file_data, _subtype="pdf")
                            attachment.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=filename
                            )
                            msg.attach(attachment)

            # Connect to SMTP server and send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"❌ Error sending email: {str(e)}")
            return False


def create_email_sender_from_env() -> Optional[EmailSender]:
    """
    Create EmailSender instance from environment variables.

    Returns:
        EmailSender instance or None if configuration is missing
    """
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        print("⚠️  Email configuration missing in .env file")
        return None

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        print("❌ Invalid SMTP_PORT in .env file")
        return None

    return EmailSender(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        sender_email=sender_email,
        sender_password=sender_password,
        use_tls=True
    )
