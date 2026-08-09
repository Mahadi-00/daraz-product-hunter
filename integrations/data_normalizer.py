"""Converts raw external data into the internal canonical format.

The rest of the application never sees Daraz's raw JSON. If the source changes
its field names tomorrow, only this file needs updating. Field-name mapping,
type coercion (e.g. "Rs. 2,499" -> 2499) and safe defaults all live here.

This file also documents what the ``sales_signal`` represents, since that
meaning drives the honesty of every sales estimate (architecture Problem 3).
"""
from __future__ import annotations

import re

from utils.logger import get_logger

log = get_logger("integrations.data_normalizer")

# --------------------------------------------------------------------------
# What the sales signal represents
# --------------------------------------------------------------------------
# We treat the source's "items sold" figure as a *cumulative* counter. The
# difference between two snapshots' signals is therefore interpreted as the
# number of units sold in the interval between them. If the source ever
# provides a figure that is NOT cumulative (e.g. resets daily), the meaning
# changes and this file must be updated to reflect it.
SALES_SIGNAL_MEANING = "cumulative units sold (difference over time = sales in period)"


def _parse_price(raw) -> int | None:
    """Parse a string/number like 'Rs. 2,499' or 2499 into an integer.

    Returns None if no usable number is found.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return int(round(float(raw)))
    digits = re.sub(r"[^\d]", "", str(raw))
    return int(digits) if digits else None


def _parse_int(raw) -> int | None:
    if raw in (None, ""):
        return None
    try:
        return int(float(str(raw).replace(",", "")))
    except (TypeError, ValueError):
        return None


def _parse_float(raw) -> float | None:
    if raw in (None, ""):
        return None
    try:
        return round(float(str(raw)), 2)
    except (TypeError, ValueError):
        return None


def normalize_product(raw_product: dict) -> dict:
    """Convert a single raw product object into our internal format."""
    current_price = _parse_price(raw_product.get("priceRaw") or raw_product.get("price")
                                 or raw_product.get("current_price"))
    original_price = _parse_price(raw_product.get("originalPriceRaw")
                                  or raw_product.get("original_price")
                                  or raw_product.get("originalPrice"))
    rating = _parse_float(raw_product.get("ratingStar") or raw_product.get("rating"))
    review_count = _parse_int(raw_product.get("reviewCount") or raw_product.get("review_count"))
    sales_signal = _parse_int(raw_product.get("itemSold") or raw_product.get("sales_signal")
                              or raw_product.get("sold"))

    return {
        "daraz_product_id": str(raw_product.get("item_id") or raw_product.get("daraz_product_id") or ""),
        "name": str(raw_product.get("name") or "Unnamed product").strip(),
        "current_price": current_price,
        "original_price": original_price,
        "rating": rating,
        "review_count": review_count or 0,
        "sales_signal": sales_signal,
        "category": (raw_product.get("category") or "").strip(),
        "brand": (raw_product.get("brand") or "").strip(),
        "thumbnail_url": raw_product.get("thumbnail") or raw_product.get("thumbnail_url") or "",
        "product_url": raw_product.get("itemUrl") or raw_product.get("product_url") or "",
    }


def normalize_seller(raw_seller: dict, product_id: str) -> dict:
    """Convert a raw seller object into our internal format."""
    return {
        "daraz_seller_id": str(raw_seller.get("seller_id") or raw_seller.get("daraz_seller_id") or ""),
        "seller_name": str(raw_seller.get("seller_name") or raw_seller.get("sellerName") or "Unknown"),
        "price": _parse_price(raw_seller.get("price") or raw_seller.get("priceRaw")),
        "rating": _parse_float(raw_seller.get("rating") or raw_seller.get("sellerRating")),
        "location": (raw_seller.get("location") or "").strip(),
        "is_official": bool(raw_seller.get("official") or raw_seller.get("is_official")),
        "product_daraz_id": product_id,
    }


def normalize_search_results(raw_response: dict) -> list[dict]:
    """Extract and normalize the list of products from a raw search response."""
    data = raw_response.get("data")
    if data is None:
        data = raw_response.get("products") or raw_response.get("results") or []
    if not isinstance(data, list):
        log.warning("Search response had no list under 'data'; returning []")
        return []
    normalized = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        normalized.append(normalize_product(raw))
    return normalized


def extract_sales_signal(raw_product: dict) -> int | None:
    """Extract the best available sales signal from a raw product.

    Returns None rather than inventing a number when no usable signal exists.
    """
    for key in ("itemSold", "sales_signal", "sold", "items_sold"):
        if key in raw_product:
            val = _parse_int(raw_product.get(key))
            if val is not None:
                return val
    return None
