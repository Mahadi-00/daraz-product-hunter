"""Integration-style tests across the analytics + services layers."""
from __future__ import annotations

import datetime as dt

from analytics import competition_analyzer, revenue_estimator, trend_analyzer
from services import analytics_service, search_service
from database import product_repository, snapshot_repository


# ---------------------------------------------------------------------------
# Competition
# ---------------------------------------------------------------------------
def test_analyze_competition():
    sellers = [
        {"price": 100, "rating": 4.0},
        {"price": 110, "rating": 4.2},
        {"price": 120, "rating": 4.5},
    ]
    result = competition_analyzer.analyze_competition(sellers)
    assert result["seller_count"] == 3
    assert result["price_min"] == 100
    assert result["price_max"] == 120
    assert 0 <= result["competition_score"] <= 100


def test_more_sellers_means_more_competition():
    low = competition_analyzer.calculate_competition_score(2, 0.3, 4.0)
    high = competition_analyzer.calculate_competition_score(14, 0.1, 4.5)
    assert high > low


# ---------------------------------------------------------------------------
# Revenue
# ---------------------------------------------------------------------------
def test_estimate_revenue_none_when_sales_none():
    r = revenue_estimator.estimate_revenue(None, 100.0)
    assert r["estimated_revenue"] is None
    assert r["is_estimated"] is True


def test_estimate_revenue_multiplies():
    r = revenue_estimator.estimate_revenue(50, 200.0)
    assert r["estimated_revenue"] == 10000


def test_average_price():
    sellers = [{"price": 100}, {"price": 200}, {"price": None}]
    assert revenue_estimator.calculate_average_price(sellers) == 150.0
    assert revenue_estimator.calculate_average_price([]) is None


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------
def _snap(days_ago, signal):
    ts = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)).isoformat()
    return {"timestamp": ts, "sales_signal": signal, "price": 100, "rating": 4.0}


def test_trend_up():
    trend = trend_analyzer.analyze_trend([_snap(10, 100), _snap(0, 300)])
    assert trend["direction"] == "up"
    assert trend["percent_change"] > 0


def test_trend_flat():
    trend = trend_analyzer.analyze_trend([_snap(10, 100), _snap(0, 101)])
    assert trend["direction"] == "flat"


def test_trend_down():
    trend = trend_analyzer.analyze_trend([_snap(10, 300), _snap(0, 100)])
    assert trend["direction"] == "down"


def test_weekly_aggregates():
    snaps = [_snap(0, 100), _snap(1, 120), _snap(7, 80), _snap(8, 90)]
    weeks = trend_analyzer.calculate_weekly_aggregates(snaps)
    assert isinstance(weeks, list)
    assert all("week" in w for w in weeks)


# ---------------------------------------------------------------------------
# End-to-end: search service populates DB + analytics
# ---------------------------------------------------------------------------
def test_search_service_end_to_end():
    results = search_service.execute_search("earbuds", use_cache=False)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    # Enriched fields present.
    assert first["id"] is not None
    assert "demand_score" in first
    assert "demand_label" in first
    assert "estimate_7d_sales" in first
    assert 0 <= first["demand_score"] <= 100
    # Product persisted.
    prod = product_repository.get_product_by_id(first["id"])
    assert prod is not None
    # Snapshot recorded.
    assert snapshot_repository.get_snapshot_count(first["id"]) >= 1


def test_search_cache_hit():
    first = search_service.execute_search("lamp", use_cache=True)
    second = search_service.execute_search("lamp", use_cache=True)
    assert first == second


def test_full_analytics_assembles():
    results = search_service.execute_search("watch", use_cache=False)
    assert results
    product = product_repository.get_product_by_id(results[0]["id"])
    full = analytics_service.get_full_product_analytics(product)
    assert "estimates" in full and "demand" in full and "trend" in full
    assert full["demand"]["score"] is not None
