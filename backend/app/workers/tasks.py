"""Celery tasks for asynchronous video processing."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from celery import Task

from app.database import SessionLocal
from app.models.video import Job, Video
from app.services.ai_service import AIService
from app.services.instagram_service import InstagramService
from app.services.storage_service import StorageService
from app.services.tiktok_service import TikTokService
from app.services.video_processor import VideoProcessor
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class BaseTaskWithRetry(Task):
    """Celery task base class with retry defaults."""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_kwargs = {"max_retries": 3}


def _update_video_status(db, video: Video, status: str, error_message: str | None = None) -> None:
    """Update video status and optional error field."""

    video.status = status
    video.error_message = error_message
    video.updated_at = datetime.utcnow()
    db.add(video)
    db.commit()
    db.refresh(video)


@celery_app.task(bind=True, base=BaseTaskWithRetry, name="app.workers.tasks.process_pipeline_task")
def process_pipeline_task(self: BaseTaskWithRetry, video_id: int) -> dict[str, str | int]:
    """Run full pipeline: download, process, upload storage, caption, upload TikTok."""

    db = SessionLocal()
    try:
        video = db.get(Video, video_id)
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        job = Job(
            video_id=video_id,
            celery_task_id=self.request.id,
            task_type="process_pipeline",
            status="started",
            started_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        instagram_service = InstagramService()
        processor = VideoProcessor()
        storage_service = StorageService()
        ai_service = AIService()
        tiktok_service = TikTokService()

        with TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)

            _update_video_status(db, video, "downloading")
            source_path = __import__("asyncio").run(
                instagram_service.download_video(video.instagram_url, tmp_dir / str(video_id))
            )

            _update_video_status(db, video, "processing")
            processed_path = __import__("asyncio").run(
                processor.process_video(source_path, tmp_dir / str(video_id))
            )
            video.local_path = str(processed_path)
            db.add(video)
            db.commit()

            _update_video_status(db, video, "uploading")
            storage_key = f"videos/{video_id}/processed.mp4"
            storage_url = __import__("asyncio").run(storage_service.upload_file(processed_path, storage_key))
            video.storage_url = storage_url

            caption, hashtags = __import__("asyncio").run(
                ai_service.generate_caption_and_tags(context_hint=video.instagram_url)
            )
            video.caption = caption
            video.hashtags = hashtags

            tiktok_url, tiktok_video_id = __import__("asyncio").run(
                tiktok_service.upload_video(processed_path, caption)
            )
            video.tiktok_url = tiktok_url
            video.tiktok_video_id = tiktok_video_id
            db.add(video)
            db.commit()

        _update_video_status(db, video, "completed")
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.add(job)
        db.commit()

        return {"video_id": video_id, "status": "completed"}

    except Exception as exc:
        logger.exception("Pipeline task failed for video_id=%s", video_id)

        video = db.get(Video, video_id)
        if video:
            _update_video_status(db, video, "failed", str(exc))

        db_job = (
            db.query(Job)
            .filter(Job.video_id == video_id, Job.celery_task_id == self.request.id)
            .order_by(Job.id.desc())
            .first()
        )
        if db_job:
            db_job.status = "failed"
            db_job.error_message = str(exc)
            db_job.completed_at = datetime.utcnow()
            db.add(db_job)
            db.commit()

        raise
    finally:
        db.close()
