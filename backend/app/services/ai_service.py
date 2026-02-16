"""AI caption generation service."""

import logging

logger = logging.getLogger(__name__)


class AIService:
    """Generates social captions and hashtags."""

    async def generate_caption_and_tags(self, context_hint: str) -> tuple[str, list[str]]:
        """Generate caption and hashtags from provided context."""

        logger.info("Generating caption", extra={"context_hint": context_hint[:80]})
        caption = "Watch this reel transformed for TikTok."
        tags = ["#reels", "#tiktok", "#automation", "#fyp"]
        return caption, tags
