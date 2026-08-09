"""Shared pytest fixtures.

Ensures tests run against an isolated, disposable SQLite database so they
never touch real data.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path, monkeypatch):
    """Point the database at a temp file for every test."""
    import config.settings as settings
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))

    # Force a fresh connection on the new path.
    from database import connection
    connection.close_connection()
    yield
    connection.close_connection()


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch):
    """Force mock data source for all tests."""
    monkeypatch.setenv("DARAZ_SOURCE_MODE", "mock")
    from integrations.daraz_client import reset_client
    reset_client()
