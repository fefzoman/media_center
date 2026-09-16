from fastapi.testclient import TestClient

from media_center.main import app


def test_health_reports_liveness_without_claiming_torrserver_is_ready() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok", "torrserver": "not_configured"}
