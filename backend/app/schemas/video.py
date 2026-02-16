"""Pydantic request/response schemas for video endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class VideoCreate(BaseModel):
    """Payload for creating a new video-processing request."""

    instagram_url: HttpUrl


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
