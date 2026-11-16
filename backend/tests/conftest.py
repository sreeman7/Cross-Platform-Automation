"""Pytest configuration for deterministic local test behavior."""

import os
from pathlib import Path

import pytest

# Tests must not inherit live credentials or authentication from backend/.env.
os.environ["DATABASE_URL"] = f"sqlite:///{Path(__file__).parent / 'test.db'}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TIKTOK_MOCK_MODE"] = "True"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ADMIN_PASSWORD"] = ""
os.environ["DEBUG"] = "True"
for key in (
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME",
    "R2_ENDPOINT_URL",
    "R2_PUBLIC_BASE_URL",
    "TIKTOK_CLIENT_KEY",
    "TIKTOK_CLIENT_SECRET",
    "INSTAGRAM_ACCESS_TOKEN",
):
    os.environ[key] = ""


@pytest.fixture(autouse=True)
def database_tables():
    """Create isolated SQLite tables for API tests before each test."""

    from app.database import Base, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
