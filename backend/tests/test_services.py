"""Unit tests for service scaffolds."""

import asyncio
from pathlib import Path

from app.services.ai_service import AIService
from app.services.instagram_service import InstagramService
from app.services.storage_service import StorageService
from app.services.tiktok_service import TikTokService
from app.services.video_processor import VideoProcessor


def test_ai_service_generates_caption_and_tags() -> None:
    service = AIService()
    caption, tags = asyncio.run(service.generate_caption_and_tags("demo"))
    assert caption
    assert len(tags) >= 1


def test_video_processor_copies_file(tmp_path: Path) -> None:
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"video")
    processor = VideoProcessor()

    output = asyncio.run(processor.process_video(input_file, tmp_path / "processed"))
    assert output.exists()
    assert output.read_bytes() == b"video"


def test_storage_service_returns_url(tmp_path: Path) -> None:
    test_file = tmp_path / "clip.mp4"
    test_file.write_bytes(b"video")
    service = StorageService()

    url = asyncio.run(service.upload_file(test_file, "videos/1/clip.mp4"))
    assert url.startswith("http")


def test_instagram_and_tiktok_stubs(tmp_path: Path) -> None:
    instagram = InstagramService()
    tiktok = TikTokService()

    downloaded = asyncio.run(instagram.download_video("https://www.instagram.com/reel/ABC123/", tmp_path))
    assert downloaded.exists()

    tiktok_url, tiktok_id = asyncio.run(tiktok.upload_video(downloaded, "caption"))
    assert "tiktok.com" in tiktok_url
    assert tiktok_id
