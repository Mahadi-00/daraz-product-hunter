"""Simple in-memory time-to-live cache.

Used to serve repeat searches for the same keyword quickly without re-hitting
the external data source. Thread-safe via a lock. Values are best-effort and
evicted by time, so correctness never depends on this cache.
"""
from __future__ import annotations

import threading
import time
from typing import Any

from config import settings

_cache: dict[str, tuple[float, Any]] = {}
_lock = threading.Lock()


def get(key: str) -> Any | None:
    """Return a cached value if present and not expired, else None."""
    with _lock:
        item = _cache.get(key)
        if item is None:
            return None
        ts, value = item
        ttl = settings.get_cache_ttl_seconds()
        if time.time() - ts > ttl:
            _cache.pop(key, None)
            return None
        return value


def set(key: str, value: Any) -> None:
    """Store a value with the configured TTL."""
    with _lock:
        _cache[key] = (time.time(), value)


def delete(key: str) -> None:
    with _lock:
        _cache.pop(key, None)


def clear() -> None:
    with _lock:
        _cache.clear()


def cache_key(keyword: str, filters: dict | None = None) -> str:
    """Build a stable cache key from a keyword and optional filter snapshot."""
    if filters:
        flat = ",".join(f"{k}={v}" for k, v in sorted(filters.items()))
        return f"{keyword.lower().strip()}|{flat}"
    return keyword.lower().strip()
