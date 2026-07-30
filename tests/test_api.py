"""Tests for API endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestVideoInfoEndpoint:
    """Tests for /api/video-info endpoint."""

    def test_video_info_success(self):
        """Test successful video info retrieval."""
        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 212,
            "thumbnail_url": "https://example.com/thumb.jpg",
            "formats": ["mp3", "m4a", "opus", "wav", "best"],
            "qualities": {
                "0": "Cao nhất (320kbps)",
                "5": "Trung bình (192kbps)",
                "9": "Thấp (128kbps)",
            },
        }

        with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_info

            response = client.post(
                "/api/video-info",
                json={"url": "https://youtube.com/watch?v=test", "cookies": "session_token=abc123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Video"
            assert data["uploader"] == "Test Channel"
            assert data["duration"] == 212
            assert data["thumbnail_url"] == "https://example.com/thumb.jpg"
            assert len(data["formats"]) == 5
            assert len(data["qualities"]) == 3

    def test_video_info_invalid_url(self):
        """Test video info with invalid/unavailable video."""
        with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("ERROR: Video unavailable")

            response = client.post(
                "/api/video-info",
                json={
                    "url": "https://youtube.com/watch?v=invalid123",
                    "cookies": "session_token=abc123",
                },
            )

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Video unavailable" in data["detail"]

    def test_video_info_missing_url(self):
        """Test video info with missing URL field."""
        response = client.post("/api/video-info", json={})

        assert response.status_code == 422  # Validation error

    def test_video_info_with_cookies(self):
        """Test video info request requires cookies field."""
        from api.models import VideoInfoRequest

        # Test model accepts cookies field and makes it accessible
        request_with_cookies = VideoInfoRequest(
            url="https://youtube.com/watch?v=test",  # type: ignore[arg-type]
            cookies="# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tCONSENT\tYES+1",
        )
        assert hasattr(request_with_cookies, "cookies")
        assert request_with_cookies.cookies is not None

        # Test API endpoint accepts cookies in request
        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 212,
            "thumbnail_url": "https://example.com/thumb.jpg",
            "formats": ["mp3", "m4a", "opus", "wav", "best"],
            "qualities": {
                "0": "Cao nhất (320kbps)",
                "5": "Trung bình (192kbps)",
                "9": "Thấp (128kbps)",
            },
        }

        with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_info

            response = client.post(
                "/api/video-info",
                json={
                    "url": "https://youtube.com/watch?v=test",
                    "cookies": "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tCONSENT\tYES+1",
                },
            )

            assert response.status_code == 200

            # Verify cookies were actually passed to get_video_info
            mock_get.assert_called_once()
            assert (
                mock_get.call_args.kwargs["cookies"]
                == "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tCONSENT\tYES+1"
            )

    def test_video_info_empty_cookies(self):
        """Test video info with empty cookies string."""
        response = client.post(
            "/api/video-info",
            json={
                "url": "https://youtube.com/watch?v=test",
                "cookies": "",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "cookies required" in data["detail"].lower()

    def test_video_info_whitespace_cookies(self):
        """Test video info with whitespace-only cookies string."""
        response = client.post(
            "/api/video-info",
            json={
                "url": "https://youtube.com/watch?v=test",
                "cookies": "   \n\t  ",
            },
        )

        # Route validation should reject whitespace-only cookies
        assert response.status_code == 400
        data = response.json()
        assert "cookies required" in data["detail"].lower()


class TestDownloadEndpointCookieValidation:
    """Tests for /api/download endpoint cookie validation."""

    def test_download_empty_cookies(self):
        """Test download with empty cookies string."""
        response = client.post(
            "/api/download",
            json={
                "url": "https://youtube.com/watch?v=test",
                "format": "mp3",
                "quality": "0",
                "cookies": "",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "cookies required" in data["detail"].lower()

    def test_download_whitespace_cookies(self):
        """Test download with whitespace-only cookies string."""
        response = client.post(
            "/api/download",
            json={
                "url": "https://youtube.com/watch?v=test",
                "format": "mp3",
                "quality": "0",
                "cookies": "   \n\t  ",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "cookies required" in data["detail"].lower()
