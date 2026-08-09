"""Manages snapshot creation and retention.

Snapshot creation is normally triggered when a product is searched. This
service also handles retention: pruning snapshots older than the configured
window and (optionally) compressing daily snapshots into weekly aggregates.
"""
from __future__ import annotations

from config import settings
from database import snapshot_repository
from utils.logger import get_logger

log = get_logger("services.snapshot_service")


def take_snapshot(product_id: int, product: dict) -> int:
    """Save a snapshot row for a product's current state."""
    snap_id = snapshot_repository.insert_snapshot(product_id, {
        "price": product.get("current_price"),
        "rating": product.get("rating"),
        "review_count": product.get("review_count"),
        "sales_signal": product.get("sales_signal"),
    })
    return snap_id


def get_history(product_id: int, days: int = 90) -> list[dict]:
    """Return the snapshot history for a product (oldest first)."""
    return snapshot_repository.get_snapshots_for_product(product_id, days)


def run_retention(product_id: int | None = None) -> int:
    """Prune snapshots older than the retention window. Returns rows removed.

    If ``product_id`` is None, prunes for every product in the database.
    """
    keep_days = settings.get_snapshot_retention_days()
    from database import product_repository
    if product_id is not None:
        removed = snapshot_repository.delete_old_snapshots(product_id, keep_days)
        log.info("Retention for product %s removed %d rows", product_id, removed)
        return removed

    total = 0
    for p in product_repository.get_all_products(limit=10_000):
        total += snapshot_repository.delete_old_snapshots(p["id"], keep_days)
    log.info("Retention sweep removed %d rows", total)
    return total
