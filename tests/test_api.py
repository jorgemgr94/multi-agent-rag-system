"""API endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_status_endpoint():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "features" in data


def test_tasks_endpoint_validation():
    response = client.post("/tasks", json={})
    assert response.status_code == 422


def test_documents_list_empty():
    """Test documents list when empty."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_briefings_placeholder():
    """Test briefings endpoint returns placeholder."""
    response = client.post(
        "/briefings",
        json={"company_name": "Test Corp"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_implemented"
