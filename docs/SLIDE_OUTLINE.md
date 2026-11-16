# Presentation Notes

1. **Problem:** Cross-posting a creator-owned Reel involves repetitive downloading, conversion, caption editing, and tracking.
2. **Design:** FastAPI accepts the request; Celery and Redis run the processing pipeline; PostgreSQL stores video and job state; R2 holds the processed file.
3. **Safety decision:** Processing stops at `ready_for_review`. A separate approval action starts private TikTok publishing, and an ambiguous upload is not retried automatically.
4. **Demo:** Show a real local run or clearly labeled mock mode. Show the job timeline, caption edit, and status result. Do not present mock mode as a real upload.
5. **Validation:** Backend tests and frontend build run in CI. Live Instagram, R2, and TikTok access still need verification with creator-owned media and approved credentials.
6. **Next work:** Replace Instaloader with official connected-account ingestion, harden token storage, and add multi-user authorization only after the single-creator flow is validated.
