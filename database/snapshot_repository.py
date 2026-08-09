"""All snapshot-table database operations.

Snapshots are time-series data, so this repository adds query patterns that
the analytics engine relies on: chronological range queries by product and
retention/cleanup of old records.
"""
from __future__ import annotations

import datetime as dt

from database.connection import get_connection

_TABLE = "product_snapshots"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def insert_snapshot(product_id: int, snapshot_data: dict) -> int:
    """Save a snapshot row for a product at the current timestamp."""
    conn = get_connection()
    cols = ("product_id", "price", "rating", "review_count", "sales_signal", "timestamp")
    values = (
        product_id,
        snapshot_data.get("price"),
        snapshot_data.get("rating"),
        snapshot_data.get("review_count"),
        snapshot_data.get("sales_signal"),
        snapshot_data.get("timestamp") or _now(),
    )
    cursor = conn.execute(
        f"INSERT INTO {_TABLE} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
        values,
    )
    conn.commit()
    return int(cursor.lastrowid)


def get_snapshots_for_product(product_id: int, days: int) -> list[dict]:
    """Return snapshots within the last N days, oldest first.

    The analytics engine needs chronological order, so ordering by timestamp
    ascending is handled here, not in callers.
    """
    conn = get_connection()
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    rows = conn.execute(
        f"SELECT * FROM {_TABLE} WHERE product_id=? AND timestamp>=? "
        f"ORDER BY timestamp ASC",
        (product_id, cutoff),
    ).fetchall()
    return [dict(r) for r in rows]


def get_latest_snapshot(product_id: int) -> dict | None:
    """Return the single most recent snapshot for a product, or None."""
    conn = get_connection()
    row = conn.execute(
        f"SELECT * FROM {_TABLE} WHERE product_id=? ORDER BY timestamp DESC LIMIT 1",
        (product_id,),
    ).fetchone()
    return dict(row) if row else None


def get_snapshot_count(product_id: int) -> int:
    """Return how many snapshots exist for a product."""
    conn = get_connection()
    row = conn.execute(
        f"SELECT COUNT(*) AS c FROM {_TABLE} WHERE product_id=?", (product_id,)
    ).fetchone()
    return int(row["c"])


def delete_old_snapshots(product_id: int, keep_days: int) -> int:
    """Delete snapshots older than ``keep_days``. Returns count deleted."""
    conn = get_connection()
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=keep_days)).isoformat()
    cursor = conn.execute(
        f"DELETE FROM {_TABLE} WHERE product_id=? AND timestamp<?",
        (product_id, cutoff),
    )
    conn.commit()
    return cursor.rowcount


def get_all_snapshot_count() -> int:
    conn = get_connection()
    row = conn.execute(f"SELECT COUNT(*) AS c FROM {_TABLE}").fetchone()
    return int(row["c"])
