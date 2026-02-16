# Cross-Platform-Automation

Automated social media distribution system that takes Instagram Reels, processes videos, generates AI captions, and publishes to TikTok.

## Current Status

This repository now includes a complete Phase 1 foundation plus pipeline scaffolding:

- FastAPI backend with PostgreSQL-ready SQLAlchemy models
- REST API for video CRUD + stats summary
- Celery worker and Redis-backed task queue wiring
- Service modules for Instagram download, video processing, R2 upload, AI captions, and TikTok upload
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
- `PATCH /api/videos/{id}`
- `DELETE /api/videos/{id}`
- `GET /api/stats/summary`
- `GET /health`

## Notes on Integrations

Current external integration modules are scaffolded with deterministic placeholder behavior so you can run the pipeline end-to-end locally before adding real credentials.

## Next Milestones

1. Replace Instagram/TikTok/AI/storage stubs with production API clients.
2. Add Alembic migrations for managed schema changes.
3. Add auth, richer analytics, and stronger test coverage.
4. Deploy backend + worker to Railway and frontend to Vercel.

## License

MIT
