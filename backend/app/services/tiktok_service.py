"""TikTok content posting service."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.video import TikTokToken

logger = logging.getLogger(__name__)


class TikTokServiceError(Exception):
    """Raised when TikTok auth or upload operations fail."""


class TikTokService:
    """Handles TikTok OAuth and content posting API interactions."""

    def __init__(self) -> None:
        """Initialize service with env-driven endpoints and app credentials."""

        self.client_key = settings.tiktok_client_key
        self.client_secret = settings.tiktok_client_secret
        self.redirect_uri = settings.tiktok_redirect_uri
        self.api_base_url = settings.tiktok_api_base_url.rstrip("/")
        self.auth_base_url = settings.tiktok_auth_base_url
        self.scopes = settings.tiktok_scopes
        self.mock_mode = settings.tiktok_mock_mode

    def get_authorization_url(self, state: str) -> str:
        """Return TikTok OAuth authorization URL."""

        params = {
            "client_key": self.client_key,
            "response_type": "code",
            "scope": self.scopes,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        return f"{self.auth_base_url}?{urlencode(params)}"

    def _latest_token(self, db: Session) -> TikTokToken | None:
        """Return most recently updated TikTok token record."""

        return db.query(TikTokToken).order_by(TikTokToken.updated_at.desc()).first()

    async def _post_json(self, path: str, payload: dict, *, access_token: str | None = None) -> dict:
        """Execute JSON POST request to TikTok API."""

        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        timeout = httpx.Timeout(45.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{self.api_base_url}{path}", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def _put_bytes(self, url: str, video_bytes: bytes) -> None:
        """Upload binary content to TikTok-provided upload URL."""

        timeout = httpx.Timeout(120.0, connect=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.put(url, content=video_bytes, headers={"Content-Type": "video/mp4"})
            response.raise_for_status()

    def _assert_oauth_config(self) -> None:
        """Validate required OAuth configuration before API calls."""

        if not self.client_key or not self.client_secret or not self.redirect_uri:
            raise TikTokServiceError(
                "TikTok OAuth config is incomplete. Set TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, and TIKTOK_REDIRECT_URI."
            )

    async def exchange_code_for_token(self, db: Session, code: str) -> TikTokToken:
        """Exchange OAuth code for tokens and persist them in DB."""

        self._assert_oauth_config()
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        response = await self._post_json("/v2/oauth/token/", payload)
        data = response.get("data", {})
        access_token = data.get("access_token")
        if not access_token:
            raise TikTokServiceError("TikTok token exchange did not return access_token.")

        expires_in = int(data.get("expires_in", 3600))
        token = TikTokToken(
            open_id=data.get("open_id"),
            access_token=access_token,
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in - 60),
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    async def _refresh_token(self, db: Session, token: TikTokToken) -> TikTokToken:
        """Refresh expired access token when refresh token is available."""

        if not token.refresh_token:
            raise TikTokServiceError("TikTok refresh token is missing; re-authorize the account.")

        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        }
        response = await self._post_json("/v2/oauth/token/", payload)
        data = response.get("data", {})
        access_token = data.get("access_token")
        if not access_token:
            raise TikTokServiceError("TikTok token refresh did not return access_token.")

        expires_in = int(data.get("expires_in", 3600))
        token.access_token = access_token
        token.refresh_token = data.get("refresh_token", token.refresh_token)
        token.scope = data.get("scope", token.scope)
        token.open_id = data.get("open_id", token.open_id)
        token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    async def get_valid_access_token(self, db: Session) -> str:
        """Return a valid access token, refreshing it if needed."""

        token = self._latest_token(db)
        if not token:
            raise TikTokServiceError("No TikTok token found. Connect TikTok account first.")

        if token.expires_at and token.expires_at <= datetime.utcnow():
            token = await self._refresh_token(db, token)

        return token.access_token

    async def upload_video(self, video_path: Path, caption: str, db: Session | None = None) -> tuple[str, str]:
        """Upload a video and return `(tiktok_url, tiktok_video_id)`."""

        logger.info("Uploading video to TikTok", extra={"video_path": str(video_path)})
        if self.mock_mode:
            video_id = "mock_tiktok_video_id"
            return f"https://www.tiktok.com/@demo/video/{video_id}", video_id

        if db is None:
            raise TikTokServiceError("Database session is required for TikTok token lookup.")
        if not video_path.exists():
            raise TikTokServiceError(f"Video file does not exist: {video_path}")

        access_token = await self.get_valid_access_token(db)
        video_bytes = await asyncio.to_thread(video_path.read_bytes)

        init_payload = {
            "post_info": {"title": caption[:150], "privacy_level": "SELF_ONLY"},
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": len(video_bytes),
                "chunk_size": len(video_bytes),
                "total_chunk_count": 1,
            },
        }
        init_response = await self._post_json(
            "/v2/post/publish/video/init/",
            init_payload,
            access_token=access_token,
        )
        init_data = init_response.get("data", {})
        upload_url = init_data.get("upload_url")
        publish_id = init_data.get("publish_id") or init_data.get("video_id")
        if not upload_url:
            raise TikTokServiceError("TikTok did not return upload_url.")

        await self._put_bytes(upload_url, video_bytes)
        if not publish_id:
            publish_id = "unknown_publish_id"

        # TikTok publish completion can be async; return publish-id based URL placeholder.
        return f"https://www.tiktok.com/@me/video/{publish_id}", str(publish_id)

    def get_account_status(self, db: Session) -> dict[str, str | bool | None]:
        """Return concise token status info for dashboard/auth checks."""

        token = self._latest_token(db)
        if not token:
            return {"connected": False, "open_id": None, "expires_at": None, "scope": None}
        return {
            "connected": True,
            "open_id": token.open_id,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "scope": token.scope,
        }
