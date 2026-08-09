"""All seller-table database operations."""
from __future__ import annotations

import datetime as dt

from database.connection import get_connection

_TABLE = "sellers"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def insert_seller(seller_data: dict, product_id: int) -> int:
    """Save a seller record linked to a product. Returns the new row's ID."""
    conn = get_connection()
    cols = ("product_id", "daraz_seller_id", "seller_name", "price", "rating",
            "location", "is_official", "updated_at")
    values = (
        product_id,
        seller_data.get("daraz_seller_id"),
        seller_data.get("seller_name"),
        seller_data.get("price"),
        seller_data.get("rating"),
        seller_data.get("location"),
        1 if seller_data.get("is_official") else 0,
        _now(),
    )
    cursor = conn.execute(
        f"INSERT INTO {_TABLE} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
        values,
    )
    conn.commit()
    return int(cursor.lastrowid)


def get_sellers_for_product(product_id: int) -> list[dict]:
    """Return all seller records associated with a product."""
    conn = get_connection()
    rows = conn.execute(
        f"SELECT * FROM {_TABLE} WHERE product_id=? ORDER BY price ASC",
        (product_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def upsert_seller(seller_data: dict, product_id: int) -> int:
    """Insert a seller, or update the matching row if it already exists.

    The seller list is refreshed on every search (see architecture Problem 7):
    we match on (product_id, seller_name, price) and update rather than skip.
    """
    conn = get_connection()
    name = seller_data.get("seller_name")
    price = seller_data.get("price")
    row = conn.execute(
        f"SELECT id FROM {_TABLE} WHERE product_id=? AND seller_name=? AND price=?",
        (product_id, name, price),
    ).fetchone()
    if row is None:
        return insert_seller(seller_data, product_id)

    seller_id = int(row["id"])
    cols = ("daraz_seller_id", "seller_name", "price", "rating", "location",
            "is_official", "updated_at")
    values = (
        seller_data.get("daraz_seller_id"),
        seller_data.get("seller_name"),
        seller_data.get("price"),
        seller_data.get("rating"),
        seller_data.get("location"),
        1 if seller_data.get("is_official") else 0,
        _now(),
    )
    assignments = ", ".join(f"{c}=?" for c in cols)
    conn.execute(
        f"UPDATE {_TABLE} SET {assignments} WHERE id=?",
        tuple(values) + (seller_id,),
    )
    conn.commit()
    return seller_id


def count_sellers_for_product(product_id: int) -> int:
    """Return the number of distinct seller records for a product."""
    conn = get_connection()
    row = conn.execute(
        f"SELECT COUNT(*) AS c FROM {_TABLE} WHERE product_id=?",
        (product_id,),
    ).fetchone()
    return int(row["c"])
