"""Tests for analytics/sales_estimator.py."""
from __future__ import annotations

import datetime as dt

from analytics import sales_estimator


def _snap(days_ago: int, signal: int, price=100):
    ts = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)).isoformat()
    return {"timestamp": ts, "sales_signal": signal, "price": price}


def test_estimate_returns_none_with_insufficient_snapshots():
    result = sales_estimator.estimate_sales([_snap(0, 100)], 7)
    assert result["estimated_sales"] is None
    assert result["confidence"] == "low"
    assert result["is_estimated"] is True


def test_estimate_measures_direct_change_within_period():
    # 100 sold 5 days ago, 220 sold now -> 120 sold in 5 days.
    snaps = [_snap(5, 100), _snap(0, 220)]
    result = sales_estimator.estimate_sales(snaps, 7)
    assert result["estimated_sales"] is not None
    # Measured change = 120, extrapolated to 7 days = 168.
    assert result["estimated_sales"] == 168
    assert result["is_extrapolated"] is True


def test_estimate_full_window_no_extrapolation():
    # Data spans 10 days, full 7-day window available.
    snaps = [_snap(10, 100), _snap(0, 250)]
    result = sales_estimator.estimate_sales(snaps, 7)
    assert result["estimated_sales"] == 150
    assert result["is_extrapolated"] is False


def test_negative_signal_change_is_none():
    # Signal dropped -> can't be a meaningful positive sales figure.
    snaps = [_snap(3, 500), _snap(0, 400)]
    assert sales_estimator.estimate_sales(snaps, 7)["estimated_sales"] is None


def test_extrapolate_to_period():
    assert sales_estimator.extrapolate_to_period(100, 5, 10) == 200
    assert sales_estimator.extrapolate_to_period(100, 10, 7) == 70


def test_confidence_levels():
    # Many snapshots + wide span -> high confidence.
    snaps = [_snap(30 - i, 100 + i * 5) for i in range(20)]
    assert sales_estimator.estimate_sales(snaps, 7)["confidence"] == "high"
    # Few snapshots -> low confidence.
    assert sales_estimator.estimate_sales([_snap(2, 10), _snap(0, 20)], 7)["confidence"] == "low"
