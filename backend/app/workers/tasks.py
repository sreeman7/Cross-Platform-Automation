"""Celery tasks for asynchronous video processing."""

from __future__ import annotations

import asyncio
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


def _set_video_status(db, video: Video, status: str, error_message: str | None = None) -> None:
    """Persist a video status transition."""

    video.status = status
    video.error_message = error_message
    video.updated_at = datetime.utcnow()
    db.add(video)
    db.commit()
    db.refresh(video)


def _start_job(
    db,
    *,
    video_id: int,
    task_type: str,
    celery_task_id: str | None,
) -> Job:
    """Create and persist a started job record."""

    job = Job(
        video_id=video_id,
        celery_task_id=celery_task_id,
        task_type=task_type,
        status="started",
        started_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _complete_job(db, job: Job) -> None:
    """Mark a job as completed."""

    job.status = "completed"
    job.completed_at = datetime.utcnow()
    db.add(job)
    db.commit()


def _fail_job(db, job: Job | None, error_message: str) -> None:
    """Mark a job as failed when available."""

    if not job:
        return
    job.status = "failed"
    job.error_message = error_message
    job.completed_at = datetime.utcnow()
    db.add(job)
    db.commit()


def _run_download_step(
    db,
    *,
    video: Video,
    output_dir: Path,
    celery_task_id: str | None,
) -> Path:
    """Download media from Instagram and persist media metadata."""

    step_job = _start_job(
        db,
        video_id=video.id,
        task_type="download_video",
        celery_task_id=celery_task_id,
    )
    try:
        _set_video_status(db, video, "downloading")
        service = InstagramService()
        result = asyncio.run(service.download_video_with_metadata(video.instagram_url, output_dir))

        video.local_path = str(result.video_path)
        video.instagram_media_id = result.media_id
        db.add(video)
        db.commit()

        _complete_job(db, step_job)
        return result.video_path
    except Exception as exc:
        _fail_job(db, step_job, str(exc))
        raise


def _run_process_step(
    db,
    *,
    video: Video,
    source_path: Path,
    output_dir: Path,
    celery_task_id: str | None,
) -> Path:
    """Process downloaded media with FFmpeg wrapper service."""

    step_job = _start_job(
        db,
        video_id=video.id,
        task_type="process_video",
        celery_task_id=celery_task_id,
    )
    try:
        _set_video_status(db, video, "processing")
        processor = VideoProcessor()
        processed_path = asyncio.run(processor.process_video(source_path, output_dir))
        video.local_path = str(processed_path)
        db.add(video)
        db.commit()

        _complete_job(db, step_job)
        return processed_path
    except Exception as exc:
        _fail_job(db, step_job, str(exc))
        raise


def _run_upload_step(
    db,
    *,
    video: Video,
    source_path: Path,
    celery_task_id: str | None,
) -> str:
    """Upload processed media to object storage and persist URL."""

    step_job = _start_job(
        db,
        video_id=video.id,
        task_type="upload_storage",
        celery_task_id=celery_task_id,
    )
    try:
        _set_video_status(db, video, "uploading")
        storage_key = f"videos/{video.id}/processed.mp4"
        storage_service = StorageService()
        storage_url = asyncio.run(storage_service.upload_file(source_path, storage_key))
        video.storage_url = storage_url
        db.add(video)
        db.commit()

        _complete_job(db, step_job)
        return storage_url
    except Exception as exc:
        _fail_job(db, step_job, str(exc))
        raise


def _run_caption_and_publish_step(
    db,
    *,
    video: Video,
    source_path: Path,
    celery_task_id: str | None,
) -> None:
    """Generate caption/hashtags and upload processed media to TikTok."""

    caption_job = _start_job(
        db,
        video_id=video.id,
        task_type="generate_caption",
        celery_task_id=celery_task_id,
    )
    tiktok_job: Job | None = None

    try:
        ai_service = AIService()
        caption, hashtags = asyncio.run(ai_service.generate_caption_and_tags(context_hint=video.instagram_url))

        video.caption = caption
        video.hashtags = hashtags
        db.add(video)
        db.commit()

        _complete_job(db, caption_job)

        tiktok_job = _start_job(
            db,
            video_id=video.id,
            task_type="upload_tiktok",
            celery_task_id=celery_task_id,
        )
        tiktok_service = TikTokService()
        tiktok_url, tiktok_video_id = asyncio.run(tiktok_service.upload_video(source_path, caption, db=db))

        video.tiktok_url = tiktok_url
        video.tiktok_video_id = tiktok_video_id
        db.add(video)
        db.commit()

        _complete_job(db, tiktok_job)
    except Exception as exc:
        if tiktok_job is None:
            _fail_job(db, caption_job, str(exc))
        else:
            _fail_job(db, tiktok_job, str(exc))
        raise


@celery_app.task(bind=True, base=BaseTaskWithRetry, name="app.workers.tasks.download_video_task")
def download_video_task(
    self: BaseTaskWithRetry,
    video_id: int,
    output_dir: str | None = None,
) -> dict[str, str | int | None]:
    """Standalone task for downloading Instagram videos."""

    db = SessionLocal()
    step_job: Job | None = None
    try:
        video = db.get(Video, video_id)
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        step_job = _start_job(
            db,
            video_id=video_id,
            task_type="download_video",
            celery_task_id=self.request.id,
        )

        target_dir = Path(output_dir) if output_dir else Path("/tmp") / f"video_{video_id}"
        _set_video_status(db, video, "downloading")

        service = InstagramService()
        result = asyncio.run(service.download_video_with_metadata(video.instagram_url, target_dir))

        video.local_path = str(result.video_path)
        video.instagram_media_id = result.media_id
        db.add(video)
        db.commit()

        _complete_job(db, step_job)
        return {
            "video_id": video_id,
            "source_path": str(result.video_path),
            "instagram_media_id": result.media_id,
        }
    except Exception as exc:
        logger.exception("download_video_task failed for video_id=%s", video_id)
        video = db.get(Video, video_id)
        if video:
            _set_video_status(db, video, "failed", str(exc))
        _fail_job(db, step_job, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(bind=True, base=BaseTaskWithRetry, name="app.workers.tasks.upload_to_storage_task")
def upload_to_storage_task(
    self: BaseTaskWithRetry,
    video_id: int,
    source_path: str,
) -> dict[str, str | int]:
    """Standalone task for uploading processed media to cloud storage."""

    db = SessionLocal()
    step_job: Job | None = None
    try:
        video = db.get(Video, video_id)
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        step_job = _start_job(
            db,
            video_id=video_id,
            task_type="upload_storage",
            celery_task_id=self.request.id,
        )

        _set_video_status(db, video, "uploading")
        storage_service = StorageService()
        storage_key = f"videos/{video_id}/processed.mp4"
        storage_url = asyncio.run(storage_service.upload_file(Path(source_path), storage_key))

        video.storage_url = storage_url
        db.add(video)
        db.commit()

        _complete_job(db, step_job)
        return {"video_id": video_id, "storage_url": storage_url}
    except Exception as exc:
        logger.exception("upload_to_storage_task failed for video_id=%s", video_id)
        video = db.get(Video, video_id)
        if video:
            _set_video_status(db, video, "failed", str(exc))
        _fail_job(db, step_job, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(bind=True, base=BaseTaskWithRetry, name="app.workers.tasks.process_pipeline_task")
def process_pipeline_task(self: BaseTaskWithRetry, video_id: int) -> dict[str, str | int]:
    """Orchestrate full async pipeline with per-step job tracking."""

    db = SessionLocal()
    pipeline_job: Job | None = None
    try:
        video = db.get(Video, video_id)
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        pending_pipeline_job = (
            db.query(Job)
            .filter(
                Job.video_id == video_id,
                Job.task_type == "process_pipeline",
                Job.celery_task_id == self.request.id,
                Job.status == "pending",
            )
            .order_by(Job.id.desc())
            .first()
        )

        if pending_pipeline_job:
            pending_pipeline_job.status = "started"
            pending_pipeline_job.started_at = datetime.utcnow()
            db.add(pending_pipeline_job)
            db.commit()
            db.refresh(pending_pipeline_job)
            pipeline_job = pending_pipeline_job
        else:
            pipeline_job = _start_job(
                db,
                video_id=video_id,
                task_type="process_pipeline",
                celery_task_id=self.request.id,
            )

        with TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp) / str(video_id)
            source_path = _run_download_step(
                db,
                video=video,
                output_dir=tmp_dir,
                celery_task_id=self.request.id,
            )
            processed_path = _run_process_step(
                db,
                video=video,
                source_path=source_path,
                output_dir=tmp_dir,
                celery_task_id=self.request.id,
            )
            _run_upload_step(
                db,
                video=video,
                source_path=processed_path,
                celery_task_id=self.request.id,
            )
            _run_caption_and_publish_step(
                db,
                video=video,
                source_path=processed_path,
                celery_task_id=self.request.id,
            )

        _set_video_status(db, video, "completed")
        _complete_job(db, pipeline_job)

        return {"video_id": video_id, "status": "completed"}

    except Exception as exc:
        logger.exception("Pipeline task failed for video_id=%s", video_id)

        video = db.get(Video, video_id)
        if video:
            _set_video_status(db, video, "failed", str(exc))

        _fail_job(db, pipeline_job, str(exc))
        raise
    finally:
        db.close()
