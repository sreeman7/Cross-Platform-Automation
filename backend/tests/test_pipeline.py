"""Pipeline and TikTok publishing tests without external services."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from celery.exceptions import Retry

from app.database import SessionLocal
from app.models.video import Job, Video
from app.services.tiktok_service import TikTokPublicationFailed, TikTokService, TikTokServiceError
from app.workers import tasks


def _video() -> int:
    """Create a video record for a worker test."""

    with SessionLocal() as db:
        video = Video(instagram_url="https://www.instagram.com/reel/ABC123/")
        db.add(video)
        db.commit()
        return video.id


def test_pipeline_prepares_review_without_publishing(monkeypatch, tmp_path: Path) -> None:
    """Processing prepares a review record but does not post to TikTok."""

    video_id = _video()

    async def download(_self, _url, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "source.mp4"
        path.write_bytes(b"video")
        return SimpleNamespace(video_path=path, media_id="123", caption="A hike in the Rockies")

    async def process(_self, source, output_dir):
        return source

    async def upload(_self, _path, _key):
        return "https://cdn.example/video.mp4"

    async def caption(_self, context_hint):
        assert context_hint == "A hike in the Rockies"
        return "A clip", ["#demo"]

    monkeypatch.setattr(tasks.InstagramService, "download_video_with_metadata", download)
    monkeypatch.setattr(tasks.VideoProcessor, "process_video", process)
    monkeypatch.setattr(tasks.StorageService, "upload_file", upload)
    monkeypatch.setattr(tasks.AIService, "generate_caption_and_tags", caption)
    monkeypatch.setattr(tasks.settings, "tiktok_mock_mode", True)

    result = tasks.process_pipeline_task.apply(args=[video_id], throw=True).get()
    assert result["status"] == "ready_for_review"
    with SessionLocal() as db:
        video = db.get(Video, video_id)
        assert video.status == "ready_for_review"
        assert video.tiktok_url is None
        assert video.tiktok_video_id is None
        assert video.storage_url == "https://cdn.example/video.mp4"
        assert video.instagram_media_id == "123"
        jobs = db.query(Job).filter(Job.video_id == video_id).all()
        assert len(jobs) == 5
        assert all(job.status == "completed" for job in jobs)


def test_publish_task_records_single_upload(monkeypatch) -> None:
    """Review approval leads to one upload and repeat execution is skipped."""

    video_id = _video()
    with SessionLocal() as db:
        video = db.get(Video, video_id)
        video.status = "publishing"
        video.storage_url = "https://cdn.example/video.mp4"
        video.caption = "Reviewed caption"
        video.hashtags = ["#approved"]
        db.commit()

    calls = []

    async def download(_self, _key, path):
        path.write_bytes(b"video")
        return path

    async def publish(_self, path, caption, db=None):
        calls.append(caption)
        return None, "publish-123"

    monkeypatch.setattr(tasks.StorageService, "download_file", download)
    monkeypatch.setattr(tasks.TikTokService, "upload_video", publish)
    monkeypatch.setattr(tasks.settings, "tiktok_mock_mode", True)

    result = tasks.publish_video_task.apply(args=[video_id], throw=True).get()
    assert result["status"] == "demo_completed"
    assert tasks.publish_video_task.apply(args=[video_id], throw=True).get()["status"] == "skipped"
    assert calls == ["Reviewed caption #approved"]
    with SessionLocal() as db:
        assert db.get(Video, video_id).tiktok_video_id == "publish-123"


def test_pipeline_records_failed_download(monkeypatch) -> None:
    """A failed stage leaves visible errors on the video and job records."""

    video_id = _video()

    async def fail(_self, _url, _output_dir):
        raise RuntimeError("download unavailable")

    monkeypatch.setattr(tasks.InstagramService, "download_video_with_metadata", fail)
    with pytest.raises(Retry):
        tasks.process_pipeline_task.apply(args=[video_id], throw=True).get()

    with SessionLocal() as db:
        video = db.get(Video, video_id)
        assert video.status == "failed"
        assert "download unavailable" in video.error_message
        jobs = db.query(Job).filter(Job.video_id == video_id).all()
        assert len(jobs) == 2
        assert all(job.status == "failed" for job in jobs)


def test_tiktok_token_exchange_uses_form_response(monkeypatch) -> None:
    """OAuth stores the access token returned at the top level by TikTok."""

    service = TikTokService()
    service.client_key = "key"
    service.client_secret = "secret"

    async def fake_form(_payload):
        return {"access_token": "access", "refresh_token": "refresh", "open_id": "user", "expires_in": 3600}

    monkeypatch.setattr(service, "_post_token_form", fake_form)
    with SessionLocal() as db:
        token = asyncio.run(service.exchange_code_for_token(db, "auth-code"))
        assert token.access_token == "access"
        assert token.refresh_token == "refresh"


def test_tiktok_status_returns_public_url_only_after_post(monkeypatch) -> None:
    """Publish status is separate from upload completion."""

    service = TikTokService()

    async def fake_token(_db):
        return "access"

    async def processing(_path, _payload, *, access_token=None):
        return {"data": {"status": "PROCESSING_UPLOAD"}, "error": {"code": "ok"}}

    monkeypatch.setattr(service, "get_valid_access_token", fake_token)
    monkeypatch.setattr(service, "_post_json", processing)
    with SessionLocal() as db:
        assert asyncio.run(service.fetch_publish_status(db, "publish-id")) == ("PROCESSING_UPLOAD", None)

        async def completed(_path, _payload, *, access_token=None):
            return {"data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": [123]}, "error": {"code": "ok"}}

        monkeypatch.setattr(service, "_post_json", completed)
        state, url = asyncio.run(service.fetch_publish_status(db, "publish-id"))
        assert state == "PUBLISH_COMPLETE"
        assert url is None

        async def failed(_path, _payload, *, access_token=None):
            return {"data": {"status": "FAILED", "fail_reason": "rejected"}, "error": {"code": "ok"}}

        monkeypatch.setattr(service, "_post_json", failed)
        with pytest.raises(TikTokServiceError, match="rejected"):
            asyncio.run(service.fetch_publish_status(db, "publish-id"))


def test_tiktok_creator_info_required_for_private_post(monkeypatch, tmp_path: Path) -> None:
    """Direct Post checks creator privacy options before initializing upload."""

    service = TikTokService()
    service.mock_mode = False
    source = tmp_path / "video.mp4"
    source.write_bytes(b"video")

    async def token(_db):
        return "access"

    async def creator(_token):
        return {"privacy_level_options": ["PUBLIC_TO_EVERYONE"]}

    monkeypatch.setattr(service, "get_valid_access_token", token)
    monkeypatch.setattr(service, "get_creator_info", creator)
    with SessionLocal() as db:
        with pytest.raises(TikTokServiceError, match="Private posting"):
            asyncio.run(service.upload_video(source, "caption", db=db))


def test_tiktok_upload_splits_large_video(monkeypatch, tmp_path: Path) -> None:
    """A video over 64 MB is streamed as valid sequential chunks."""

    source = tmp_path / "large.mp4"
    with source.open("wb") as output:
        output.truncate(64_000_001)
    service = TikTokService()
    service.mock_mode = False
    upload_ranges = []

    async def token(_db):
        return "access"

    async def creator(_token):
        return {"privacy_level_options": ["SELF_ONLY"]}

    async def init(_path, payload, *, access_token=None):
        assert payload["source_info"] == {
            "source": "FILE_UPLOAD",
            "video_size": 64_000_001,
            "chunk_size": 10_000_000,
            "total_chunk_count": 6,
        }
        return {"data": {"upload_url": "https://upload.example/video", "publish_id": "published-1"}}

    async def put(_url, chunk, start, total_size):
        upload_ranges.append((start, len(chunk), total_size))

    monkeypatch.setattr(service, "get_valid_access_token", token)
    monkeypatch.setattr(service, "get_creator_info", creator)
    monkeypatch.setattr(service, "_post_json", init)
    monkeypatch.setattr(service, "_put_bytes", put)

    with SessionLocal() as db:
        assert asyncio.run(service.upload_video(source, "caption", db=db)) == (None, "published-1")
    assert upload_ranges == [
        (0, 10_000_000, 64_000_001),
        (10_000_000, 10_000_000, 64_000_001),
        (20_000_000, 10_000_000, 64_000_001),
        (30_000_000, 10_000_000, 64_000_001),
        (40_000_000, 10_000_000, 64_000_001),
        (50_000_000, 14_000_001, 64_000_001),
    ]


def test_tiktok_upload_rejects_empty_video() -> None:
    """Empty uploads fail before requesting a TikTok upload URL."""

    with pytest.raises(TikTokServiceError, match="empty"):
        TikTokService._chunk_sizes(0)
    assert TikTokService._chunk_sizes(4_000_000) == [4_000_000]
