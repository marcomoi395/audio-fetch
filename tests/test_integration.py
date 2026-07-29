"""Integration tests for end-to-end workflows."""
import os
import tempfile
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _make_fake_audio_file(tmp_dir: str, filename: str = "Test Video.mp3") -> str:
    """Create a real (tiny) temp file so FileResponse can open it."""
    path = os.path.join(tmp_dir, filename)
    with open(path, "wb") as f:
        f.write(b"\x00" * 16)  # minimal fake bytes
    return path


class TestEndToEndFlow:
    """Test complete user workflows from start to finish."""

    def test_full_workflow_video_info_to_download(self):
        """Test complete flow: fetch video info → download audio."""
        test_url = "https://youtube.com/watch?v=test123"

        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 180,
            "thumbnail_url": "https://example.com/thumb.jpg",
            "formats": ["mp3", "m4a", "opus", "wav", "best"],
            "qualities": {
                "0": "Cao nhất (320kbps)",
                "5": "Trung bình (192kbps)",
                "9": "Thấp (128kbps)",
            },
        }

        # Step 1: Fetch video info — mock get_video_info at the service boundary
        with patch(
            "api.routes.get_video_info", new_callable=AsyncMock
        ) as mock_get_info:
            mock_get_info.return_value = mock_info

            response = client.post(
                "/api/video-info",
                json={"url": test_url},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Video"
            assert data["uploader"] == "Test Channel"
            assert data["duration"] == 180

        # Step 2: Download — mock download_audio at the service boundary,
        # create a real temp file so FileResponse has something to serve.
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_path = _make_fake_audio_file(tmp_dir, "Test Video.mp3")

            with patch(
                "api.routes.download_audio", new_callable=AsyncMock
            ) as mock_dl:
                mock_dl.return_value = fake_path

                response = client.post(
                    "/api/download",
                    json={"url": test_url, "format": "mp3", "quality": "0"},
                )

                assert response.status_code == 200
                assert "audio" in response.headers.get("content-type", "")

    def test_error_recovery_flow(self):
        """Test error handling and retry flow."""
        test_url = "https://youtube.com/watch?v=invalid"

        # Attempt 1: video unavailable
        with patch(
            "api.routes.get_video_info", new_callable=AsyncMock
        ) as mock_get_info:
            mock_get_info.side_effect = Exception("Video unavailable")

            response = client.post("/api/video-info", json={"url": test_url})

            assert response.status_code == 400
            data = response.json()
            assert "Video unavailable" in data["detail"]

        # Attempt 2: valid URL after retry
        valid_url = "https://youtube.com/watch?v=valid"
        valid_info = {
            "title": "Valid Video",
            "uploader": "Test Channel",
            "duration": 120,
            "thumbnail_url": "https://example.com/thumb.jpg",
            "formats": ["mp3", "m4a", "opus", "wav", "best"],
            "qualities": {"0": "Cao nhất (320kbps)"},
        }

        with patch(
            "api.routes.get_video_info", new_callable=AsyncMock
        ) as mock_get_info:
            mock_get_info.return_value = valid_info

            response = client.post("/api/video-info", json={"url": valid_url})

            assert response.status_code == 200
            assert response.json()["title"] == "Valid Video"

    def test_concurrent_download_blocking(self):
        """Test that a second download is rejected while one is active."""
        from services.queue import DownloadQueue

        # Force queue into active state
        DownloadQueue._active = True
        try:
            response = client.post(
                "/api/download",
                json={
                    "url": "https://youtube.com/watch?v=test",
                    "format": "mp3",
                    "quality": "0",
                },
            )
            assert response.status_code == 503
            assert "in progress" in response.json()["detail"]
        finally:
            # Always restore so other tests aren't affected
            DownloadQueue._active = False
