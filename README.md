# Cross-Platform Automation

A single-creator workspace for preparing a creator-owned Instagram Reel for TikTok. Submit a Reel URL, follow the processing jobs, review the caption draft and video, then approve either a simulated upload or a private TikTok upload. The dashboard shows status and failure reasons.

This is a portfolio project under active development, not a live distribution service. Tests and builds pass, but a complete run against Instagram, R2, and TikTok has not yet been verified.

## How It Works

```text
React dashboard -> FastAPI -> PostgreSQL (SQLite for local development)
                       |           ^
                       v           |
                  Redis/Celery worker
                       |
        Instagram -> FFmpeg -> R2 -> caption draft
                                         |
                                creator reviews/approves
                                         |
                         simulated or private TikTok upload
```

The worker uses the Instagram post caption as context for OpenAI when both are available. It cannot analyze the video itself; without context or an API key it returns a placeholder for the creator to edit. The processing job ends at `ready_for_review`. Approval starts a separate publish job. A conditional database update lets only one worker claim that job. Uploads are not automatically retried after an ambiguous TikTok failure, because a retry could create a duplicate post.

## Current State

| Area | Status |
| --- | --- |
| API, database migration, Redis worker | Running locally; backend tests pass |
| Dashboard | Builds locally; sign-in and browser flow still need a manual walkthrough |
| Instagram download, FFmpeg, R2, OpenAI, TikTok integration | Code exists; external accounts and a full live run are unverified |
| TikTok mock mode | Simulates only the final upload; Instagram and R2 still run for real |
| Public deployment, screenshots, recorded demo | Not completed |

## Stack

FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL, FFmpeg, React, Vite, and Tailwind CSS. Integrations use Instaloader, Cloudflare R2's S3 API, optional OpenAI caption generation, and TikTok's OAuth and Content Posting API.

## Run Locally With Docker

You need Docker Desktop and Node.js. Docker supplies Python 3.11, FFmpeg, and Redis; you do not need to install them on your Mac. The repo uses SQLite for this local setup. From the repository root:

```bash
test -f backend/.env || cp backend/.env.example backend/.env
```

Edit `backend/.env` without committing or sharing it. For the local Docker setup, set `DATABASE_URL=sqlite:////app/app.db`, `REDIS_URL=redis://redis:6379/0`, `DEBUG=True`, a unique `SECRET_KEY`, and an `ADMIN_PASSWORD` you will use to sign in. Set `TIKTOK_MOCK_MODE=True` to simulate TikTok. Leave `OPENAI_API_KEY=` empty if you do not have API access; do not leave the example `sk-xxx` value. Do not assume the example R2 or TikTok credentials are usable.

Run the migration, then start the API and worker:

```bash
docker compose run --rm --build api alembic upgrade head
docker compose up -d --build
curl http://localhost:8000/health
```

In another terminal, start the frontend:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173` and sign in with your `ADMIN_PASSWORD`. API documentation is at `http://localhost:8000/docs`. The frontend reads `VITE_API_URL`, defaulting to `http://localhost:8000`. Stop the backend later with `docker compose down` from the repository root.

Login and dashboard loading need no external accounts. Submitting a Reel still needs Instagram access and **real** Cloudflare R2 settings, including an enabled public `R2_PUBLIC_BASE_URL` for browser preview. Mock mode does not bypass those stages. If you run without Docker, install Python 3.11, FFmpeg, Redis, and the packages in `backend/requirements.txt`, then run Alembic, Uvicorn, and Celery separately.

## Test

```bash
docker compose exec -T worker pytest --cov=app --cov-report=term-missing --cov-fail-under=70
cd frontend
npm ci
npm run build
```

CI runs the same backend coverage gate and frontend build. Verified locally on November 16, 2026: 30 backend tests passed at 77.73% coverage, and the Vite build passed. Tests mock external services; they do not prove live posting.

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

## Next Milestones

1. Sign in locally and walk through the dashboard in a browser.
2. Configure R2 and run one creator-owned Reel through `ready_for_review`, then approve a clearly labeled simulated upload.
3. Decide whether to redesign the product for TikTok's Direct Post requirements. Do not claim live publishing until developer approval and a real private-post test succeed.
4. Deploy the API, worker, and frontend only after the local flow is reliable. Capture screenshots and a short demo, and document the deployed URLs.

## Limits And Next Work

- Instaloader may fail when Instagram changes access rules. Official Meta ingestion for a connected professional account is planned.
- TikTok Direct Post requires an approved app and creator authorization. Unaudited apps are restricted to private posts. Private posts may not have public URLs; the dashboard does not invent one.
- [TikTok's content-sharing guidelines](https://developers.tiktok.com/docs/en/content-sharing-guidelines) do not accept an arbitrary cross-platform copying tool or a single-account utility as an audited Direct Post product. This portfolio UI is not ready for that audit or a public launch.
- The dashboard is for one admin, not multiple creator accounts. TikTok tokens are stored in the application database and need a production token-handling review.
- The initial Alembic migration targets a fresh database. Existing tables created by older versions need a manual schema check before migration.
- Screenshots, a recorded demo, and a verified live deployment are still outstanding.

Only republish media you own or have permission to use. See [the demo walkthrough](docs/DEMO_SCRIPT.md) for a suggested recording flow.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
