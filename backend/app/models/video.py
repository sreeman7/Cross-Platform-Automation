"""ORM models for videos and background jobs."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Video(Base):
    """Represents a user-submitted Instagram reel and its processing lifecycle."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    instagram_url: Mapped[str] = mapped_column(String(500), nullable=False)
    instagram_media_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    tiktok_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tiktok_video_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    storage_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    jobs: Mapped[list["Job"]] = relationship(back_populates="video", cascade="all, delete-orphan")


class Job(Base):
    """Tracks each task execution linked to a video record."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    video: Mapped[Video] = relationship(back_populates="jobs")
