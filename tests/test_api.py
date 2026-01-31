"""API endpoint tests."""

from unittest.mock import MagicMock, patch

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


def test_documents_list_empty():
    """Test documents list when empty."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_briefings_endpoint():
    """Test briefings endpoint returns a briefing response."""
    # Mock the LLM calls to avoid hitting the API
    mock_response = MagicMock()
    mock_response.content = """{
        "overview": "Test overview",
        "key_priorities": [],
        "relevant_trends": [],
        "considerations": []
    }"""

    with patch("app.briefings.agents.base.ChatOpenAI") as mock_chat:
        mock_chat.return_value.invoke.return_value = mock_response

        response = client.post(
            "/briefings",
            json={"company_name": "Test Corp"},
        )

    assert response.status_code == 200
    data = response.json()
    # Should have metadata from the orchestrator
    assert "metadata" in data
    assert "company_summary" in data


def test_briefings_health():
    """Test briefings health endpoint."""
    response = client.get("/briefings/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "specialists" in data
