"""Estimates 7-day and 30-day sales from a series of snapshots.

This module is deliberately careful: it *always* produces estimates, never
certainty. It returns context alongside every number (confidence, snapshot
count, time range covered, and whether it is extrapolated) so the UI can
present results honestly. If there are fewer than 2 snapshots it returns None
rather than inventing a figure.
"""
from __future__ import annotations

import datetime as dt

from config import constants

SUPPORTED_PERIODS = constants.ESTIMATE_PERIODS  # (7, 30)


def _parse_ts(ts) -> dt.datetime:
    if isinstance(ts, dt.datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=dt.timezone.utc)
        return ts
    return dt.datetime.fromisoformat(ts)


def _signal(snap: dict) -> int | None:
    return snap.get("sales_signal")


def estimate_sales(snapshots: list[dict], period_days: int) -> dict:
    """Estimate units sold over ``period_days`` from a snapshot series.

    Snapshots must be chronological (oldest first). Returns a dict with:
        - ``estimated_sales``: int or None
        - ``confidence``: 'high' | 'medium' | 'low'
        - ``snapshot_count``
        - ``days_covered``: actual span of the snapshot data
        - ``is_extrapolated``: bool (True when scaled from fewer days)
        - ``is_estimated``: always True
        - ``period_days``
    """
    snaps = [s for s in snapshots if _signal(s) is not None]
    base = {
        "estimated_sales": None,
        "confidence": "low",
        "snapshot_count": len(snaps),
        "days_covered": 0,
        "is_extrapolated": False,
        "is_estimated": True,
        "period_days": period_days,
    }
    if len(snaps) < 2:
        # Not enough data to estimate anything (architecture: no invented numbers).
        return base

    early, recent = snaps[0], snaps[-1]
    measured_change = calculate_signal_change(early, recent)
    if measured_change is None:
        return base

    measured_days = _days_between(_parse_ts(early.get("timestamp")),
                                  _parse_ts(recent.get("timestamp")))
    measured_days = max(measured_days, 1)
    base["days_covered"] = measured_days

    if measured_days >= period_days:
        # We have enough real data to measure the full window.
        estimated = measured_change
        is_extrapolated = False
    else:
        estimated = extrapolate_to_period(measured_change, measured_days, period_days)
        is_extrapolated = True

    base["estimated_sales"] = int(round(estimated))
    base["is_extrapolated"] = is_extrapolated
    base["confidence"] = _confidence(snapshot_count=len(snaps), days_covered=measured_days)
    return base


def calculate_signal_change(early_snapshot: dict, recent_snapshot: dict) -> int | None:
    """Difference in sales signal between two snapshots.

    Returns None if negative (can happen with data inconsistencies) because a
    negative "sales in a period" figure is meaningless -- we choose honesty
    over a misleading number.
    """
    early = _signal(early_snapshot)
    recent = _signal(recent_snapshot)
    if early is None or recent is None:
        return None
    delta = recent - early
    return delta if delta >= 0 else None


def extrapolate_to_period(measured_change: int, measured_days: int, target_days: int) -> int:
    """Scale a measured change proportionally to a longer target window.

    E.g. 5 days of data -> a 7-day estimate. The result is flagged as an
    extrapolation by the caller, never presented as a direct measurement.
    """
    if measured_days <= 0:
        return measured_change
    return int(round(measured_change * target_days / measured_days))


def _days_between(a: dt.datetime, b: dt.datetime) -> int:
    return max((b - a).total_seconds() / 86400.0, 0)


def _confidence(snapshot_count: int, days_covered: int) -> str:
    """Map data completeness to a confidence label (high/medium/low)."""
    if snapshot_count >= constants.MIN_SNAPSHOTS_HIGH_CONFIDENCE and \
            days_covered >= constants.MIN_DAYS_FOR_RELIABLE_ESTIMATE:
        return "high"
    if snapshot_count >= constants.MIN_SNAPSHOTS_MEDIUM_CONFIDENCE:
        return "medium"
    return "low"
