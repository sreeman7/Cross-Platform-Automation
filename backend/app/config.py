"""Centralized application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration for API, DB, queue, and integrations."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Social Media Automation API"
    debug: bool = True
    secret_key: str = "change-me"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"

    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_endpoint_url: str = ""
    r2_public_base_url: str = ""
    r2_region: str = "auto"

    instagram_access_token: str = ""

    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_redirect_uri: str = "http://localhost:8000/auth/tiktok/callback"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: int = 30


settings = Settings()
