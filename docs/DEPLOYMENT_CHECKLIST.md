# Live Deployment Checklist

Use only videos you own or are permitted to republish. Do not commit API keys or connection strings.

## Before Deploying

- Confirm GitHub Actions backend tests and frontend build are green.
- Create a fresh PostgreSQL database (Supabase), TLS Redis broker URL (Upstash), and Cloudflare R2 bucket with a public preview domain.
- Set `DATABASE_URL`, `REDIS_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, and `R2_PUBLIC_BASE_URL` on Railway. Use the Upstash Redis URI beginning `rediss://`, not its REST URL beginning `https://`.
- Set `DEBUG=False`, a unique `SECRET_KEY`, and a strong `ADMIN_PASSWORD`. Never put the admin password in `VITE_*` variables.
- Set `ALLOWED_ORIGINS` to the exact Vercel frontend origin.
- Set `TIKTOK_REDIRECT_URI` to the deployed frontend URL with trailing slash. Register the same URI in TikTok developer settings.
- Set `TIKTOK_MOCK_MODE=True` for initial infrastructure tests, then `False` for live TikTok tests.
- `OPENAI_API_KEY` is optional. Without it the caption service returns a generic draft for manual review.

## Backend And Frontend

- Deploy Railway API from `backend/` using the Dockerfile and `backend/railway.toml`. It installs FFmpeg and applies Alembic migrations before serving.
- Deploy a separate Railway worker from `backend/` using the same Dockerfile and environment, overriding start command to `celery -A app.workers.celery_app worker --loglevel=info`.
- Deploy Vercel from `frontend/`, with `VITE_API_URL` set to the Railway API HTTPS URL.
- Check `/health`, `/docs`, the dashboard login, and browser network requests.

## Creator-Owned Media Test

1. Connect your TikTok test account; ensure the app has `video.publish` approval. TikTok may restrict unaudited apps to private posts.
2. Submit one Instagram Reel you own. Check the job timeline until `ready_for_review`.
3. Preview the R2 video. Edit the generated caption and hashtags.
4. Click **Approve and publish privately**. Confirm the worker creates one `upload_tiktok` job and a `publish_id`.
5. Wait for `completed` or inspect the error. A private post may never have a public URL.
6. Repeat a safe status check and confirm no duplicate post is created.

## Known Boundaries

- Instaloader access to Instagram can fail under login or rate restrictions. Official Meta ingestion for connected professional accounts is a planned improvement.
- The dashboard uses single-admin password protection; multi-user accounts are not implemented.
- If a worker crashes after TikTok accepts an upload but before the publish ID is saved, reconcile in TikTok before a manual retry.
- There is no deployed URL or recorded demo video in this repository yet.
