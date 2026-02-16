# Cross-Platform-Automation

Automated social media distribution system that takes Instagram Reels, processes videos, generates AI captions, and publishes to TikTok.

## Project Pitch

Cross-Platform-Automation is a portfolio-grade full-stack system that automates short-form video distribution from Instagram Reels to TikTok. It combines a FastAPI backend, Celery workers, and a React dashboard to deliver an end-to-end pipeline: ingest URL -> process media -> generate AI caption -> publish -> track status in real time.

Why this stands out for internships:

- Demonstrates backend architecture (API + async workers + persistence)
- Uses real cloud integrations (Supabase/PostgreSQL, Cloudflare R2, Upstash Redis)
- Implements external API workflows (OpenAI and TikTok OAuth/content posting)
- Ships with CI, deployment configuration, and production-oriented error handling

## Current Status

This repository now includes a complete Phase 1 foundation plus Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 7, and Phase 8 implementations:

- FastAPI backend with PostgreSQL-ready SQLAlchemy models
- REST API for video CRUD + stats summary
- Celery worker and Redis-backed task queue with per-step job tracking
- Service modules for Instagram download (Instaloader-based), video processing, real R2 storage upload/download, AI captions, and TikTok OAuth/upload
- React + Tailwind dashboard for submitting URLs and monitoring processing status
- Frontend TikTok connect flow, OAuth callback handling, and per-video job timeline view
- Initial pytest test suite
- Docker and docker-compose setup
- CI workflow for backend tests + frontend build

## Architecture

- Frontend: React (Vite + Tailwind)
- Backend: FastAPI + SQLAlchemy
- Queue: Celery + Redis
- Database: PostgreSQL (Supabase in production)
- Storage: Cloudflare R2
- AI: OpenAI API (implemented with fallback mode)
- Deployment targets: Railway (API/worker) + Vercel (frontend)

## Repository Structure

```text
Cross-Platform-Automation/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── workers/
│   │   ├── utils/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (local or Upstash)
- PostgreSQL (local or Supabase)

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set environment variables in `backend/.env`.

Run API:

```bash
uvicorn app.main:app --reload
```

Run worker:

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

API docs:

- Swagger UI: `http://localhost:8000/docs`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

By default, frontend expects backend at `http://localhost:8000`. Override using `VITE_API_URL`.

## Docker (Local)

```bash
docker compose up --build
```

## Testing

Backend tests:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
```

Notes:

- `backend/tests/conftest.py` forces safe local defaults for test execution.
- CI enforces `--cov-fail-under=70` on backend tests.

## Implemented API Endpoints

- `POST /api/videos/`
- `GET /api/videos/`
- `GET /api/videos/{id}`
- `GET /api/videos/{id}/jobs`
- `PATCH /api/videos/{id}`
- `DELETE /api/videos/{id}`
- `GET /api/stats/summary`
- `GET /api/tiktok/auth-url`
- `GET /api/tiktok/callback`
- `GET /api/tiktok/account`
- `GET /health`

## Notes on Integrations

Instagram download now uses real shortcode parsing and Instaloader post resolution, then downloads media bytes with retries. Cloudflare R2 storage uses real `boto3` S3-compatible upload/download logic with retries. OpenAI caption generation is implemented with retry + graceful fallback when API/config fails. TikTok OAuth/token handling and upload initialization are implemented for Phase 6.

## Next Milestones

1. Add Alembic migrations for managed schema changes.
2. Add user authentication and role-based access.
3. Add TikTok publish-status polling to resolve final public URLs.
4. Record demo video and add dashboard/API screenshots.

## Phase 3 Storage Notes

- `StorageService` uploads processed videos to Cloudflare R2 via `boto3`.
- Retry policy: 3 attempts with exponential backoff for transient failures.
- URL resolution:
  - Uses `R2_PUBLIC_BASE_URL` when provided (recommended for public CDN URLs).
  - Falls back to endpoint-based URL format if public base URL is not set.

## Phase 4 Queue Notes

- Celery tasks implemented:
  - `download_video_task`
  - `upload_to_storage_task`
  - `process_pipeline_task` (orchestrates full workflow)
- Retry policy: Celery autoretry with max 3 retries and exponential backoff.
- Job tracking:
  - `POST /api/videos/` creates a pending `process_pipeline` job when queueing succeeds.
  - Every pipeline step writes a `jobs` row (`download_video`, `process_video`, `upload_storage`, `generate_caption`, `upload_tiktok`).
  - Query per-video jobs via `GET /api/videos/{id}/jobs`.

## Phase 5 AI Notes

- `AIService` uses OpenAI chat completions to generate:
  - caption (<=150 chars)
  - 4-8 normalized hashtags
- Retry policy: up to 3 attempts with exponential backoff.
- Graceful degradation:
  - If `OPENAI_API_KEY` is missing or OpenAI call fails, a deterministic fallback caption and hashtags are returned.
- New env vars:
  - `OPENAI_MODEL` (default: `gpt-4o-mini`)
  - `OPENAI_TIMEOUT_SECONDS` (default: `30`)

## Phase 6 TikTok Notes

- Added OAuth endpoints:
  - `GET /api/tiktok/auth-url`
  - `GET /api/tiktok/callback`
  - `GET /api/tiktok/account`
- Added persistent token model: `tiktok_tokens`.
- `TikTokService` now supports:
  - OAuth auth URL generation
  - code-to-token exchange
  - automatic token refresh
  - upload initialization + binary upload calls
- Dev-mode option:
  - `TIKTOK_MOCK_MODE=True` keeps local development/testing unblocked without live TikTok credentials.

## Phase 7 Frontend Notes

- Dashboard now includes:
  - TikTok account connection card (`Connect TikTok` / `Reconnect`)
  - OAuth callback handling from query params (`code`, `state`)
  - per-video job timeline drawer fed by `GET /api/videos/{id}/jobs`
  - improved error visibility for API failures
- Frontend API client now includes methods for:
  - TikTok auth URL, callback exchange, account status
  - per-video jobs retrieval

## Phase 8 Testing and Deployment Notes

- Added CI pipeline:
  - `.github/workflows/ci.yml`
  - backend pytest + coverage gate (70%)
  - frontend production build check
- Added test config:
  - `backend/pytest.ini`
  - `backend/tests/conftest.py` for local-safe env defaults
- Added deployment config:
  - `railway.toml` for backend service start/health checks
  - `vercel.json` for frontend static deployment and SPA routing
  - `frontend/.env.example` with `VITE_API_URL`

## Deployment Guide

### Backend API (Railway)

1. Create a Railway service from this repo root.
2. Set root directory to `backend`.
3. Build command:
   - `pip install -r requirements.txt`
4. Start command:
   - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all required env vars from `backend/.env.example`.
6. Verify health endpoint:
   - `GET /health`

### Celery Worker (Railway)

1. Create a second Railway service from same repo.
2. Set root directory to `backend`.
3. Build command:
   - `pip install -r requirements.txt`
4. Start command:
   - `celery -A app.workers.celery_app worker --loglevel=info`
5. Reuse same env vars as backend API.

### Frontend (Vercel)

1. Import repo into Vercel.
2. Set project root to `frontend`.
3. Build command:
   - `npm run build`
4. Output directory:
   - `dist`
5. Add env var:
   - `VITE_API_URL=https://your-backend-domain`

## Screenshots

Add screenshots after capture (recommended filenames):

- `docs/screenshots/dashboard-overview.png`
- `docs/screenshots/upload-form-and-queue.png`
- `docs/screenshots/job-timeline-expanded.png`
- `docs/screenshots/swagger-endpoints.png`
- `docs/screenshots/tiktok-connect-flow.png`

Capture checklist is available in:

- `docs/screenshots/README.md`

## Demo

- 2-3 minute recording script:
  - `docs/DEMO_SCRIPT.md`
- Slide structure for project presentation:
  - `docs/SLIDE_OUTLINE.md`

## License

MIT
