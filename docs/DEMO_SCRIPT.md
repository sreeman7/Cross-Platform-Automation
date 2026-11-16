# Demo Walkthrough

Record only a flow you have actually tested. Use a Reel you own or have permission to republish.

1. Explain the architecture briefly: React sends the URL to FastAPI; Celery processes the video and stores status in PostgreSQL.
2. Submit the Reel in the dashboard. Show the job timeline from download through `ready_for_review`.
3. Preview the processed video. Explain that OpenAI uses the Instagram post caption as context when available, not video frames. Edit the draft caption and hashtags before approving.
4. For an infrastructure demo, enable `TIKTOK_MOCK_MODE=True` and label the result **simulated**. This does not create a TikTok post.
5. For a live demo, use an approved TikTok developer app and an authorized creator account. Approve the private upload and show the actual publish status. Do not claim a public URL unless the API returns one.
6. Show the test command and CI results. State that external API behavior still needs live validation if you have not completed it.

Keep credentials, tokens, and private account data off-screen.
