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

Current repository status: API, worker pipeline, protected creator dashboard, review-before-publish flow, database migrations, and CI tests are implemented. Live third-party publishing and cloud deployment require account credentials and validation with permitted media.

- FastAPI backend with PostgreSQL-ready SQLAlchemy models
- REST API for video CRUD + stats summary
- Celery worker and Redis-backed task queue with per-step job tracking
- Service modules for Instagram download (Instaloader-based), video processing, real R2 storage upload/download, AI captions, and TikTok OAuth/upload
- React + Tailwind dashboard for submitting URLs and monitoring processing status
- Frontend TikTok connect flow, OAuth callback handling, and per-video job timeline view
- Backend pytest suite with a 70% CI coverage gate
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
- FFmpeg executable (provided by `backend/Dockerfile`)

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set environment variables in `backend/.env`.

For local development set `DEBUG=True`. For deployment set `DEBUG=False`, `ADMIN_PASSWORD` to a strong unique password, and `SECRET_KEY` to a separate random secret. The API refuses to start in production mode without them. Never commit `.env`.

For Upstash, copy the TLS Redis connection URI (`rediss://...`) into `REDIS_URL`. The Upstash REST endpoint (`https://...`) cannot be used as the Celery broker.

Run API:

```bash
alembic upgrade head
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
- Verified locally: 22 backend tests pass with more than 73% coverage; frontend `npm run build` passes.

## Implemented API Endpoints

- `POST /api/videos/`
- `GET /api/videos/`
- `GET /api/videos/{id}`
- `GET /api/videos/{id}/jobs`
- `POST /api/videos/{id}/check-publication`
- `POST /api/videos/{id}/approve`
- `POST /api/auth/login`
- `PATCH /api/videos/{id}`
- `DELETE /api/videos/{id}`
- `GET /api/stats/summary`
- `GET /api/tiktok/auth-url`
- `GET /api/tiktok/callback`
- `GET /api/tiktok/account`
- `GET /health`

## Notes on Integrations

Instagram download uses Instaloader for publicly accessible reels; login restrictions and platform changes can block retrieval. R2 upload uses `boto3`. OpenAI captions fall back to a generic caption when no key is configured. The pipeline now stops at `ready_for_review`; the creator edits the caption and approves a private TikTok post. TikTok OAuth and upload code exist, but live posting requires app approval, a connected account, permitted media, and validation against TikTok's API. `TIKTOK_MOCK_MODE=True` simulates the final upload and is labeled `demo_completed`; it does not publish anything.

## Next Milestones

1. Validate the full workflow with creator-owned media and live Instagram, R2, Redis, and TikTok accounts.
2. Add official Meta account-based ingestion as the reliable alternative to Instaloader.
3. Add multi-user roles if this grows beyond a single creator account.
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
  - `TIKTOK_MOCK_MODE=True` simulates upload; no TikTok post is created.
  - A processed clip waits at `ready_for_review` until the dashboard user explicitly approves a private post.
  - Real upload stays `publishing` until `POST /api/videos/{id}/check-publication` confirms success.
  - TikTok may not provide a public post ID for private posts; the dashboard does not invent a URL.
  - A failed or interrupted TikTok upload is not retried automatically because doing so could create duplicate posts. Inspect the job and TikTok account before retrying manually.

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
  - `backend/railway.toml` for Dockerfile-based API service with FFmpeg and Alembic migration on startup
  - `frontend/vercel.json` for SPA routing
  - `frontend/.env.example` with `VITE_API_URL`

## Deployment Guide

### Backend API (Railway)

1. Create a Railway service from this repo root.
2. Set root directory to `backend`.
3. Use the `backend/Dockerfile` builder (specified in `backend/railway.toml`).
4. Use the API start command from `backend/railway.toml`.
5. Add all required env vars from `backend/.env.example`.
   Set `DEBUG=False`, `ADMIN_PASSWORD`, and a unique `SECRET_KEY` before exposing the API.
6. Verify health endpoint:
   - `GET /health`

### Celery Worker (Railway)

1. Create a second Railway service from same repo.
2. Set root directory to `backend`.
3. Build command:
   - `pip install -r requirements.txt`
4. Use the same Dockerfile and override the start command with `celery -A app.workers.celery_app worker --loglevel=info`.
5. Reuse same env vars as backend API.

For an existing database created by older versions of this project, inspect its schema before applying the initial Alembic migration. The initial migration is intended for a fresh database and may conflict with existing tables.

### Frontend (Vercel)

1. Import repo into Vercel.
2. Set project root to `frontend`.
3. Build command:
   - `npm run build`
4. Output directory:
   - `dist`
5. Add env var:
   - `VITE_API_URL=https://your-backend-domain`

Set `TIKTOK_REDIRECT_URI` on the backend and in the TikTok developer app to the deployed frontend URL, including its trailing slash. See [deployment checklist](docs/DEPLOYMENT_CHECKLIST.md) for the live verification steps.

## Screenshots

Add screenshots after capture (recommended filenames):

- `docs/screenshots/dashboard-overview.png`
- `docs/screenshots/upload-form-and-queue.png`
- `docs/screenshots/job-timeline-expanded.png`
- `docs/screenshots/swagger-endpoints.png`
- `docs/screenshots/tiktok-connect-flow.png`

Capture checklist is available in:

- `docs/screenshots/README.md`

## License

MIT
