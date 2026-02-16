# Demo Script (2-3 Minutes)

## 1. Problem and Goal (20-30s)

"Creators often repurpose Instagram Reels to TikTok manually. This project automates that pipeline: ingest a Reel URL, process media, generate AI caption/hashtags, and publish to TikTok with status tracking."

## 2. Architecture Walkthrough (30-40s)

Show README architecture section and explain:

- React dashboard submits URL
- FastAPI creates a video record and queues a Celery job
- Worker pipeline steps:
  - download from Instagram
  - process video
  - upload to Cloudflare R2
  - generate caption with OpenAI
  - upload to TikTok
- PostgreSQL tracks status and job history

## 3. Live Backend Demo (35-45s)

1. Open Swagger UI (`/docs`).
2. Use `POST /api/videos/` with an Instagram reel URL.
3. Call `GET /api/videos/{id}` to show status transitions.
4. Call `GET /api/videos/{id}/jobs` to show per-step jobs.
5. Call `GET /api/stats/summary` to show aggregate analytics.

## 4. Live Frontend Demo (35-45s)

1. Show dashboard stats cards.
2. Click `Connect TikTok` (or explain mock mode for local dev).
3. Submit a reel URL in Upload Form.
4. Open `Show job timeline` on the new card.
5. Show generated caption and final TikTok URL field when completed.

## 5. Engineering Quality (20-30s)

Mention:

- Retry logic + graceful error handling across services
- Celery async pipeline with durable job records
- CI workflow with backend coverage gate and frontend build checks
- Deployment-ready config for Railway + Vercel

## 6. Close (10-15s)

"Next improvements: auth, TikTok publish-status polling, and richer analytics. The current version is production-structured and deployable on free tiers."
