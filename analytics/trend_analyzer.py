"""Identifies trends from a snapshot time series.

Determines whether the sales signal is growing, flat, or declining, plus how
fast, and whether the movement is accelerating. Also groups snapshots into
weekly aggregates for charting.
"""
from __future__ import annotations

import datetime as dt

from config import constants


def _parse_ts(ts) -> dt.datetime:
    if isinstance(ts, dt.datetime):
        return ts.replace(tzinfo=dt.timezone.utc) if ts.tzinfo is None else ts
    return dt.datetime.fromisoformat(ts)


def analyze_trend(snapshots: list[dict]) -> dict:
    """Analyze the overall direction of change in a snapshot series.

    Snapshots should be chronological (oldest first). Returns trend direction
    ('up'/'flat'/'down'), percent change, per-day rate of change, and whether
    the change is accelerating or decelerating.
    """
    signals = [s.get("sales_signal") for s in snapshots if s.get("sales_signal") is not None]
    result = {
        "direction": "flat",
        "percent_change": 0.0,
        "rate_per_day": 0.0,
        "acceleration": "stable",
        "data_points": len(signals),
    }
    if len(signals) < 2:
        return result

    first, last = signals[0], signals[-1]
    if first == 0:
        percent = 0.0
    else:
        percent = (last - first) / first * 100.0

    try:
        days = max(_days_between(_parse_ts(snapshots[0]["timestamp"]),
                                 _parse_ts(snapshots[-1]["timestamp"])), 1)
    except (KeyError, ValueError):
        days = 1
    rate_per_day = (last - first) / days

    tol = constants.TREND_FLAT_TOLERANCE_PERCENT
    if percent > tol:
        direction = "up"
    elif percent < -tol:
        direction = "down"
    else:
        direction = "flat"

    # Acceleration: compare the second half change rate to the first half.
    acceleration = "stable"
    if len(signals) >= 4:
        half = len(signals) // 2
        first_half = signals[half] - signals[0]
        second_half = signals[-1] - signals[half]
        if second_half > first_half + 1:
            acceleration = "accelerating"
        elif second_half < first_half - 1:
            acceleration = "decelerating"

    return {
        "direction": direction,
        "percent_change": round(percent, 2),
        "rate_per_day": round(rate_per_day, 2),
        "acceleration": acceleration,
        "data_points": len(signals),
    }


def calculate_weekly_aggregates(snapshots: list[dict]) -> list[dict]:
    """Group snapshots by ISO week and compute weekly totals/averages.

    Returns a list of weekly points (oldest first) for charting.
    """
    weeks: dict[str, dict] = {}
    for s in snapshots:
        try:
            ts = _parse_ts(s["timestamp"])
        except (KeyError, ValueError):
            continue
        key = f"{ts.isocalendar()[0]}-W{ts.isocalendar()[1]:02d}"
        entry = weeks.setdefault(key, {
            "week": key,
            "start": ts.date().isoformat(),
            "sales_sum": 0,
            "price_sum": 0.0,
            "count": 0,
            "avg_rating_sum": 0.0,
        })
        entry["sales_sum"] += s.get("sales_signal") or 0
        if s.get("price") is not None:
            entry["price_sum"] += s["price"]
            entry["count"] += 1
        if s.get("rating") is not None:
            entry["avg_rating_sum"] += s["rating"]

    result = []
    for key in sorted(weeks):
        w = weeks[key]
        result.append({
            "week": key,
            "start": w["start"],
            "total_signal": w["sales_sum"],
            "avg_price": round(w["price_sum"] / w["count"], 2) if w["count"] else None,
            "avg_rating": round(w["avg_rating_sum"] / max(len([s for s in snapshots if _week_of(s) == key]), 1), 2),
        })
    return result


def _week_of(snapshot: dict) -> str:
    try:
        ts = _parse_ts(snapshot["timestamp"])
        return f"{ts.isocalendar()[0]}-W{ts.isocalendar()[1]:02d}"
    except (KeyError, ValueError):
        return ""


def _days_between(a: dt.datetime, b: dt.datetime) -> float:
    return (b - a).total_seconds() / 86400.0
