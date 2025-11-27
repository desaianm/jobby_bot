"""SQLite database module for multi-user Jobby Bot support."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Database file location
DB_PATH = Path(__file__).parent / "data" / "jobby_bot.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            discord_user_id INTEGER UNIQUE NOT NULL,
            discord_username TEXT,
            email TEXT,
            auto_monitor_enabled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Resumes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            resume_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        )
    """)

    # Preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            preferences_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        )
    """)

    # Monitor state table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_state (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            processed_jobs TEXT,
            last_check TIMESTAMP,
            UNIQUE(user_id)
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_user(discord_user_id: int, discord_username: str = None) -> int:
    """Get existing user or create new one. Returns internal user ID."""
    conn = get_connection()
    cursor = conn.cursor()

    # Try to get existing user
    cursor.execute(
        "SELECT id FROM users WHERE discord_user_id = ?",
        (discord_user_id,)
    )
    row = cursor.fetchone()

    if row:
        user_id = row["id"]
        # Update username if provided
        if discord_username:
            cursor.execute(
                "UPDATE users SET discord_username = ?, updated_at = ? WHERE id = ?",
                (discord_username, datetime.now(), user_id)
            )
            conn.commit()
    else:
        # Create new user
        cursor.execute(
            "INSERT INTO users (discord_user_id, discord_username) VALUES (?, ?)",
            (discord_user_id, discord_username)
        )
        conn.commit()
        user_id = cursor.lastrowid

    conn.close()
    return user_id


def get_user_resume(discord_user_id: int) -> Optional[dict]:
    """Get user's resume as dict, or None if not set."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.resume_json FROM resumes r
        JOIN users u ON r.user_id = u.id
        WHERE u.discord_user_id = ?
    """, (discord_user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row["resume_json"])
    return None


def save_user_resume(discord_user_id: int, resume_dict: dict, discord_username: str = None):
    """Save or update user's resume."""
    user_id = get_or_create_user(discord_user_id, discord_username)

    conn = get_connection()
    cursor = conn.cursor()

    resume_json = json.dumps(resume_dict)

    # Upsert resume
    cursor.execute("""
        INSERT INTO resumes (user_id, resume_json)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            resume_json = excluded.resume_json,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, resume_json))

    conn.commit()
    conn.close()


def get_user_preferences(discord_user_id: int) -> Optional[dict]:
    """Get user's preferences as dict, or None if not set."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.preferences_json FROM preferences p
        JOIN users u ON p.user_id = u.id
        WHERE u.discord_user_id = ?
    """, (discord_user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row["preferences_json"])
    return None


def save_user_preferences(discord_user_id: int, preferences_dict: dict, discord_username: str = None):
    """Save or update user's preferences."""
    user_id = get_or_create_user(discord_user_id, discord_username)

    conn = get_connection()
    cursor = conn.cursor()

    preferences_json = json.dumps(preferences_dict)

    # Upsert preferences
    cursor.execute("""
        INSERT INTO preferences (user_id, preferences_json)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            preferences_json = excluded.preferences_json,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, preferences_json))

    conn.commit()
    conn.close()


def get_user_email(discord_user_id: int) -> Optional[str]:
    """Get user's email, or None if not set."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT email FROM users WHERE discord_user_id = ?",
        (discord_user_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return row["email"]
    return None


def set_user_email(discord_user_id: int, email: str, discord_username: str = None):
    """Set user's email address."""
    get_or_create_user(discord_user_id, discord_username)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET email = ?, updated_at = ? WHERE discord_user_id = ?",
        (email, datetime.now(), discord_user_id)
    )

    conn.commit()
    conn.close()


def is_auto_monitor_enabled(discord_user_id: int) -> bool:
    """Check if auto monitor is enabled for user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT auto_monitor_enabled FROM users WHERE discord_user_id = ?",
        (discord_user_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return bool(row["auto_monitor_enabled"])
    return False


def set_auto_monitor_enabled(discord_user_id: int, enabled: bool, discord_username: str = None):
    """Enable or disable auto monitor for user."""
    get_or_create_user(discord_user_id, discord_username)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET auto_monitor_enabled = ?, updated_at = ? WHERE discord_user_id = ?",
        (1 if enabled else 0, datetime.now(), discord_user_id)
    )

    conn.commit()
    conn.close()


def get_monitor_state(discord_user_id: int) -> dict:
    """Get user's monitor state (processed jobs and last check time)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ms.processed_jobs, ms.last_check FROM monitor_state ms
        JOIN users u ON ms.user_id = u.id
        WHERE u.discord_user_id = ?
    """, (discord_user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        processed_jobs = json.loads(row["processed_jobs"]) if row["processed_jobs"] else []
        return {
            "processed_jobs": processed_jobs,
            "last_check": row["last_check"]
        }
    return {"processed_jobs": [], "last_check": None}


def save_monitor_state(discord_user_id: int, processed_jobs: list, last_check: datetime = None):
    """Save user's monitor state."""
    user_id = get_or_create_user(discord_user_id)

    conn = get_connection()
    cursor = conn.cursor()

    processed_jobs_json = json.dumps(processed_jobs)
    last_check = last_check or datetime.now()

    # Upsert monitor state
    cursor.execute("""
        INSERT INTO monitor_state (user_id, processed_jobs, last_check)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            processed_jobs = excluded.processed_jobs,
            last_check = excluded.last_check
    """, (user_id, processed_jobs_json, last_check))

    conn.commit()
    conn.close()


def get_auto_monitor_users() -> list:
    """Get all users who have auto monitor enabled, email set, and preferences set."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.discord_user_id, u.discord_username, u.email,
               p.preferences_json, r.resume_json
        FROM users u
        JOIN preferences p ON p.user_id = u.id
        LEFT JOIN resumes r ON r.user_id = u.id
        WHERE u.auto_monitor_enabled = 1
          AND u.email IS NOT NULL
          AND u.email != ''
    """)

    rows = cursor.fetchall()
    conn.close()

    users = []
    for row in rows:
        users.append({
            "discord_user_id": row["discord_user_id"],
            "discord_username": row["discord_username"],
            "email": row["email"],
            "preferences": json.loads(row["preferences_json"]),
            "resume": json.loads(row["resume_json"]) if row["resume_json"] else None
        })

    return users
