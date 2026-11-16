"""Pytest configuration for deterministic local test behavior."""

import os
from pathlib import Path

import pytest

# Ensure tests run against local SQLite instead of external Supabase.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'test.db'}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("TIKTOK_MOCK_MODE", "True")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("DEBUG", "True")


@pytest.fixture(autouse=True)
def database_tables():
    """Create isolated SQLite tables for API tests before each test."""

    from app.database import Base, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
