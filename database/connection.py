"""Database connection management.

Provides a single shared connection (singleton) to every database module so
the application never opens many independent connections. Handles schema
initialization on first startup and enables SQLite WAL mode for better
concurrent read performance.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from config import settings
from utils.logger import get_logger

log = get_logger("database.connection")

_conn: sqlite3.Connection | None = None

# SQLite writes can throw "database is locked"; retry briefly on those.
_LOCK_BUSY_SQLITE_CODES = (sqlite3.OperationalError,)


def get_connection() -> sqlite3.Connection:
    """Return the shared SQLite connection, creating + initializing if needed."""
    global _conn
    if _conn is None:
        db_path: Path = settings.get_database_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        # WAL improves concurrent read performance (see architecture Problem 5).
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.row_factory = sqlite3.Row
        initialize_database()
        log.info("Connected to SQLite database at %s", db_path)
    return _conn


def initialize_database() -> None:
    """Create all tables/indexes if they do not already exist.

    Safe to call on every startup because every statement is
    ``CREATE ... IF NOT EXISTS``.
    """
    from database import models

    conn = get_connection()
    cursor = conn.cursor()
    for ddl in models.get_all_schema_statements():
        cursor.execute(ddl)
    conn.commit()


def close_connection() -> None:
    """Gracefully close the shared connection."""
    global _conn
    if _conn is not None:
        _conn.commit()
        _conn.close()
        _conn = None
        log.info("Database connection closed")


def execute_with_retry(sql: str, params: tuple = (), *, retries: int = 3):
    """Run a write statement with a short retry on SQLite lock errors.

    Implements the 'retry on lock' behaviour described in the architecture
    (Problem 5): wait ~100ms and retry up to 3 times before giving up.
    """
    import time

    conn = get_connection()
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        except _LOCK_BUSY_SQLITE_CODES as exc:
            last_err = exc
            if "locked" in str(exc).lower():
                time.sleep(0.1 * (attempt + 1))
                continue
            raise
    raise last_err  # type: ignore[misc]


def get_all_products() -> list[sqlite3.Row]:
    """Debug/diagnostic helper: return every product row."""
    conn = get_connection()
    return list(conn.execute("SELECT * FROM products ORDER BY id"))
