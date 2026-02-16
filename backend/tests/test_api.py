"""Integration-style tests for API endpoints."""

from fastapi.testclient import TestClient

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
