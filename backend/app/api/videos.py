"""Video CRUD and statistics endpoints."""

from collections import Counter
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.video import Job, Video
from app.schemas.video import JobResponse, StatsSummary, VideoCreate, VideoListItem, VideoResponse, VideoUpdate
from app.workers.tasks import process_pipeline_task, publish_video_task
from app.services.tiktok_service import TikTokService, TikTokServiceError

router = APIRouter(prefix="/api", tags=["videos"])
logger = logging.getLogger(__name__)


@router.post("/videos/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
def create_video(payload: VideoCreate, db: Session = Depends(get_db)) -> Video:
    """Create a video record and queue async processing."""

    video = Video(instagram_url=str(payload.instagram_url), status="pending")
    db.add(video)
    db.commit()
    db.refresh(video)

    job = Job(video_id=video.id, task_type="process_pipeline", status="pending")
    db.add(job)
    db.commit()

    try:
        task = process_pipeline_task.delay(video.id)
        job.celery_task_id = task.id
        video.error_message = None
    except Exception as exc:
        logger.warning("Could not enqueue Celery task for video_id=%s: %s", video.id, exc)
        video.status = "failed"
        video.error_message = "Task queue unavailable. Please try again later."
        job.status = "failed"
        job.error_message = video.error_message
        db.add(job)
        db.add(video)
        db.commit()
        raise HTTPException(status_code=503, detail=video.error_message) from exc

    db.add(job)
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


@router.get("/videos/{video_id}/jobs", response_model=list[JobResponse])
def get_video_jobs(video_id: int, db: Session = Depends(get_db)) -> list[Job]:
    """Return all background jobs associated with a video."""

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    return db.query(Job).filter(Job.video_id == video_id).order_by(Job.id.asc()).all()


@router.post("/videos/{video_id}/approve", response_model=VideoResponse)
def approve_video(video_id: int, db: Session = Depends(get_db)) -> Video:
    """Queue TikTok upload only after explicit creator approval."""

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != "ready_for_review" or video.tiktok_video_id:
        raise HTTPException(status_code=409, detail="Video is not ready for approval")
    if not video.storage_url or not video.caption:
        raise HTTPException(status_code=409, detail="Processed video and caption are required")

    video.status = "publishing"
    db.commit()
    try:
        publish_video_task.delay(video_id)
    except Exception as exc:
        video.status = "ready_for_review"
        db.commit()
        logger.exception("Could not enqueue TikTok publication for video_id=%s", video_id)
        raise HTTPException(status_code=503, detail="Task queue unavailable") from exc
    db.refresh(video)
    return video


@router.post("/videos/{video_id}/check-publication", response_model=VideoResponse)
def check_publication(video_id: int, db: Session = Depends(get_db)) -> Video:
    """Refresh TikTok publication status after a successful upload."""

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != "publishing" or not video.tiktok_video_id:
        raise HTTPException(status_code=409, detail="Video is not awaiting TikTok publication")
    try:
        publication_status, public_url = asyncio.run(
            TikTokService().fetch_publish_status(db, video.tiktok_video_id)
        )
    except TikTokServiceError as exc:
        video.status = "failed"
        video.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail="TikTok publishing failed") from exc
    if publication_status == "PUBLISH_COMPLETE":
        video.status = "completed"
        video.tiktok_url = public_url
        db.commit()
        db.refresh(video)
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
        ready_for_review=counter.get("ready_for_review", 0),
        publishing=counter.get("publishing", 0) + counter.get("publishing_in_progress", 0),
        completed=counter.get("completed", 0),
        demo_completed=counter.get("demo_completed", 0),
        failed=counter.get("failed", 0),
    )
