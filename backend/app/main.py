"""FastAPI entrypoint."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from itsdangerous import BadSignature, SignatureExpired

from app.api.auth import router as auth_router, token_serializer
from app.api.tiktok import router as tiktok_router
from app.api.videos import router as videos_router
from app.config import settings
from app.utils.logger import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.middleware("http")
async def require_admin(request: Request, call_next):
    """Protect API routes when the deployment has an admin password."""

    if settings.admin_password and request.url.path.startswith("/api/") and request.url.path != "/api/auth/login":
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            return JSONResponse({"detail": "Login required"}, status_code=401)
        try:
            identity = token_serializer().loads(authorization[7:], max_age=8 * 60 * 60)
            if identity != "admin":
                raise BadSignature("Invalid identity")
        except (BadSignature, SignatureExpired):
            return JSONResponse({"detail": "Session expired; log in again"}, status_code=401)
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize required resources on service startup."""

    if not settings.debug and (not settings.admin_password or settings.secret_key == "change-me"):
        raise RuntimeError("Production requires ADMIN_PASSWORD and a unique SECRET_KEY")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple liveness endpoint."""

    return {"status": "ok"}


app.include_router(videos_router)
app.include_router(tiktok_router)
app.include_router(auth_router)
