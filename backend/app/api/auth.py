"""Single-admin login for the portfolio dashboard."""

import secrets

from fastapi import APIRouter, HTTPException
from itsdangerous import URLSafeTimedSerializer
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Admin password supplied by the dashboard."""

    password: str


def token_serializer() -> URLSafeTimedSerializer:
    """Return the signer used for short-lived dashboard tokens."""

    return URLSafeTimedSerializer(settings.secret_key, salt="dashboard-session")


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, str]:
    """Issue a signed session token after password verification."""

    if not settings.admin_password or not secrets.compare_digest(payload.password, settings.admin_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"access_token": token_serializer().dumps("admin")}
