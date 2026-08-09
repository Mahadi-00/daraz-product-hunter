"""Controls outbound request frequency.

Sending hundreds of requests per second to any data source is irresponsible
and likely to get the app blocked. This module records request timestamps and
introduces delays when requests are being made too quickly. It is a no-op when
the per-minute limit is configured high/unlimited.
"""
from __future__ import annotations

import threading
import time

from config import settings
from utils.logger import get_logger

log = get_logger("integrations.rate_limiter")

_lock = threading.Lock()
_last_request_ts: float | None = None


def get_min_interval_seconds() -> float:
    """Minimum seconds that must elapse between outbound requests."""
    per_minute = settings.get_rate_limit_per_minute()
    if per_minute <= 0:
        return 0.0
    return 60.0 / per_minute


def wait_if_needed() -> None:
    """Sleep as needed to respect the rate limit. Call before every request."""
    global _last_request_ts
    interval = get_min_interval_seconds()
    if interval <= 0:
        return
    with _lock:
        if _last_request_ts is not None:
            elapsed = time.monotonic() - _last_request_ts
            wait = interval - elapsed
            if wait > 0:
                time.sleep(wait)
        # Mark now as the start of the next window so concurrent callers wait.
        _last_request_ts = time.monotonic()


def record_request() -> None:
    """Record the timestamp of a completed request."""
    global _last_request_ts
    with _lock:
        _last_request_ts = time.monotonic()


def reset() -> None:
    """Clear rate-limit state (used by tests)."""
    global _last_request_ts
    with _lock:
        _last_request_ts = None
