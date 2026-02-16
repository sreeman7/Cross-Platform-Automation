"""Unit tests for service scaffolds."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
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
    assert all(tag.startswith("#") for tag in tags)


def test_ai_service_parses_openai_json(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AIService()

    async def fake_call_openai(_context_hint: str) -> str:
        return '{"caption":"Daily creator update","hashtags":["reels","tiktok","#fyp"]}'

    monkeypatch.setattr(service, "_call_openai", fake_call_openai)
    caption, tags = asyncio.run(service.generate_caption_and_tags("creator vlog"))

    assert caption == "Daily creator update"
    assert tags == ["#reels", "#tiktok", "#fyp"]


def test_ai_service_fallback_when_openai_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AIService()

    async def failing_call_openai(_context_hint: str) -> str:
        raise RuntimeError("network down")

    monkeypatch.setattr(service, "_call_openai", failing_call_openai)
    caption, tags = asyncio.run(service.generate_caption_and_tags("my demo reel"))

    assert "cross-platform" in caption.lower()
    assert len(tags) >= 4


def test_video_processor_copies_file(tmp_path: Path) -> None:
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"video")
    processor = VideoProcessor()

    output = asyncio.run(processor.process_video(input_file, tmp_path / "processed"))
    assert output.exists()
    assert output.read_bytes() == b"video"


def test_storage_service_returns_url(tmp_path: Path) -> None:
    class FakeS3Client:
        def __init__(self) -> None:
            self.upload_calls: list[tuple[str, str, str, dict]] = []
            self.download_calls: list[tuple[str, str, str]] = []

        def upload_file(self, file_name: str, bucket: str, key: str, ExtraArgs: dict) -> None:
            self.upload_calls.append((file_name, bucket, key, ExtraArgs))

        def download_file(self, bucket: str, key: str, destination: str) -> None:
            self.download_calls.append((bucket, key, destination))
            Path(destination).write_bytes(b"downloaded")

    test_file = tmp_path / "clip.mp4"
    test_file.write_bytes(b"video")
    fake_client = FakeS3Client()
    service = StorageService(
        client=fake_client,
        bucket_name="social-media-videos",
        endpoint_url="https://account-id.r2.cloudflarestorage.com",
        public_base_url="https://cdn.example.dev",
    )

    url = asyncio.run(service.upload_file(test_file, "videos/1/clip.mp4"))
    assert url == "https://cdn.example.dev/videos/1/clip.mp4"
    assert len(fake_client.upload_calls) == 1

    destination = tmp_path / "downloaded" / "clip.mp4"
    downloaded_path = asyncio.run(service.download_file("videos/1/clip.mp4", destination))
    assert downloaded_path.exists()
    assert downloaded_path.read_bytes() == b"downloaded"


def test_storage_service_falls_back_to_endpoint_url() -> None:
    service = StorageService(
        client=SimpleNamespace(upload_file=lambda *_args, **_kwargs: None),
        bucket_name="social-media-videos",
        endpoint_url="https://account-id.r2.cloudflarestorage.com",
        public_base_url="",
    )
    assert (
        service.get_file_url("videos/1/test.mp4")
        == "https://account-id.r2.cloudflarestorage.com/social-media-videos/videos/1/test.mp4"
    )


def test_instagram_download_with_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    instagram = InstagramService()

    def fake_get_post(shortcode: str) -> SimpleNamespace:
        assert shortcode == "ABC123"
        return SimpleNamespace(is_video=True, video_url="https://cdn.example.com/mock.mp4", mediaid=987654)

    async def fake_download(video_url: str, output_path: Path) -> None:
        assert video_url.endswith(".mp4")
        output_path.write_bytes(b"video")

    monkeypatch.setattr(instagram, "_get_post_by_shortcode", fake_get_post)
    monkeypatch.setattr(instagram, "_download_video_file", fake_download)

    result = asyncio.run(instagram.download_video_with_metadata("https://www.instagram.com/reel/ABC123/", tmp_path))
    assert result.video_path.exists()
    assert result.media_id == "987654"


def test_instagram_invalid_url_raises(tmp_path: Path) -> None:
    instagram = InstagramService()
    with pytest.raises(Exception):
        asyncio.run(instagram.download_video("https://www.youtube.com/watch?v=demo", tmp_path))


def test_tiktok_stub_upload(tmp_path: Path) -> None:
    tiktok = TikTokService()
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"video")
    tiktok_url, tiktok_id = asyncio.run(tiktok.upload_video(video_path, "caption"))
    assert "tiktok.com" in tiktok_url
    assert tiktok_id
