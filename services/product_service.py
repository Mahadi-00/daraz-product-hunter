"""Product-specific operations: retrieval, upsert, existence checks."""
from __future__ import annotations

from database import product_repository, seller_repository, snapshot_repository


def get_or_create_from_normalized(product: dict) -> int:
    """Upsert a normalized product and return its internal database ID."""
    return product_repository.upsert_product(product)


def upsert_sellers(product_id: int, seller_list: list[dict]) -> int:
    """Upsert a list of seller records for a product. Returns seller count."""
    for seller in seller_list:
        seller_repository.upsert_seller(seller, product_id)
    return seller_repository.count_sellers_for_product(product_id)


def get_product(product_id: int) -> dict | None:
    return product_repository.get_product_by_id(product_id)


def product_exists(daraz_product_id: str) -> bool:
    return product_repository.get_product_by_daraz_id(daraz_product_id) is not None


def record_snapshot(product_id: int, product: dict) -> int:
    """Record a snapshot of a product's current state."""
    return snapshot_repository.insert_snapshot(product_id, {
        "price": product.get("current_price"),
        "rating": product.get("rating"),
        "review_count": product.get("review_count"),
        "sales_signal": product.get("sales_signal"),
    })
