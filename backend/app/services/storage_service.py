"""Cloudflare R2 (S3-compatible) storage service."""

import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Uploads and resolves media locations in object storage."""

    async def upload_file(self, local_path: Path, key: str) -> str:
        """Upload a local file and return a public URL.

        This scaffold returns a deterministic URL and can be swapped to boto3.
        """

        logger.info("Uploading file to storage", extra={"path": str(local_path), "key": key})
        if settings.r2_public_base_url:
            return f"{settings.r2_public_base_url.rstrip('/')}/{key}"
        return f"https://example-r2.local/{key}"
