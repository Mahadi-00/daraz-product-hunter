"""Formatting helpers: numbers, currency, dates.

Kept free of any I/O so any layer can import and use them safely.
"""
from __future__ import annotations

import datetime as dt

_ESTIMATED_PREFIX = "Est."


def format_price(value) -> str:
    """Format a number as a Pakistani Rupee string, e.g. ``Rs. 2,499``."""
    if value is None:
        return "—"
    try:
        num = int(round(float(value)))
    except (TypeError, ValueError):
        return "—"
    return f"Rs. {num:,}"


def format_number(value) -> str:
    """Format a plain integer with thousands separators."""
    if value is None:
        return "—"
    try:
        num = int(round(float(value)))
    except (TypeError, ValueError):
        return "—"
    return f"{num:,}"


def format_rating(value) -> str:
    if value is None:
        return "—"
    return f"{float(value):.1f}"


def format_percent(value) -> str:
    """Format a signed percentage, e.g. ``+12.4%`` or ``-3.1%``."""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


def format_estimated_sales(value) -> str:
    """Render an estimated sales figure with an explicit ``Est.`` prefix.

    An honest, always-labeled estimate. Returns ``"Not enough data yet"``
    when the estimate is None rather than inventing a number.
    """
    if value is None:
        return "Not enough data yet"
    return f"{_ESTIMATED_PREFIX} {format_number(value)}"


def format_timestamp(ts) -> str:
    """Format a timestamp (datetime/str) as ``YYYY-MM-DD HH:MM``."""
    if isinstance(ts, str):
        try:
            ts = dt.datetime.fromisoformat(ts)
        except ValueError:
            return ts
    if isinstance(ts, dt.datetime):
        return ts.strftime("%Y-%m-%d %H:%M")
    return str(ts)


def is_estimated(value) -> bool:
    """Return True if a displayed figure is an estimate (starts with 'Est.')."""
    return isinstance(value, str) and value.startswith(_ESTIMATED_PREFIX)
