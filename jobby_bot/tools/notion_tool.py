"""Notion tool wrapper for tracking job applications."""

import os
from datetime import datetime
from typing import Optional

from notion_client import Client


class NotionTool:
    """
    Wrapper around notion-client for job application tracking.
    """

    def __init__(self, database_id: Optional[str] = None):
        """
        Initialize Notion tool.

        Args:
            database_id: Notion database ID (if not provided, reads from NOTION_DATABASE_ID env var)
        """
        self.api_key = os.environ.get("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError(
                "NOTION_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        self.database_id = database_id or os.environ.get("NOTION_DATABASE_ID")
        if not self.database_id:
            raise ValueError(
                "NOTION_DATABASE_ID not found. "
                "Please set it in your .env file or pass it to the constructor."
            )

        self.client = Client(auth=self.api_key)

        # Validate database exists and is accessible
        try:
            self.client.databases.retrieve(database_id=self.database_id)
            print(f"✅ Connected to Notion database: {self.database_id[:8]}...")
        except Exception as e:
            raise ValueError(
                f"Could not access Notion database {self.database_id}: {e}\n"
                "Make sure the database ID is correct and the integration has access."
            )

    def create_job_entry(
        self,
        job_title: str,
        company: str,
        job_url: str,
        description: str = "",
        status: str = "To Apply",
        resume_path: Optional[str] = None,
        cover_letter_path: Optional[str] = None,
        applied_date: Optional[str] = None,
        location: Optional[str] = None,
        salary: Optional[str] = None
    ) -> str:
        """
        Create a new job entry in the Notion database.

        Args:
            job_title: Title of the job
            company: Company name
            job_url: URL to the job listing
            description: Job description (truncated to 2000 chars for Notion)
            status: Application status (default: "To Apply")
            resume_path: Path to customized resume file
            cover_letter_path: Path to cover letter file
            applied_date: Date applied (ISO format string)
            location: Job location
            salary: Salary information

        Returns:
            URL to the created Notion page
        """
        # Truncate description to fit Notion's rich text limit
        if len(description) > 2000:
            description = description[:1997] + "..."

        # Build properties dictionary
        properties = {
            "Job Title": {"title": [{"text": {"content": job_title}}]},
            "Company": {"rich_text": [{"text": {"content": company}}]},
            "Job URL": {"url": job_url},
            "Status": {"select": {"name": status}},
        }

        # Add optional fields
        if description:
            properties["Description"] = {
                "rich_text": [{"text": {"content": description}}]
            }

        if location:
            properties["Location"] = {
                "rich_text": [{"text": {"content": location}}]
            }

        if salary:
            properties["Salary"] = {
                "rich_text": [{"text": {"content": salary}}]
            }

        if resume_path:
            properties["Resume Path"] = {
                "rich_text": [{"text": {"content": resume_path}}]
            }

        if cover_letter_path:
            properties["Cover Letter Path"] = {
                "rich_text": [{"text": {"content": cover_letter_path}}]
            }

        if applied_date:
            properties["Applied Date"] = {"date": {"start": applied_date}}

        try:
            # Create the page
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )

            page_url = response["url"]
            print(f"✅ Created Notion entry: {job_title} at {company}")
            return page_url

        except Exception as e:
            print(f"❌ Error creating Notion entry for {job_title}: {e}")
            return ""

    def update_status(
        self,
        page_id: str,
        new_status: str
    ) -> bool:
        """
        Update the status of a job application.

        Args:
            page_id: Notion page ID
            new_status: New status value
                ("To Apply", "Applied", "Interview", "Offer", "Rejected")

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {"select": {"name": new_status}}
                }
            )
            print(f"✅ Updated status to: {new_status}")
            return True

        except Exception as e:
            print(f"❌ Error updating status: {e}")
            return False

    def add_notes(
        self,
        page_id: str,
        notes: str
    ) -> bool:
        """
        Add notes to a job application page.

        Args:
            page_id: Notion page ID
            notes: Notes to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Append to the page as a new block
            self.client.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": notes}}]
                        }
                    }
                ]
            )
            print(f"✅ Added notes to page")
            return True

        except Exception as e:
            print(f"❌ Error adding notes: {e}")
            return False

    def batch_create_entries(
        self,
        jobs_data: list[dict]
    ) -> list[str]:
        """
        Create multiple job entries in batch.

        Args:
            jobs_data: List of dictionaries with job data
                Each dict should have keys: job_title, company, job_url, etc.

        Returns:
            List of created Notion page URLs
        """
        page_urls = []

        for job in jobs_data:
            url = self.create_job_entry(**job)
            if url:
                page_urls.append(url)

        print(f"\n✅ Created {len(page_urls)} Notion entries")
        return page_urls
