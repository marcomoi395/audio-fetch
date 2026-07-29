"""Basic test to verify FastAPI app initialization."""
from fastapi.testclient import TestClient

from main import app


def test_health_endpoint():
    """Test that health endpoint returns correct structure."""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ffmpeg_available" in data
    assert "queue_active" in data
    assert data["queue_active"] is False
    assert isinstance(data["ffmpeg_available"], bool)


def test_app_initialization():
    """Test that FastAPI app initializes without errors."""
    assert app.title == "Audio Fetch"
    assert app.version == "1.0.0"


def test_root_serves_html():
    """Test that GET / returns 200 with HTML content."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
