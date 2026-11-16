# Cross-Platform Automation

A single-creator workspace for preparing an Instagram Reel for TikTok. Submit a Reel URL, watch a Celery worker download and convert it, review the caption draft and video, then explicitly approve a private TikTok upload. The dashboard shows each job and its failure reason.

This is a portfolio project under active development. Local tests and builds pass; a complete live run against Instagram, R2, and TikTok has not yet been verified.

## How It Works

```text
React dashboard -> FastAPI -> PostgreSQL
                       |           ^
                       v           |
                  Redis/Celery worker
                       |
        Instagram -> FFmpeg -> R2 -> caption draft
                                         |
                                creator reviews/approves
                                         |
                                TikTok private upload
```

The worker uses the Instagram post caption as context for OpenAI when both are available. It cannot analyze the video itself; without context or an API key it returns a placeholder for the creator to edit. The processing job ends at `ready_for_review`. Approval starts a separate publish job. A conditional database update lets only one worker claim that job. Uploads are not automatically retried after an ambiguous TikTok failure, because a retry could create a duplicate post.

## Stack

FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL, FFmpeg, React, Vite, and Tailwind CSS. Integrations use Instaloader, Cloudflare R2's S3 API, optional OpenAI caption generation, and TikTok's OAuth and Content Posting API.

## Run Locally

You need Python 3.11, Node.js 20, FFmpeg, a Redis server, and a PostgreSQL database. SQLite works for local API tests. For a full processing run, configure Instagram access and R2 in `backend/.env`.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`. Use `DEBUG=True` locally and set `DATABASE_URL` and `REDIS_URL` to working services. Upstash's `rediss://` connection URI works with Celery; its `https://` REST endpoint does not. Leave `OPENAI_API_KEY` empty to use a generic caption draft. For a full processing run, `R2_PUBLIC_BASE_URL` must point to an enabled public R2 domain; the S3 API endpoint cannot serve browser previews. `TIKTOK_MOCK_MODE=True` simulates the final upload and is labeled as simulated in the dashboard; it does not post to TikTok.

Start three terminals:

```bash
# backend/
alembic upgrade head
uvicorn app.main:app --reload

# backend/ in another terminal
celery -A app.workers.celery_app worker --loglevel=info

# frontend/ in another terminal
npm ci
npm run dev
```

Open `http://localhost:5173` for the dashboard and `http://localhost:8000/docs` for API documentation. The frontend reads `VITE_API_URL`, defaulting to `http://localhost:8000`.

## Test

```bash
cd backend
pytest --cov=app --cov-report=term-missing --cov-fail-under=70

cd ../frontend
npm ci
npm run build
```

CI runs the same backend coverage gate and frontend build. The last local backend run passed 23 tests at 73.89% coverage. Unit tests mock external services; they do not prove live posting.

## API And Status

| Action | Endpoint |
| --- | --- |
| Log in | `POST /api/auth/login` |
| Submit a Reel | `POST /api/videos/` |
| List or inspect videos | `GET /api/videos/`, `GET /api/videos/{id}` |
| Edit caption and hashtags | `PATCH /api/videos/{id}` |
| Inspect stage history | `GET /api/videos/{id}/jobs` |
| Approve private upload | `POST /api/videos/{id}/approve` |
| Refresh TikTok status | `POST /api/videos/{id}/check-publication` |
| Dashboard totals | `GET /api/stats/summary` |
| Connect TikTok | `GET /api/tiktok/auth-url`, `GET /api/tiktok/callback` |

Processing statuses: `pending`, `downloading`, `processing`, `uploading`, `ready_for_review`, `publishing`, `completed`, `demo_completed`, `failed`. Simulated runs are counted separately from published runs.

## Deployment

`backend/railway.toml` uses the Dockerfile, which installs FFmpeg and runs Alembic migrations before the API starts. A second Railway service runs the Celery worker. Vercel builds from `frontend/`. See [the deployment checklist](docs/DEPLOYMENT_CHECKLIST.md) for variables and a creator-owned-media test.

In production set `DEBUG=False`, a strong `ADMIN_PASSWORD`, a unique `SECRET_KEY`, and exact `ALLOWED_ORIGINS`. The API refuses to start in production mode without the password and secret. Do not put credentials in `VITE_*` variables or commit `.env`.

## Limits And Next Work

- Instaloader may fail when Instagram changes access rules. Official Meta ingestion for a connected professional account is planned.
- TikTok Direct Post requires an approved app and creator authorization. Unaudited apps may be limited to private posts. Private posts may not have public URLs; the dashboard does not invent one.
- TikTok's developer review has additional product and consent requirements. This single-creator portfolio UI is not yet ready for that audit or a public launch.
- The dashboard is for one admin, not multiple creator accounts. TikTok tokens are stored in the application database and need a production token-handling review.
- The initial Alembic migration targets a fresh database. Existing tables created by older versions need a manual schema check before migration.
- Screenshots, a recorded demo, and a verified live deployment are still outstanding.

Only republish media you own or have permission to use. See [the demo walkthrough](docs/DEMO_SCRIPT.md) for a suggested recording flow.
