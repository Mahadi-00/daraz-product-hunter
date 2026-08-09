"""Central configuration.

All values that control *how the system behaves* live here: database location,
request timeouts, how many products to fetch, which endpoints to use, etc.
There is deliberately NO business logic in this module -- only values.

Values are read from environment variables (or the optional ``.env`` file)
with sensible defaults applied when the variable is absent.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional at import time
    pass


# --------------------------------------------------------------------------
# Project root helpers
# --------------------------------------------------------------------------
def get_project_root() -> Path:
    """Absolute path to the project root (one level above this file)."""
    return Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------
def get_database_path() -> Path:
    """Absolute path to the SQLite file, independent of the CWD."""
    configured = os.getenv("DATABASE_PATH", "data/daraz_hunter.db")
    p = Path(configured)
    if p.is_absolute():
        return p
    return get_project_root() / p


# --------------------------------------------------------------------------
# Data source / API
# --------------------------------------------------------------------------
def get_source_mode() -> str:
    """Return ``"mock"`` or ``"http"`` depending on configuration."""
    mode = os.getenv("DARAZ_SOURCE_MODE", "mock").strip().lower()
    return mode if mode in ("mock", "http") else "mock"


def get_api_config() -> dict:
    """Return a dict with data-source connection details.

    Sensitive values (like an API key) come from the environment so they are
    never hard-coded or committed. Non-sensitive values have defaults.
    """
    return {
        "mode": get_source_mode(),
        "base_url": os.getenv("DARAZ_BASE_URL", "https://www.daraz.pk").rstrip("/"),
        "api_key": os.getenv("DARAZ_API_KEY", ""),
        "timeout": int(os.getenv("DARAZ_REQUEST_TIMEOUT", "10")),
        "max_results": int(os.getenv("DARAZ_MAX_RESULTS", "20")),
    }


# --------------------------------------------------------------------------
# Rate limiting
# --------------------------------------------------------------------------
def get_rate_limit_per_minute() -> int:
    """Maximum number of outbound requests allowed per minute."""
    return int(os.getenv("DARAZ_RATE_LIMIT_PER_MINUTE", "15"))


# --------------------------------------------------------------------------
# Caching
# --------------------------------------------------------------------------
def get_cache_ttl_seconds() -> int:
    """How long a search result may be served from the in-memory cache."""
    return int(os.getenv("CACHE_TTL_MINUTES", "10")) * 60


# --------------------------------------------------------------------------
# Snapshots / history
# --------------------------------------------------------------------------
def get_snapshot_retention_days() -> int:
    """Raw daily snapshots older than this are pruned during cleanup."""
    return int(os.getenv("SNAPSHOT_RETENTION_DAYS", "90"))


def is_auto_snapshot_enabled() -> bool:
    return os.getenv("AUTO_SNAPSHOT_ENABLED", "false").lower() == "true"


def get_auto_snapshot_interval_hours() -> int:
    return int(os.getenv("AUTO_SNAPSHOT_INTERVAL_HOURS", "24"))
