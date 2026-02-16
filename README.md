# Cross-Platform-Automation

Automated social media distribution system that takes Instagram Reels, processes videos, generates AI captions, and publishes to TikTok.

## Current Status

This repository now includes a complete Phase 1 foundation plus Phase 2, Phase 3, and Phase 4 implementations:

- FastAPI backend with PostgreSQL-ready SQLAlchemy models
- REST API for video CRUD + stats summary
- Celery worker and Redis-backed task queue with per-step job tracking
- Service modules for Instagram download (Instaloader-based), video processing, real R2 storage upload/download, AI captions, and TikTok upload
- React + Tailwind dashboard for submitting URLs and monitoring processing status
- Initial pytest test suite
- Docker and docker-compose setup

## Architecture

- Frontend: React (Vite + Tailwind)
- Backend: FastAPI + SQLAlchemy
- Queue: Celery + Redis
- Database: PostgreSQL (Supabase in production)
- Storage: Cloudflare R2
- AI: OpenAI API (scaffolded)
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

## Implemented API Endpoints

- `POST /api/videos/`
- `GET /api/videos/`
- `GET /api/videos/{id}`
- `GET /api/videos/{id}/jobs`
- `PATCH /api/videos/{id}`
- `DELETE /api/videos/{id}`
- `GET /api/stats/summary`
- `GET /health`

## Notes on Integrations

Instagram download now uses real shortcode parsing and Instaloader post resolution, then downloads media bytes with retries. Cloudflare R2 storage now uses real `boto3` S3-compatible upload/download logic with retries. AI/TikTok modules remain scaffolded placeholders for later phases.

## Next Milestones

1. Replace TikTok/AI/storage stubs with production API clients.
2. Add Alembic migrations for managed schema changes.
3. Add auth, richer analytics, and stronger test coverage.
4. Deploy backend + worker to Railway and frontend to Vercel.

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

## License

MIT
