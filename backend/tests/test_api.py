"""Integration-style tests for API endpoints."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api import tiktok as tiktok_api
from app.api import videos as videos_api
from app.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_video_crud_flow() -> None:
    create_response = client.post(
        "/api/videos/",
        json={"instagram_url": "https://www.instagram.com/reel/ABC123/"},
    )
    assert create_response.status_code == 201
    video_id = create_response.json()["id"]

    get_response = client.get(f"/api/videos/{video_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == video_id

    patch_response = client.patch(
        f"/api/videos/{video_id}",
        json={"caption": "Custom caption", "hashtags": ["#custom"]},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["caption"] == "Custom caption"

    list_response = client.get("/api/videos/")
    assert list_response.status_code == 200
    assert any(video["id"] == video_id for video in list_response.json())

    delete_response = client.delete(f"/api/videos/{video_id}")
    assert delete_response.status_code == 200


def test_video_jobs_tracking_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(videos_api.process_pipeline_task, "delay", lambda _video_id: SimpleNamespace(id="task-123"))

    create_response = client.post(
        "/api/videos/",
        json={"instagram_url": "https://www.instagram.com/reel/JOB123/"},
    )
    assert create_response.status_code == 201
    video_id = create_response.json()["id"]

    jobs_response = client.get(f"/api/videos/{video_id}/jobs")
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert len(jobs) >= 1
    assert jobs[0]["task_type"] == "process_pipeline"


def test_tiktok_auth_endpoints(monkeypatch) -> None:
    class FakeToken:
        open_id = "open_123"
        scope = "video.publish"
        expires_at = None

    async def fake_exchange(_self, _db, _code):
        return FakeToken()

    monkeypatch.setattr(tiktok_api.TikTokService, "exchange_code_for_token", fake_exchange)

    auth_response = client.get("/api/tiktok/auth-url")
    assert auth_response.status_code == 200
    assert "authorization_url" in auth_response.json()

    callback_response = client.get("/api/tiktok/callback?code=abc123&state=state123")
    assert callback_response.status_code == 200
    assert callback_response.json()["connected"] is True

    account_response = client.get("/api/tiktok/account")
    assert account_response.status_code == 200
    assert "connected" in account_response.json()
