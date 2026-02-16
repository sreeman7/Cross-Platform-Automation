"""TikTok OAuth endpoints."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.video import TikTokAccountStatusResponse, TikTokAuthUrlResponse, TikTokCallbackResponse
from app.services.tiktok_service import TikTokService, TikTokServiceError

router = APIRouter(prefix="/api/tiktok", tags=["tiktok"])


@router.get("/auth-url", response_model=TikTokAuthUrlResponse)
def get_tiktok_auth_url() -> TikTokAuthUrlResponse:
    """Generate TikTok OAuth authorization URL for frontend redirect."""

    service = TikTokService()
    state = secrets.token_urlsafe(16)
    return TikTokAuthUrlResponse(authorization_url=service.get_authorization_url(state), state=state)


@router.get("/callback", response_model=TikTokCallbackResponse)
async def tiktok_callback(
    code: str = Query(..., min_length=2),
    state: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
) -> TikTokCallbackResponse:
    """Exchange TikTok OAuth code and persist access/refresh tokens."""

    _ = state
    service = TikTokService()

    try:
        token = await service.exchange_code_for_token(db, code)
    except TikTokServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TikTokCallbackResponse(
        connected=True,
        open_id=token.open_id,
        scope=token.scope,
        expires_at=token.expires_at,
    )


@router.get("/account", response_model=TikTokAccountStatusResponse)
def get_tiktok_account_status(db: Session = Depends(get_db)) -> TikTokAccountStatusResponse:
    """Return current TikTok account connection status."""

    service = TikTokService()
    status_data = service.get_account_status(db)
    return TikTokAccountStatusResponse(**status_data)
