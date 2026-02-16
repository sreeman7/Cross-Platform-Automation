"""Instagram integration service."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class InstagramDownloadError(Exception):
    """Raised when Instagram media cannot be downloaded."""


class InvalidInstagramUrlError(InstagramDownloadError):
    """Raised when a user submits a non-supported Instagram URL."""


@dataclass
class InstagramDownloadResult:
    """Download output containing local file path and parsed media metadata."""

    video_path: Path
    shortcode: str
    media_id: str | None


class InstagramService:
    """Handles retrieving reel media from Instagram."""

    def _extract_shortcode(self, instagram_url: str) -> str:
        """Extract supported Instagram shortcode from reel/post/tv URL."""

        parsed = urlparse(instagram_url)
        if "instagram.com" not in parsed.netloc:
            raise InvalidInstagramUrlError("Only instagram.com URLs are supported.")

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2 or parts[0] not in {"reel", "p", "tv"}:
            raise InvalidInstagramUrlError(
                "Invalid Instagram URL format. Use URLs like https://www.instagram.com/reel/<shortcode>/"
            )

        shortcode = parts[1].strip()
        if not shortcode:
            raise InvalidInstagramUrlError("Missing Instagram shortcode in URL.")
        return shortcode

    def _get_post_by_shortcode(self, shortcode: str) -> object:
        """Load Instagram post object via Instaloader."""

        try:
            import instaloader
        except ImportError as exc:  # pragma: no cover - dependency installation issue
            raise InstagramDownloadError("Instaloader is not installed in the runtime environment.") from exc

        loader = instaloader.Instaloader(
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
        )
        return instaloader.Post.from_shortcode(loader.context, shortcode)

    async def _download_video_file(self, video_url: str, output_path: Path) -> None:
        """Download a remote video URL and persist it to output_path."""

        timeout = httpx.Timeout(45.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            output_path.write_bytes(response.content)

    async def download_video_with_metadata(self, instagram_url: str, output_dir: Path) -> InstagramDownloadResult:
        """Download Instagram reel video with retries and return metadata."""

        shortcode = self._extract_shortcode(instagram_url)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{shortcode}.mp4"

        for attempt in range(3):
            try:
                logger.info("Downloading Instagram reel", extra={"url": instagram_url, "attempt": attempt + 1})
                post = await asyncio.to_thread(self._get_post_by_shortcode, shortcode)

                if not getattr(post, "is_video", False):
                    raise InstagramDownloadError("Provided Instagram URL does not point to a video.")

                video_url = getattr(post, "video_url", None)
                if not video_url:
                    raise InstagramDownloadError("Instagram video URL could not be resolved.")

                await self._download_video_file(video_url, output_path)
                if not output_path.exists() or output_path.stat().st_size == 0:
                    raise InstagramDownloadError("Downloaded file is missing or empty.")

                media_id = getattr(post, "mediaid", None)
                return InstagramDownloadResult(
                    video_path=output_path,
                    shortcode=shortcode,
                    media_id=str(media_id) if media_id is not None else None,
                )

            except InvalidInstagramUrlError:
                raise
            except (httpx.HTTPError, InstagramDownloadError, OSError) as exc:
                logger.warning("Instagram download attempt failed (%s/3): %s", attempt + 1, exc)
                if attempt == 2:
                    raise InstagramDownloadError(f"Failed to download Instagram video: {exc}") from exc
                await asyncio.sleep(2**attempt)
            except Exception as exc:  # pragma: no cover - unexpected external failures
                logger.exception("Unexpected Instagram error while downloading reel.")
                if attempt == 2:
                    raise InstagramDownloadError(f"Unexpected Instagram download failure: {exc}") from exc
                await asyncio.sleep(2**attempt)

        raise InstagramDownloadError("Instagram download failed after retries.")

    async def download_video(self, instagram_url: str, output_dir: Path) -> Path:
        """Backward-compatible helper that returns only the local video path."""

        result = await self.download_video_with_metadata(instagram_url, output_dir)
        return result.video_path
