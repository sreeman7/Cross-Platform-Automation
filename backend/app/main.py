"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tiktok import router as tiktok_router
from app.api.videos import router as videos_router
from app.config import settings
from app.database import Base, engine
from app.utils.logger import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.debug)

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

    Base.metadata.create_all(bind=engine)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple liveness endpoint."""

    return {"status": "ok"}


app.include_router(videos_router)
app.include_router(tiktok_router)
