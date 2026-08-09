"""Database schema definitions.

Every table and index in the system is defined here so the schema lives in
exactly one place. Repositories call :func:`get_all_schema_statements` at
startup (via ``connection.initialize_database``) to build the schema.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------

PRODUCTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    daraz_product_id   TEXT NOT NULL UNIQUE,
    name               TEXT NOT NULL,
    current_price      REAL,
    original_price     REAL,
    rating             REAL,
    review_count       INTEGER DEFAULT 0,
    sales_signal       INTEGER,
    category           TEXT,
    brand              TEXT,
    thumbnail_url      TEXT,
    product_url        TEXT,
    seller_count_known INTEGER DEFAULT 0,
    last_seen_at       TEXT,
    created_at         TEXT,
    updated_at         TEXT
);
"""

SELLERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sellers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id     INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    daraz_seller_id TEXT,
    seller_name    TEXT,
    price          REAL,
    rating         REAL,
    location       TEXT,
    is_official    INTEGER DEFAULT 0,
    updated_at     TEXT,
    UNIQUE(product_id, seller_name, price)
);
"""

SNAPSHOTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS product_snapshots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price        REAL,
    rating       REAL,
    review_count INTEGER,
    sales_signal INTEGER,
    timestamp    TEXT NOT NULL
);
"""

# --------------------------------------------------------------------------
# Indexes
# --------------------------------------------------------------------------

SNAPSHOTS_INDEX_SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_snapshots_product_time
ON product_snapshots (product_id, timestamp);
"""

SELLERS_INDEX_SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_sellers_product
ON sellers (product_id);
"""

_PRODUCT_NAME_INDEX = """
CREATE INDEX IF NOT EXISTS idx_products_name
ON products (name);
"""


# --------------------------------------------------------------------------
# Public accessor
# --------------------------------------------------------------------------
def get_all_schema_statements() -> list[str]:
    """Return every DDL statement needed to build the schema (idempotent)."""
    return [
        PRODUCTS_SCHEMA,
        SELLERS_SCHEMA,
        SNAPSHOTS_SCHEMA,
        SNAPSHOTS_INDEX_SCHEMA,
        SELLERS_INDEX_SCHEMA,
        _PRODUCT_NAME_INDEX,
    ]
