"""JobSpy tool wrapper for job scraping from LinkedIn, Indeed, and Google."""

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from jobspy import scrape_jobs


class JobSpyTool:
    """
    Wrapper around python-jobspy for job scraping with error handling and filtering.
    """

    def __init__(self, output_dir: str = "output/job_listings"):
        """
        Initialize JobSpy tool.

        Args:
            output_dir: Directory to save job listings CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def search_jobs(
        self,
        search_term: str,
        location: str = "",
        sites: Optional[List[str]] = None,
        results_wanted: int = 20,
        hours_old: int = 72,
        is_remote: bool = False,
        job_type: Optional[str] = None,
        country_indeed: str = "USA"
    ) -> pd.DataFrame:
        """
        Search for jobs using JobSpy across multiple job sites.

        Args:
            search_term: Job title or keywords to search for
            location: Location to search (e.g., "San Francisco, CA")
            sites: List of sites to scrape (default: ["indeed", "linkedin", "google"])
            results_wanted: Number of results to retrieve (default: 20)
            hours_old: Only show jobs posted within this many hours (default: 72)
            is_remote: Filter for remote jobs only (default: False)
            job_type: Type of job - "fulltime", "parttime", "internship", "contract"
            country_indeed: Country code for Indeed (default: "USA")

        Returns:
            DataFrame with job listings containing columns:
            - title: Job title
            - company: Company name
            - location: Job location
            - date_posted: Date the job was posted
            - job_url: URL to job listing
            - description: Job description
            - etc.
        """
        if sites is None:
            sites = ["indeed", "linkedin", "google"]

        print(f"\n🔍 Searching for '{search_term}' jobs...")
        print(f"   Location: {location or 'Any'}")
        print(f"   Remote: {is_remote}")
        print(f"   Sites: {', '.join(sites)}")
        print(f"   Results wanted: {results_wanted}")

        try:
            # Scrape jobs with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    jobs_df = scrape_jobs(
                        site_name=sites,
                        search_term=search_term,
                        location=location,
                        results_wanted=results_wanted,
                        hours_old=hours_old,
                        is_remote=is_remote,
                        job_type=job_type,
                        country_indeed=country_indeed
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                        print(f"   Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise

            if jobs_df is None or jobs_df.empty:
                print("❌ No jobs found")
                return pd.DataFrame()

            # Remove duplicates based on job_url
            initial_count = len(jobs_df)
            jobs_df = jobs_df.drop_duplicates(subset=['job_url'], keep='first')
            final_count = len(jobs_df)

            if initial_count > final_count:
                print(f"   Removed {initial_count - final_count} duplicates")

            # Save to CSV with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = self.output_dir / f"jobs_{timestamp}.csv"
            jobs_df.to_csv(csv_path, index=False)

            print(f"✅ Found {len(jobs_df)} jobs")
            print(f"   Saved to: {csv_path}")

            return jobs_df

        except Exception as e:
            print(f"❌ Error scraping jobs: {e}")
            # Return empty DataFrame on error
            return pd.DataFrame()

    def filter_jobs(
        self,
        jobs_df: pd.DataFrame,
        blacklist_companies: Optional[List[str]] = None,
        blacklist_keywords: Optional[List[str]] = None,
        min_salary: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Filter job listings based on blacklist and criteria.

        Args:
            jobs_df: DataFrame of job listings
            blacklist_companies: List of company names to exclude
            blacklist_keywords: List of keywords to exclude from titles/descriptions
            min_salary: Minimum salary (if salary info is available)

        Returns:
            Filtered DataFrame
        """
        if jobs_df.empty:
            return jobs_df

        filtered_df = jobs_df.copy()
        initial_count = len(filtered_df)

        # Filter by company blacklist
        if blacklist_companies:
            blacklist_lower = [c.lower() for c in blacklist_companies]
            filtered_df = filtered_df[
                ~filtered_df['company'].str.lower().isin(blacklist_lower)
            ]
            removed = initial_count - len(filtered_df)
            if removed > 0:
                print(f"   Removed {removed} jobs from blacklisted companies")

        # Filter by keyword blacklist in title and description
        if blacklist_keywords:
            for keyword in blacklist_keywords:
                keyword_lower = keyword.lower()
                before_count = len(filtered_df)

                # Check in title
                if 'title' in filtered_df.columns:
                    filtered_df = filtered_df[
                        ~filtered_df['title'].str.lower().str.contains(keyword_lower, na=False)
                    ]

                # Check in description
                if 'description' in filtered_df.columns:
                    filtered_df = filtered_df[
                        ~filtered_df['description'].str.lower().str.contains(keyword_lower, na=False)
                    ]

                removed = before_count - len(filtered_df)
                if removed > 0:
                    print(f"   Removed {removed} jobs containing '{keyword}'")

        final_count = len(filtered_df)
        if initial_count > final_count:
            print(f"   Final count after filtering: {final_count} jobs")

        return filtered_df
