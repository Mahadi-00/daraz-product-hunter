"""Tests for analytics/demand_scorer.py."""
from __future__ import annotations

from analytics import demand_scorer


def test_classify_demand_thresholds():
    assert demand_scorer.classify_demand(90)["key"] == "high"
    assert demand_scorer.classify_demand(80)["key"] == "high"
    assert demand_scorer.classify_demand(70)["key"] == "good"
    assert demand_scorer.classify_demand(50)["key"] == "average"
    assert demand_scorer.classify_demand(20)["key"] == "low"


def test_classify_demand_emojis():
    assert demand_scorer.classify_demand(85)["emoji"] == "🔥"
    assert demand_scorer.classify_demand(10)["emoji"] == "🔴"


def test_normalize_signal_bounds():
    assert demand_scorer.normalize_signal(10000, 0, 10000) == 100.0
    assert demand_scorer.normalize_signal(0, 0, 10000) == 0.0
    assert demand_scorer.normalize_signal(5000, 0, 10000) == 50.0
    assert demand_scorer.normalize_signal(None, 0, 10000) == 0.0


def test_price_competitiveness():
    assert demand_scorer.calculate_price_competitiveness_score(80, 100) > \
           demand_scorer.calculate_price_competitiveness_score(180, 100)


def test_demand_score_without_sales_is_partial_confidence():
    result = demand_scorer.calculate_demand_score(
        sales_velocity=None, review_count=5000, rating=4.5,
        competition_score=50, price_score=80)
    assert 0 <= result["score"] <= 100
    assert result["confidence"] == "partial"


def test_demand_score_with_sales_is_full_confidence():
    result = demand_scorer.calculate_demand_score(
        sales_velocity=50, review_count=5000, rating=4.5,
        competition_score=50, price_score=80)
    assert result["confidence"] == "full"
    assert result["classification"]["label"] in (
        "High Demand", "Good", "Average", "Low Demand")


def test_weights_present():
    result = demand_scorer.calculate_demand_score(10, 100, 4.0, 40, 60)
    assert abs(sum(result["weights"].values()) - 1.0) < 1e-9
