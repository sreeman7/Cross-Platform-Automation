"""Instagram integration service."""

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class InstagramService:
    """Handles retrieving reel media from Instagram."""

    async def download_video(self, instagram_url: str, output_dir: Path) -> Path:
        """Download a reel video to a local temporary path with retry behavior.

        This scaffold simulates the operation and is ready to be replaced with
        Instaloader or Graph API calls.
        """

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "source.mp4"

        for attempt in range(3):
            try:
                logger.info("Downloading Instagram reel", extra={"url": instagram_url, "attempt": attempt + 1})
                await asyncio.sleep(0.2)
                output_path.write_bytes(b"mock-video-data")
                return output_path
            except Exception as exc:  # pragma: no cover - network integration placeholder
                logger.warning("Instagram download attempt failed: %s", exc)
                if attempt == 2:
                    raise
                await asyncio.sleep(2**attempt)

        return output_path
