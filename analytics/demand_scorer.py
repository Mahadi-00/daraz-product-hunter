"""Generates a demand score 0-100 and a demand classification.

Pure calculation with no side effects and no I/O: give it numbers, it gives
you a score and a label. Weights come from ``config.constants``.
"""
from __future__ import annotations

from config import constants


def normalize_signal(raw_value: float | None, min_val: float, max_val: float) -> float:
    """Map a metric into a 0-100 scale.

    Values at or above ``max_val`` become 100; at or below ``min_val`` become
    0. Returns 0.0 when the raw value is None or the range is degenerate.
    """
    if raw_value is None:
        return 0.0
    if max_val <= min_val:
        return 0.0
    normalized = (raw_value - min_val) / (max_val - min_val) * 100.0
    return max(0.0, min(100.0, normalized))


def classify_demand(score: float) -> dict:
    """Map a numeric score (0-100) to a classification dict.

    Returns ``{"key", "label", "emoji", "min", "max"}``.
    """
    for key in constants.DEMAND_ORDER:  # high -> low
        entry = constants.DEMAND_LABELS[key]
        if score >= entry["min"] and score <= entry["max"]:
            return {
                "key": key,
                "label": entry["label"],
                "emoji": entry["emoji"],
                "min": entry["min"],
                "max": entry["max"],
            }
    # Fallback (should not happen, but safe): lowest bucket.
    low = constants.DEMAND_LABELS["low"]
    return {"key": "low", "label": low["label"], "emoji": low["emoji"],
            "min": low["min"], "max": low["max"]}


def calculate_price_competitiveness_score(product_price: float | None,
                                          category_avg_price: float | None) -> float:
    """Score price competitiveness.

    Products priced near or below the category average score higher; very
    expensive products score lower. Returns 0-100.
    """
    if product_price is None:
        return 50.0  # unknown price -> neutral
    if category_avg_price is None or category_avg_price <= 0:
        return 70.0  # no benchmark -> mildly favorable
    ratio = product_price / category_avg_price
    # ratio <= 0.8 -> 100; ratio >= 1.6 -> ~0.
    score = (1.4 - ratio) / 0.6 * 100.0
    return max(0.0, min(100.0, score))


def calculate_demand_score(
    sales_velocity: float | None,
    review_count: int,
    rating: float,
    competition_score: float,
    price_score: float,
    review_score: float | None = None,
) -> dict:
    """Apply configured weights and produce a demand score + classification.

    Note on honesty: if there is no sales history yet (``sales_velocity`` is
    None), we still score using the other signals but mark ``confidence`` as
    lower so the UI can reflect that the score is provisional.
    """
    w = constants
    # Review-count signal: normalize up to MAX_REVIEWS_FOR_FULL_SCORE.
    if review_score is None:
        review_score = normalize_signal(review_count, 0, w.MAX_REVIEWS_FOR_FULL_SCORE)
    # Rating signal: normalize up to MIN_RATING_FOR_FULL_SCORE.
    rating_score = normalize_signal(rating, 0, w.MIN_RATING_FOR_FULL_SCORE)
    # Competition: invert so that *moderate* competition is good (some demand
    # proven) while extreme competition lowers the score.
    competition_factor = max(0.0, 100.0 - competition_score)

    if sales_velocity is not None:
        velocity_score = normalize_signal(sales_velocity, 0, 200)
        score = (
            w.WEIGHT_SALES_VELOCITY * velocity_score
            + w.WEIGHT_REVIEW_COUNT * review_score
            + w.WEIGHT_RATING * rating_score
            + w.WEIGHT_COMPETITION * competition_factor
            + w.WEIGHT_PRICE * price_score
        )
        confidence = "full"
    else:
        # No sales history yet: scale the available-weighted portion up.
        active_weight = w.WEIGHT_REVIEW_COUNT + w.WEIGHT_RATING + w.WEIGHT_COMPETITION + w.WEIGHT_PRICE
        score = (
            w.WEIGHT_REVIEW_COUNT * review_score
            + w.WEIGHT_RATING * rating_score
            + w.WEIGHT_COMPETITION * competition_factor
            + w.WEIGHT_PRICE * price_score
        ) / active_weight
        confidence = "partial"

    score = max(0.0, min(100.0, score))
    classification = classify_demand(score)
    return {
        "score": round(score, 1),
        "confidence": confidence,
        "classification": classification,
        "weights": {
            "sales_velocity": w.WEIGHT_SALES_VELOCITY,
            "review_count": w.WEIGHT_REVIEW_COUNT,
            "rating": w.WEIGHT_RATING,
            "competition": w.WEIGHT_COMPETITION,
            "price": w.WEIGHT_PRICE,
        },
    }
