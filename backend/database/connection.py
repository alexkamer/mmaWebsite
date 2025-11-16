"""SQLite database connection."""
import sqlite3
from pathlib import Path
from typing import Any, Optional

# Database path - adjust if needed
DB_PATH = Path(__file__).parent.parent.parent / "data" / "mma.db"


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute a SELECT query and return results as list of dicts."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()


def execute_query_one(query: str, params: tuple = ()) -> Optional[dict[str, Any]]:
    """Execute a SELECT query and return first result as dict."""
    results = execute_query(query, params)
    return results[0] if results else None
