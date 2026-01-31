"""SQLite database for meal logging and history tracking."""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".mela-mcp" / "meal_log.db"
DB_PATH = Path(os.environ.get("MELA_MEAL_LOG_PATH", str(DEFAULT_DB_PATH)))


def init_db(db_path: Path | None = None) -> None:
    """Create the meals table if it doesn't exist."""
    global DB_PATH
    if db_path is not None:
        DB_PATH = db_path
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                recipe_id INTEGER,
                tags TEXT,
                status TEXT NOT NULL DEFAULT 'planned',
                portions INTEGER,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def get_connection() -> sqlite3.Connection:
    """Get a connection to the meal log database."""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def log_meal(
    date: str,
    title: str,
    recipe_id: int | None = None,
    tags: str | None = None,
    status: str = "cooked",
    portions: int | None = None,
    notes: str | None = None,
) -> dict:
    """Insert a meal log entry and return the new row as a dict."""
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO meals (date, title, recipe_id, tags, status, portions, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (date, title, recipe_id, tags, status, portions, notes, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM meals WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def update_meal(meal_id: int, **kwargs) -> dict:
    """Update fields on an existing meal entry.

    Allowed fields: date, title, recipe_id, tags, status, portions, notes.
    """
    allowed = {"date", "title", "recipe_id", "tags", "status", "portions", "notes"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM meals WHERE id = ?", (meal_id,)).fetchone()
            if row is None:
                raise ValueError(f"No meal with id {meal_id}")
            return dict(row)
        finally:
            conn.close()

    fields["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [meal_id]

    conn = get_connection()
    try:
        conn.execute(f"UPDATE meals SET {set_clause} WHERE id = ?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM meals WHERE id = ?", (meal_id,)).fetchone()
        if row is None:
            raise ValueError(f"No meal with id {meal_id}")
        return dict(row)
    finally:
        conn.close()


def get_meals(
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
    tags: str | None = None,
) -> list[dict]:
    """Query meals with optional filters."""
    conditions = []
    params: list = []

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if tags:
        for tag in tags.split(","):
            conditions.append("tags LIKE ?")
            params.append(f"%{tag.strip()}%")

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    conn = get_connection()
    try:
        cursor = conn.execute(f"SELECT * FROM meals {where} ORDER BY date DESC", params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_unreconciled(days: int = 7) -> list[dict]:
    """Get meals with status 'planned' in the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM meals WHERE status = 'planned' AND date >= ? AND date <= ? ORDER BY date",
            (cutoff, today),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_tag_frequency(days: int = 90) -> dict[str, int]:
    """Return a dict of tag -> count over the given time window."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT tags FROM meals WHERE tags IS NOT NULL AND date >= ?",
            (cutoff,),
        )
        freq: dict[str, int] = {}
        for row in cursor.fetchall():
            for tag in row["tags"].split(","):
                tag = tag.strip()
                if tag:
                    freq[tag] = freq.get(tag, 0) + 1
        return freq
    finally:
        conn.close()


def get_stale_meals(days: int = 90, min_gap: int = 30) -> list[dict]:
    """Titles/recipe_ids not seen in min_gap days, looking back over days window.

    Returns meals that were cooked at some point in the window but whose most
    recent occurrence is older than min_gap days ago.
    """
    window_start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    stale_cutoff = (datetime.now() - timedelta(days=min_gap)).strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT title, recipe_id, MAX(date) as last_date, COUNT(*) as times_cooked
            FROM meals
            WHERE date >= ? AND status IN ('cooked', 'planned')
            GROUP BY COALESCE(recipe_id, title)
            HAVING MAX(date) < ?
            ORDER BY last_date ASC
            """,
            (window_start, stale_cutoff),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


init_db()
