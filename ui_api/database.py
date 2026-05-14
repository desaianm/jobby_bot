"""Database module for Job Ops UI API.

Manages the `jobs` table in the existing SQLite DB. All operations use
synchronous sqlite3 — no DROP TABLE or DELETE statements used.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Fixed path to the existing shared SQLite database
DB_PATH = Path(__file__).parent.parent / "jobby_bot" / "data" / "jobby_bot.db"

VALID_STATUSES = {"discovered", "ready", "applied", "archived"}


def get_connection() -> sqlite3.Connection:
    """Return a connection with dict-like row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_jobs_table() -> None:
    """Create the jobs table if it does not already exist."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                job_url TEXT,
                site TEXT,
                date_posted TEXT,
                salary TEXT,
                description TEXT,
                status TEXT DEFAULT 'discovered',
                fit_score INTEGER,
                fit_assessment TEXT,
                tailored_summary TEXT,
                resume_path TEXT,
                cover_letter_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def get_jobs(status: Optional[str] = None) -> list[dict]:
    """Return all jobs, optionally filtered by status.

    Args:
        status: One of 'discovered', 'ready', 'applied', or None for all.

    Returns:
        List of job dicts ordered by created_at descending.
    """
    conn = get_connection()
    try:
        if status and status in VALID_STATUSES:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        else:
            # Exclude archived by default; use status='archived' to fetch them
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status != 'archived' ORDER BY created_at DESC"
            )
        return [_row_to_dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_job(job_id: int) -> Optional[dict]:
    """Return a single job by primary key, or None if not found.

    Args:
        job_id: The integer primary key.

    Returns:
        Job dict or None.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        )
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def update_job_status(job_id: int, status: str) -> bool:
    """Update only the status column for a job.

    Args:
        job_id: Primary key of the job to update.
        status: New status value (must be in VALID_STATUSES).

    Returns:
        True if a row was updated, False otherwise.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}.")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), job_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# Allowed mutable fields for update_job_fields (guards against SQL injection)
_MUTABLE_FIELDS = {
    "status",
    "fit_score",
    "fit_assessment",
    "tailored_summary",
    "resume_path",
    "cover_letter_path",
    "title",
    "company",
    "location",
    "job_url",
    "salary",
    "description",
}


def update_job_fields(job_id: int, **fields: Any) -> bool:
    """Update one or more allowed fields on a job row.

    Args:
        job_id: Primary key.
        **fields: Keyword arguments where keys are column names.

    Returns:
        True if a row was updated, False otherwise.

    Raises:
        ValueError: If an unknown field name is supplied.
    """
    if not fields:
        return False

    unknown = set(fields.keys()) - _MUTABLE_FIELDS
    if unknown:
        raise ValueError(f"Unknown/disallowed field(s): {unknown}")

    # Validate status value if provided
    if "status" in fields and fields["status"] not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{fields['status']}'. Must be one of {VALID_STATUSES}."
        )

    set_clauses = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values()) + [datetime.now().isoformat(), job_id]

    conn = get_connection()
    try:
        cursor = conn.execute(
            f"UPDATE jobs SET {set_clauses}, updated_at = ? WHERE id = ?",  # noqa: S608
            values,
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def insert_jobs(jobs_list: list[dict]) -> int:
    """Bulk-insert jobs from a JobSpy results list.

    Skips rows whose external_id already exists in the table.

    Args:
        jobs_list: List of dicts with job data (e.g. from JobSpy DataFrame.to_dict()).

    Returns:
        Number of rows actually inserted.
    """
    if not jobs_list:
        return 0

    conn = get_connection()
    inserted = 0
    try:
        for job in jobs_list:
            external_id = str(job.get("id", "")) or None
            # Skip if external_id already present to avoid duplicates
            if external_id:
                exists = conn.execute(
                    "SELECT 1 FROM jobs WHERE external_id = ? AND status != 'archived'",
                    (external_id,),
                ).fetchone()
                if exists:
                    continue

            # Normalise salary: combine min/max interval fields when present
            salary = _extract_salary(job)

            conn.execute(
                """
                INSERT INTO jobs (
                    external_id, title, company, location, job_url, site,
                    date_posted, salary, description, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered')
                """,
                (
                    external_id,
                    str(job.get("title") or ""),
                    str(job.get("company") or ""),
                    str(job.get("location") or ""),
                    str(job.get("job_url") or ""),
                    str(job.get("site") or ""),
                    str(job.get("date_posted") or ""),
                    salary,
                    str(job.get("description") or ""),
                ),
            )
            inserted += 1

        conn.commit()
    finally:
        conn.close()

    return inserted


def _extract_salary(job: dict) -> Optional[str]:
    """Build a human-readable salary string from JobSpy row fields."""
    # JobSpy may return min_amount / max_amount / currency / interval
    min_amt = job.get("min_amount")
    max_amt = job.get("max_amount")
    currency = job.get("currency", "USD") or "USD"
    interval = job.get("interval", "") or ""

    if min_amt and max_amt:
        return f"{currency} {min_amt:,.0f} – {max_amt:,.0f} {interval}".strip()
    if min_amt:
        return f"{currency} {min_amt:,.0f}+ {interval}".strip()
    if max_amt:
        return f"Up to {currency} {max_amt:,.0f} {interval}".strip()

    # Fall back to a direct salary string field if present
    return str(job.get("salary") or "") or None


def get_job_counts() -> dict:
    """Return row counts per status and total.

    Returns:
        Dict with keys: discovered, ready, applied, total.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM jobs WHERE status != 'archived' GROUP BY status"
        ).fetchall()
        counts: dict[str, int] = {"discovered": 0, "ready": 0, "applied": 0}
        for row in rows:
            status = row["status"]
            if status in counts:
                counts[status] = row["cnt"]
        counts["total"] = sum(counts.values())
        return counts
    finally:
        conn.close()
