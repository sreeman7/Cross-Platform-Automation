"""Pydantic request/response schemas for video endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class VideoCreate(BaseModel):
    """Payload for creating a new video-processing request."""

    instagram_url: HttpUrl

    @field_validator("instagram_url")
    @classmethod
    def validate_instagram_url(cls, value: HttpUrl) -> HttpUrl:
        """Restrict submissions to supported Instagram media URLs."""

        if "instagram.com" not in value.host:
            raise ValueError("URL must be on instagram.com")

        parts = [part for part in value.path.split("/") if part]
        if len(parts) < 2 or parts[0] not in {"reel", "p", "tv"}:
            raise ValueError("URL must be an Instagram reel/post/tv link")

        return value


class VideoUpdate(BaseModel):
    """Partial update payload for editable video fields."""

    caption: str | None = Field(default=None, max_length=2200)
    hashtags: list[str] | None = None


class VideoResponse(BaseModel):
    """Detailed API response for a single video."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    instagram_url: str
    instagram_media_id: str | None
    tiktok_url: str | None
    tiktok_video_id: str | None
    storage_url: str | None
    local_path: str | None
    caption: str | None
    hashtags: list[str] | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class VideoListItem(BaseModel):
    """Compact response model for list endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    instagram_url: str
    tiktok_url: str | None
    status: str
    caption: str | None
    hashtags: list[str] | None
    created_at: datetime


class StatsSummary(BaseModel):
    """Aggregate dashboard counters for processing states."""

    total_videos: int
    pending: int
    downloading: int
    processing: int
    uploading: int
    completed: int
    failed: int


class JobResponse(BaseModel):
    """Response model for background job tracking records."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    celery_task_id: str | None
    task_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
