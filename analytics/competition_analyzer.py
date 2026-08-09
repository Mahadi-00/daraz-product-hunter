"""Analyzes seller competition for a product.

More sellers = higher competition, but we also consider price clustering
(tightly clustered prices suggest strong competition; spread-out prices suggest
different market segments). Produces a numeric competition score 0-100 that
feeds into the demand scorer.
"""
from __future__ import annotations


def analyze_competition(sellers: list[dict]) -> dict:
    """Return a competition analysis dict for a list of sellers.

    Fields: ``seller_count``, ``price_min``, ``price_max``, ``price_spread``
    (0-1 normalized), ``avg_rating`` and ``competition_score`` (0-100).
    """
    prices = [s.get("price") for s in sellers if s.get("price") is not None]
    ratings = [s.get("rating") for s in sellers if s.get("rating") is not None]

    seller_count = len(sellers)
    price_min = min(prices) if prices else None
    price_max = max(prices) if prices else None

    # Normalized price spread: how wide the range is relative to its midpoint.
    price_spread = 0.0
    if prices and len(prices) > 1 and (price_max or 0) > 0:
        midpoint = (price_max + price_min) / 2.0
        price_spread = min(1.0, (price_max - price_min) / midpoint)

    avg_rating = (sum(ratings) / len(ratings)) if ratings else None

    score = calculate_competition_score(seller_count, price_spread, avg_rating)
    return {
        "seller_count": seller_count,
        "price_min": price_min,
        "price_max": price_max,
        "price_spread": round(price_spread, 4),
        "avg_rating": round(avg_rating, 2) if avg_rating is not None else None,
        "competition_score": round(score, 2),
    }


def calculate_competition_score(seller_count: int, price_spread: float, avg_rating: float | None) -> float:
    """Internal competition scoring.

    More sellers and tighter price clustering (lower spread) => higher
    competition. Rating contributes a mild factor. Returns 0-100.
    """
    # Seller factor: up to 100 at 15+ sellers.
    seller_score = min(100.0, seller_count * 6.5)

    # Price clustering factor: tight clustering (spread ~0) => 100.
    cluster_score = (1.0 - price_spread) * 100.0
    if seller_count <= 1:
        cluster_score = 0.0  # one seller is not "competition" regardless of spread

    # Rating factor: better-rated sellers compete harder.
    if avg_rating is None:
        rating_score = 50.0
    else:
        rating_score = min(100.0, (avg_rating / 5.0) * 100.0)

    return (seller_score * 0.5) + (cluster_score * 0.35) + (rating_score * 0.15)
