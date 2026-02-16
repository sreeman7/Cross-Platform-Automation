"""TikTok content posting service."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TikTokService:
    """Handles TikTok upload interactions."""

    async def upload_video(self, video_path: Path, caption: str) -> tuple[str, str]:
        """Upload a video and return (tiktok_url, tiktok_video_id).

        This scaffold is a placeholder for TikTok Content Posting API.
        """

        logger.info("Uploading video to TikTok", extra={"video_path": str(video_path)})
        video_id = "mock_tiktok_video_id"
        video_url = "https://www.tiktok.com/@demo/video/mock_tiktok_video_id"
        return video_url, video_id
