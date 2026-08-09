"""All product-table database operations (Repository Pattern).

No raw SQL is written outside this module for product data, so switching to
another database later only requires updating these files.
"""
from __future__ import annotations

import datetime as dt

from database.connection import get_connection

_TABLE = "products"
_FIELDS = (
    "daraz_product_id",
    "name",
    "current_price",
    "original_price",
    "rating",
    "review_count",
    "sales_signal",
    "category",
    "brand",
    "thumbnail_url",
    "product_url",
    "seller_count_known",
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def insert_product(product_data: dict) -> int:
    """Insert a new product row. Returns the new row's internal ID."""
    conn = get_connection()
    now = _now()
    data = dict(product_data)
    data.setdefault("created_at", now)
    data["updated_at"] = now
    data["last_seen_at"] = now

    cols = _FIELDS + ("created_at", "updated_at", "last_seen_at")
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO {_TABLE} ({', '.join(cols)}) VALUES ({placeholders})"
    cursor = conn.execute(sql, tuple(data.get(c) for c in cols))
    conn.commit()
    return int(cursor.lastrowid)


def update_product(product_id: int, product_data: dict) -> bool:
    """Update an existing product row with fresh data. Returns success bool."""
    conn = get_connection()
    data = {k: product_data.get(k) for k in _FIELDS if k in product_data}
    data["updated_at"] = _now()
    data["last_seen_at"] = _now()
    if not data:
        return False
    assignments = ", ".join(f"{k}=?" for k in data)
    cursor = conn.execute(
        f"UPDATE {_TABLE} SET {assignments} WHERE id=?",
        tuple(data.values()) + (product_id,),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_product_by_daraz_id(daraz_product_id: str) -> dict | None:
    """Look up a product by its Daraz-assigned ID, or return None."""
    conn = get_connection()
    row = conn.execute(
        f"SELECT * FROM {_TABLE} WHERE daraz_product_id=?", (daraz_product_id,)
    ).fetchone()
    return dict(row) if row else None


def get_product_by_id(internal_id: int) -> dict | None:
    """Retrieve a product by our internal database ID."""
    conn = get_connection()
    row = conn.execute(f"SELECT * FROM {_TABLE} WHERE id=?", (internal_id,)).fetchone()
    return dict(row) if row else None


def get_all_products(limit: int = 100, offset: int = 0) -> list[dict]:
    """Return a paginated list of all products."""
    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM {_TABLE} ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [dict(r) for r in rows]


def search_products_local(keyword: str, limit: int = 100) -> list[dict]:
    """Search the local database for products whose name contains keyword.

    Used to surface cached results quickly while a live search runs.
    """
    conn = get_connection()
    pattern = f"%{keyword.strip()}%"
    rows = conn.execute(
        f"SELECT * FROM {_TABLE} WHERE name LIKE ? ORDER BY review_count DESC LIMIT ?",
        (pattern, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_product(product_data: dict) -> int:
    """Insert or update a product by Daraz ID. Returns the internal ID."""
    existing = get_product_by_daraz_id(product_data["daraz_product_id"])
    if existing is None:
        return insert_product(product_data)
    update_product(existing["id"], product_data)
    return existing["id"]


def get_product_count() -> int:
    conn = get_connection()
    row = conn.execute(f"SELECT COUNT(*) AS c FROM {_TABLE}").fetchone()
    return int(row["c"])
