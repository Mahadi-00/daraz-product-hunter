"""Orchestrates a full search operation.

The most important user action: given a keyword, this coordinates fetching,
normalizing, persisting, snapshotting and analyzing -- and returns a list of
enriched, filtered, sorted product dicts for the UI. Any product that fails
mid-pipeline is skipped gracefully so the others still appear.
"""
from __future__ import annotations

from integrations import data_normalizer, daraz_client
from database import seller_repository, snapshot_repository
from services import analytics_service, product_service
from utils import cache_manager, validators
from utils.logger import get_logger

log = get_logger("services.search_service")


def execute_search(keyword: str, filters: dict | None = None,
                   use_cache: bool = True) -> list[dict]:
    """Run the full search pipeline and return enriched product dicts.

    Steps: validate -> (cache check) -> fetch -> normalize -> upsert ->
    sellers -> snapshot -> analytics -> filter -> sort.
    """
    filters = filters or {}
    keyword = validators.validate_keyword(keyword)

    cache_key = cache_manager.cache_key(keyword, filters)
    if use_cache:
        cached = cache_manager.get(cache_key)
        if cached is not None:
            log.info("Cache hit for '%s'", keyword)
            return cached

    raw = _fetch(keyword)
    normalized_products = data_normalizer.normalize_search_results(raw)
    log.info("Fetched and normalized %d products for '%s'", len(normalized_products), keyword)

    enriched = []
    for product in normalized_products:
        if not product.get("daraz_product_id"):
            continue
        try:
            internal_id = product_service.get_or_create_from_normalized(product)
            product["id"] = internal_id

            # Seller data (best-effort; unknown is recorded as 0, not skipped).
            try:
                raw_sellers = daraz_client.get_client().get_product_sellers(
                    product["daraz_product_id"])
                sellers = [data_normalizer.normalize_seller(s, product["daraz_product_id"])
                           for s in raw_sellers]
                seller_count = product_service.upsert_sellers(internal_id, sellers)
                product["seller_count"] = seller_count
            except Exception as exc:  # noqa: BLE001
                log.warning("Seller fetch failed for %s: %s", product["daraz_product_id"], exc)
                product["seller_count"] = 0

            # Snapshot for history.
            product_service.record_snapshot(internal_id, product)

            # Analytics.
            enriched_dict = analytics_service.get_summary_analytics(product)
            enriched.append(_merge_product_and_analytics(product, enriched_dict))
        except Exception as exc:  # noqa: BLE001
            # Graceful skip: one bad product must not kill the whole search.
            log.warning("Skipping product %s due to error: %s",
                        product.get("daraz_product_id"), exc)
            continue

    enriched = apply_filters(enriched, filters)
    enriched = sort_results(enriched, filters.get("sort_by", "demand"))

    if use_cache:
        cache_manager.set(cache_key, enriched)
    return enriched


def _fetch(keyword: str) -> dict:
    client = daraz_client.get_client()
    return client.search_products(keyword, page=1,
                                  page_size=daraz_client.get_client().config.get("max_results", 20))


def apply_filters(products: list[dict], filters: dict) -> list[dict]:
    """Filter the enriched results by the user's selections."""
    result = products

    min_rating = filters.get("min_rating")
    if min_rating:
        result = [p for p in result
                  if (p.get("rating") or 0) >= min_rating]

    max_price = filters.get("max_price")
    if max_price:
        result = [p for p in result
                  if (p.get("current_price") or 0) <= max_price]

    demand_keys = filters.get("demand") or []
    if demand_keys:
        allowed = set(demand_keys)
        result = [p for p in result
                  if p.get("demand_class_key") in allowed]

    return result


def sort_results(products: list[dict], sort_by: str) -> list[dict]:
    """Sort results by a field. Unknown fields fall back to demand score."""
    sort_by = sort_by or "demand"
    reverse = True

    if sort_by == "price":
        key = lambda p: p.get("current_price") or 0  # noqa: E731
        reverse = False
    elif sort_by == "reviews":
        key = lambda p: p.get("review_count") or 0  # noqa: E731
    elif sort_by == "sales":
        key = lambda p: (p.get("estimate_7d_sales") or 0)  # noqa: E731
    else:  # default: demand score
        key = lambda p: p.get("demand_score") or 0  # noqa: E731

    return sorted(products, key=key, reverse=reverse)


def _merge_product_and_analytics(product: dict, summary: dict) -> dict:
    """Flatten a product dict with its summary analytics for easy UI use."""
    return {
        **product,
        "demand_score": summary["demand"]["score"],
        "demand_confidence": summary["demand"]["confidence"],
        "demand_class_key": summary["demand"]["classification"]["key"],
        "demand_label": summary["demand"]["classification"]["label"],
        "demand_emoji": summary["demand"]["classification"]["emoji"],
        "estimate_7d_sales": summary["estimate_7d"]["estimated_sales"],
        "estimate_7d_confidence": summary["estimate_7d"]["confidence"],
        "estimate_7d_extrapolated": summary["estimate_7d"]["is_extrapolated"],
        "estimate_30d_sales": summary["estimate_30d"]["estimated_sales"],
        "estimate_30d_confidence": summary["estimate_30d"]["confidence"],
        "revenue_7d": summary["revenue_7d"]["estimated_revenue"],
        "competition_score": summary["competition_score"],
        "seller_count": summary["seller_count"],
        "trend_direction": summary["trend_direction"],
        "trend_percent": summary["trend_percent"],
        "confidence": summary["confidence"],
        "snapshot_count": _snapshot_count(product["id"]),
    }


def _snapshot_count(product_id: int) -> int:
    try:
        return snapshot_repository.get_snapshot_count(product_id)
    except Exception:  # noqa: BLE001
        return 0
