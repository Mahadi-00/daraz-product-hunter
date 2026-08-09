"""Pulls together all analytics results for a product into one clean object.

This is the module the UI calls when it needs the full picture of a product.
It orchestrates the sales, revenue, competition, demand and trend modules.
"""
from __future__ import annotations

from analytics import (competition_analyzer, demand_scorer, revenue_estimator,
                       sales_estimator, trend_analyzer)
from config import constants
from database import seller_repository, snapshot_repository
from utils.logger import get_logger

log = get_logger("services.analytics_service")


def get_full_product_analytics(product: dict, sellers: list[dict] | None = None,
                               snapshots: list[dict] | None = None) -> dict:
    """Compute the complete analytics picture for a product.

    ``sellers`` and ``snapshots`` may be passed in to avoid re-querying the
    database when the caller already has them (important to avoid Streamlit
    rerenders causing excessive DB/API work).
    """
    product_id = product["id"]
    if sellers is None:
        sellers = seller_repository.get_sellers_for_product(product_id)
    if snapshots is None:
        # Pull a generous window (120 days) so estimates have plenty of data.
        snapshots = snapshot_repository.get_snapshots_for_product(product_id, 120)

    # 7D and 30D sales estimates.
    estimates = {}
    for period in constants.ESTIMATE_PERIODS:
        estimates[period] = sales_estimator.estimate_sales(snapshots, period)

    # Revenue using the average price across sellers.
    avg_price = revenue_estimator.calculate_average_price(sellers)
    revenue_7 = revenue_estimator.estimate_revenue(
        estimates[7]["estimated_sales"], avg_price or product.get("current_price"))
    revenue_30 = revenue_estimator.estimate_revenue(
        estimates[30]["estimated_sales"], avg_price or product.get("current_price"))

    competition = competition_analyzer.analyze_competition(sellers)

    # Sales velocity: measured per-day change from the 7-day estimate.
    velocity = None
    if estimates[7]["estimated_sales"] is not None and estimates[7]["days_covered"]:
        velocity = estimates[7]["estimated_sales"] / max(estimates[7]["days_covered"], 1)

    # Price competitiveness vs. category average (fall back to own price).
    price_score = demand_scorer.calculate_price_competitiveness_score(
        product.get("current_price"),
        _category_avg_price(sellers) or product.get("current_price"))

    demand = demand_scorer.calculate_demand_score(
        sales_velocity=velocity,
        review_count=product.get("review_count") or 0,
        rating=product.get("rating") or 0.0,
        competition_score=competition["competition_score"],
        price_score=price_score,
    )

    trend = trend_analyzer.analyze_trend(snapshots)
    weekly = trend_analyzer.calculate_weekly_aggregates(snapshots)

    return {
        "product": product,
        "sellers": sellers,
        "snapshot_count": len(snapshots),
        "estimates": {
            "7d": estimates[7],
            "30d": estimates[30],
        },
        "revenue": {
            "7d": revenue_7,
            "30d": revenue_30,
            "average_price": avg_price,
        },
        "competition": competition,
        "demand": demand,
        "trend": trend,
        "weekly_aggregates": weekly,
    }


def get_summary_analytics(product: dict) -> dict:
    """Lighter analytics used for the results table.

    Only the metrics the table needs: demand score/class, 7D & 30D estimates,
    competition count, trend direction. Faster than full analytics.
    """
    full = get_full_product_analytics(product)
    return {
        "product_id": product["id"],
        "demand": full["demand"],
        "estimate_7d": full["estimates"]["7d"],
        "estimate_30d": full["estimates"]["30d"],
        "revenue_7d": full["revenue"]["7d"],
        "competition_score": full["competition"]["competition_score"],
        "seller_count": full["competition"]["seller_count"],
        "trend_direction": full["trend"]["direction"],
        "trend_percent": full["trend"]["percent_change"],
        "confidence": _overall_confidence(full),
    }


def _overall_confidence(full: dict) -> str:
    """Aggregate a single confidence label from the estimate confidences."""
    period_keys = [f"{p}d" for p in constants.ESTIMATE_PERIODS]
    confs = [full["estimates"][k]["confidence"] for k in period_keys]
    if "high" in confs:
        return "high"
    if "medium" in confs:
        return "medium"
    return "low"


def _category_avg_price(sellers: list[dict]) -> float | None:
    return revenue_estimator.calculate_average_price(sellers)
