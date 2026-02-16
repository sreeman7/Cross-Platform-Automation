"""Video CRUD and statistics endpoints."""

from collections import Counter
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.video import Video
from app.schemas.video import StatsSummary, VideoCreate, VideoListItem, VideoResponse, VideoUpdate
from app.workers.tasks import process_pipeline_task

router = APIRouter(prefix="/api", tags=["videos"])
logger = logging.getLogger(__name__)


@router.post("/videos/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
def create_video(payload: VideoCreate, db: Session = Depends(get_db)) -> Video:
    """Create a video record and queue async processing."""

    video = Video(instagram_url=str(payload.instagram_url), status="pending")
    db.add(video)
    db.commit()
    db.refresh(video)

    try:
        task = process_pipeline_task.delay(video.id)
        _ = task.id
        video.error_message = None
    except Exception as exc:
        logger.warning("Could not enqueue Celery task for video_id=%s: %s", video.id, exc)
        video.error_message = "Queued in DB, but task broker unavailable. Start Redis/Celery and retry."

    db.add(video)
    db.commit()

    return video


@router.get("/videos/", response_model=list[VideoListItem])
def list_videos(
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[Video]:
    """List videos with optional status filtering and pagination."""

    query = db.query(Video)
    if status:
        query = query.filter(Video.status == status)
    return query.order_by(Video.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)) -> Video:
    """Return a specific video record by id."""

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.patch("/videos/{video_id}", response_model=VideoResponse)
def update_video(video_id: int, payload: VideoUpdate, db: Session = Depends(get_db)) -> Video:
    """Update editable fields on a video record."""

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    if payload.caption is not None:
        video.caption = payload.caption
    if payload.hashtags is not None:
        video.hashtags = payload.hashtags

    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.delete("/videos/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete a video record by id."""

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    db.delete(video)
    db.commit()
    return {"message": "Video deleted successfully"}


@router.get("/stats/summary", response_model=StatsSummary)
def get_stats_summary(db: Session = Depends(get_db)) -> StatsSummary:
    """Return aggregate counts by processing state."""

    statuses = [row[0] for row in db.query(Video.status).all()]
    counter = Counter(statuses)

    return StatsSummary(
        total_videos=len(statuses),
        pending=counter.get("pending", 0),
        downloading=counter.get("downloading", 0),
        processing=counter.get("processing", 0),
        uploading=counter.get("uploading", 0),
        completed=counter.get("completed", 0),
        failed=counter.get("failed", 0),
    )
