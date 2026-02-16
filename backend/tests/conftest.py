"""Pytest configuration for deterministic local test behavior."""

import os
from pathlib import Path

# Ensure tests run against local SQLite instead of external Supabase.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'test.db'}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("TIKTOK_MOCK_MODE", "True")
os.environ.setdefault("OPENAI_API_KEY", "")
