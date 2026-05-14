"""Seed script — inserts 10 sample jobs into the jobs table for local testing.

Usage (from the project root):
    python -m ui_api.seed_mock_data
or:
    python ui_api/seed_mock_data.py
"""

import sys
from pathlib import Path

# Allow running directly as a script without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui_api.database import get_connection, init_jobs_table  # noqa: E402

SAMPLE_JOBS = [
    {
        "external_id": "mock-001",
        "title": "Senior Software Engineer",
        "company": "Acme Corp",
        "location": "San Francisco, CA",
        "job_url": "https://jobs.acme.com/senior-swe-001",
        "site": "linkedin",
        "date_posted": "2026-03-08",
        "salary": "USD 160,000 – 200,000 yearly",
        "description": (
            "We're looking for a senior engineer to join our platform team. "
            "You'll work on high-scale distributed systems with Python, Go, and Kubernetes."
        ),
        "status": "discovered",
    },
    {
        "external_id": "mock-002",
        "title": "Full-Stack Engineer",
        "company": "StartupXYZ",
        "location": "Remote",
        "job_url": "https://startupxyz.io/careers/fullstack",
        "site": "indeed",
        "date_posted": "2026-03-07",
        "salary": "USD 120,000 – 150,000 yearly",
        "description": (
            "Join our seed-stage startup building the future of fintech. "
            "Stack: React, FastAPI, PostgreSQL."
        ),
        "status": "discovered",
    },
    {
        "external_id": "mock-003",
        "title": "Machine Learning Engineer",
        "company": "DeepMind Labs",
        "location": "New York, NY",
        "job_url": "https://deepmindlabs.ai/jobs/mle",
        "site": "glassdoor",
        "date_posted": "2026-03-06",
        "salary": "USD 180,000 – 230,000 yearly",
        "description": (
            "Research and production ML engineering role. "
            "Experience with PyTorch, CUDA, and large-scale training required."
        ),
        "status": "ready",
        "fit_score": 87,
        "fit_assessment": "Strong alignment with ML background and Python expertise.",
    },
    {
        "external_id": "mock-004",
        "title": "Backend Engineer — Python",
        "company": "CloudBase",
        "location": "Austin, TX",
        "job_url": "https://cloudbase.io/jobs/backend-python",
        "site": "linkedin",
        "date_posted": "2026-03-05",
        "salary": "USD 140,000 – 170,000 yearly",
        "description": "Build and maintain scalable REST APIs. Django/FastAPI experience preferred.",
        "status": "ready",
        "fit_score": 92,
        "fit_assessment": "Excellent fit — direct match with FastAPI experience.",
    },
    {
        "external_id": "mock-005",
        "title": "DevOps Engineer",
        "company": "Infra Pro",
        "location": "Seattle, WA",
        "job_url": "https://infrapro.com/openings/devops",
        "site": "indeed",
        "date_posted": "2026-03-04",
        "salary": "USD 130,000 – 160,000 yearly",
        "description": (
            "Manage CI/CD pipelines, Kubernetes clusters, and AWS infrastructure. "
            "Terraform expertise a plus."
        ),
        "status": "discovered",
    },
    {
        "external_id": "mock-006",
        "title": "Data Engineer",
        "company": "Analytics Co",
        "location": "Chicago, IL",
        "job_url": "https://analyticsco.com/careers/data-engineer",
        "site": "glassdoor",
        "date_posted": "2026-03-03",
        "salary": "USD 115,000 – 145,000 yearly",
        "description": "Design and maintain data pipelines with Spark, dbt, and Snowflake.",
        "status": "applied",
        "fit_score": 75,
        "fit_assessment": "Good fit but limited Spark experience.",
    },
    {
        "external_id": "mock-007",
        "title": "iOS Engineer",
        "company": "MobileFirst",
        "location": "Boston, MA",
        "job_url": "https://mobilefirst.app/jobs/ios",
        "site": "linkedin",
        "date_posted": "2026-03-03",
        "salary": "USD 135,000 – 165,000 yearly",
        "description": "Swift / SwiftUI engineer to build consumer mobile apps at scale.",
        "status": "discovered",
    },
    {
        "external_id": "mock-008",
        "title": "Platform Engineer",
        "company": "Hyperscale",
        "location": "Remote",
        "job_url": "https://hyperscale.io/platform-engineer",
        "site": "indeed",
        "date_posted": "2026-03-02",
        "salary": "USD 155,000 – 195,000 yearly",
        "description": (
            "Build developer-facing tooling and internal platforms. "
            "Strong Golang and distributed systems background required."
        ),
        "status": "applied",
        "fit_score": 68,
        "fit_assessment": "Moderate fit — Golang experience is limited.",
    },
    {
        "external_id": "mock-009",
        "title": "Security Engineer",
        "company": "CyberGuard",
        "location": "Washington, DC",
        "job_url": "https://cyberguard.com/careers/security",
        "site": "glassdoor",
        "date_posted": "2026-03-01",
        "salary": "USD 145,000 – 185,000 yearly",
        "description": (
            "Application security, penetration testing, and secure SDLC. "
            "OSCP or equivalent certifications preferred."
        ),
        "status": "discovered",
    },
    {
        "external_id": "mock-010",
        "title": "Staff Engineer",
        "company": "Enterprise SaaS",
        "location": "Denver, CO (Hybrid)",
        "job_url": "https://enterprisesaas.com/jobs/staff-engineer",
        "site": "linkedin",
        "date_posted": "2026-02-28",
        "salary": "USD 200,000 – 250,000 yearly",
        "description": (
            "Technical leadership role owning architecture across multiple product squads. "
            "8+ years engineering experience required."
        ),
        "status": "ready",
        "fit_score": 80,
        "fit_assessment": "Strong architecture background; meets seniority bar.",
    },
]


def seed() -> None:
    """Insert sample jobs, skipping any whose external_id already exists."""
    init_jobs_table()
    conn = get_connection()
    inserted = 0
    skipped = 0
    try:
        for job in SAMPLE_JOBS:
            exists = conn.execute(
                "SELECT 1 FROM jobs WHERE external_id = ?", (job["external_id"],)
            ).fetchone()
            if exists:
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO jobs (
                    external_id, title, company, location, job_url, site,
                    date_posted, salary, description, status,
                    fit_score, fit_assessment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job["external_id"],
                    job["title"],
                    job["company"],
                    job["location"],
                    job["job_url"],
                    job["site"],
                    job["date_posted"],
                    job.get("salary"),
                    job.get("description"),
                    job.get("status", "discovered"),
                    job.get("fit_score"),
                    job.get("fit_assessment"),
                ),
            )
            inserted += 1

        conn.commit()
    finally:
        conn.close()

    print(f"Seed complete: {inserted} jobs inserted, {skipped} already existed.")


if __name__ == "__main__":
    seed()
