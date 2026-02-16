"""Cloudflare R2 (S3-compatible) storage service."""

from __future__ import annotations

import asyncio
import logging
import mimetypes
from pathlib import Path
from urllib.parse import quote

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageServiceError(Exception):
    """Raised when storage operations fail."""


class StorageService:
    """Uploads and retrieves media in Cloudflare R2 (S3-compatible API)."""

    def __init__(
        self,
        client: BaseClient | None = None,
        bucket_name: str | None = None,
        endpoint_url: str | None = None,
        public_base_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region_name: str | None = None,
    ) -> None:
        """Initialize service with optional overrides for testability."""

        self.bucket_name = bucket_name or settings.r2_bucket_name
        self.endpoint_url = endpoint_url or settings.r2_endpoint_url
        self.public_base_url = public_base_url or settings.r2_public_base_url
        self.access_key_id = access_key_id or settings.r2_access_key_id
        self.secret_access_key = secret_access_key or settings.r2_secret_access_key
        self.region_name = region_name or getattr(settings, "r2_region", "auto")
        self._client = client

    def _validate_required_config(self) -> None:
        """Validate required storage configuration values."""

        required = {
            "R2_BUCKET_NAME": self.bucket_name,
            "R2_ENDPOINT_URL": self.endpoint_url,
            "R2_ACCESS_KEY_ID": self.access_key_id,
            "R2_SECRET_ACCESS_KEY": self.secret_access_key,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise StorageServiceError(f"Missing storage configuration: {', '.join(missing)}")

    def _get_client(self) -> BaseClient:
        """Return initialized S3-compatible boto3 client."""

        if self._client is not None:
            return self._client

        self._validate_required_config()
        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
            config=Config(signature_version="s3v4"),
        )
        return self._client

    def _content_type_for(self, local_path: Path) -> str:
        """Infer content type for uploaded object."""

        guessed, _ = mimetypes.guess_type(str(local_path))
        return guessed or "application/octet-stream"

    def get_file_url(self, key: str) -> str:
        """Return externally accessible URL for an object key."""

        encoded_key = quote(key.lstrip("/"), safe="/")
        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{encoded_key}"
        if self.endpoint_url and self.bucket_name:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{encoded_key}"
        raise StorageServiceError("Cannot build file URL without endpoint and bucket configuration.")

    def _upload_file_sync(self, local_path: Path, key: str) -> None:
        """Synchronous upload helper to execute in thread pool."""

        if not local_path.exists():
            raise StorageServiceError(f"Local file not found: {local_path}")
        if not self.bucket_name:
            raise StorageServiceError("Missing storage bucket configuration (R2_BUCKET_NAME).")

        client = self._get_client()
        client.upload_file(
            str(local_path),
            self.bucket_name,
            key,
            ExtraArgs={"ContentType": self._content_type_for(local_path)},
        )

    async def upload_file(self, local_path: Path, key: str) -> str:
        """Upload local file to R2 and return accessible URL."""

        logger.info("Uploading file to storage", extra={"path": str(local_path), "key": key})
        for attempt in range(3):
            try:
                await asyncio.to_thread(self._upload_file_sync, local_path, key)
                return self.get_file_url(key)
            except (BotoCoreError, ClientError, OSError, StorageServiceError) as exc:
                logger.warning("Storage upload attempt failed (%s/3): %s", attempt + 1, exc)
                if attempt == 2:
                    raise StorageServiceError(f"Failed uploading file to storage: {exc}") from exc
                await asyncio.sleep(2**attempt)

        raise StorageServiceError("Upload failed after retries.")

    def _download_file_sync(self, key: str, destination_path: Path) -> None:
        """Synchronous download helper to execute in thread pool."""

        if not self.bucket_name:
            raise StorageServiceError("Missing storage bucket configuration (R2_BUCKET_NAME).")

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        client = self._get_client()
        client.download_file(self.bucket_name, key, str(destination_path))

    async def download_file(self, key: str, destination_path: Path) -> Path:
        """Download an object from R2 to local destination path."""

        logger.info("Downloading file from storage", extra={"key": key, "destination": str(destination_path)})
        for attempt in range(3):
            try:
                await asyncio.to_thread(self._download_file_sync, key, destination_path)
                return destination_path
            except (BotoCoreError, ClientError, OSError, StorageServiceError) as exc:
                logger.warning("Storage download attempt failed (%s/3): %s", attempt + 1, exc)
                if attempt == 2:
                    raise StorageServiceError(f"Failed downloading file from storage: {exc}") from exc
                await asyncio.sleep(2**attempt)

        raise StorageServiceError("Download failed after retries.")
