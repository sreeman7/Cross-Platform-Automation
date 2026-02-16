"""AI caption generation service."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Generates social captions and hashtags."""

    def __init__(self) -> None:
        """Initialize AI service with model and OpenAI client settings."""

        self.model = settings.openai_model
        self.timeout = settings.openai_timeout_seconds
        self._client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def _fallback_caption_and_tags(self, context_hint: str) -> tuple[str, list[str]]:
        """Return deterministic fallback caption and hashtags when AI is unavailable."""

        safe_hint = context_hint.strip()[:60]
        caption = (
            f"Fresh cross-platform clip drop. {safe_hint}"
            if safe_hint
            else "Fresh cross-platform clip drop."
        )
        return caption, ["#reels", "#tiktok", "#automation", "#fyp", "#contentcreator"]

    async def _call_openai(self, context_hint: str) -> str:
        """Call OpenAI chat completions API and return raw content."""

        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        response = await self._client.chat.completions.create(
            model=self.model,
            temperature=0.7,
            timeout=self.timeout,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write short, engaging TikTok captions with relevant hashtags. "
                        "Respond only as valid JSON with keys: caption (string), hashtags (array of strings). "
                        "Limit caption to <=150 chars. Return 4-8 hashtags, each starting with #."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Generate a caption and hashtags for this Instagram reel context: {context_hint}",
                },
            ],
        )
        return response.choices[0].message.content or ""

    def _parse_response(self, content: str) -> tuple[str, list[str]]:
        """Parse OpenAI response content into (caption, hashtags)."""

        cleaned = content.strip()
        if not cleaned:
            raise ValueError("Empty AI response.")

        try:
            parsed: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                raise
            parsed = json.loads(match.group(0))

        caption = str(parsed.get("caption", "")).strip()
        raw_hashtags = parsed.get("hashtags", [])
        if not isinstance(raw_hashtags, list):
            raise ValueError("hashtags must be a list")

        hashtags: list[str] = []
        for tag in raw_hashtags:
            tag_str = str(tag).strip()
            if not tag_str:
                continue
            if not tag_str.startswith("#"):
                tag_str = f"#{tag_str.lstrip('#')}"
            if tag_str not in hashtags:
                hashtags.append(tag_str)

        if not caption:
            raise ValueError("caption is empty")
        if not hashtags:
            raise ValueError("hashtags are empty")

        return caption[:150], hashtags[:8]

    async def generate_caption_and_tags(self, context_hint: str) -> tuple[str, list[str]]:
        """Generate caption and hashtags from provided context.

        Uses OpenAI when configured; gracefully falls back to deterministic output
        when API key/network/model responses fail.
        """

        logger.info("Generating caption", extra={"context_hint": context_hint[:80]})
        for attempt in range(3):
            try:
                raw_content = await self._call_openai(context_hint)
                caption, hashtags = self._parse_response(raw_content)
                return caption, hashtags
            except Exception as exc:
                logger.warning("AI generation attempt failed (%s/3): %s", attempt + 1, exc)
                if attempt == 2:
                    fallback_caption, fallback_tags = self._fallback_caption_and_tags(context_hint)
                    logger.info("Using fallback caption generation.")
                    return fallback_caption, fallback_tags
                await asyncio.sleep(2**attempt)
