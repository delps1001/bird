from __future__ import annotations

import sqlite3

import pytest

from bird_listener.persistence.schema import init_db


@pytest.fixture
def db() -> sqlite3.Connection:
    """In-memory SQLite database with schema applied."""
    conn = init_db(":memory:")
    yield conn
    conn.close()
