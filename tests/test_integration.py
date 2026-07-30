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
        with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get_info:
            mock_get_info.return_value = mock_info

            response = client.post(
                "/api/video-info",
                json={"url": test_url, "cookies": "# Netscape HTTP Cookie File\n"},
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

            with patch("api.routes.download_audio", new_callable=AsyncMock) as mock_dl:
                mock_dl.return_value = fake_path

                response = client.post(
                    "/api/download",
                    json={
                        "url": test_url,
                        "format": "mp3",
                        "quality": "0",
                        "cookies": "# Netscape HTTP Cookie File\n",
                    },
                )

                assert response.status_code == 200
                assert "audio" in response.headers.get("content-type", "")

    def test_error_recovery_flow(self):
        """Test error handling and retry flow."""
        test_url = "https://youtube.com/watch?v=invalid"

        # Attempt 1: video unavailable
        with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get_info:
            mock_get_info.side_effect = Exception("Video unavailable")

            response = client.post(
                "/api/video-info",
                json={"url": test_url, "cookies": "# Netscape HTTP Cookie File\n"},
            )

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

        with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get_info:
            mock_get_info.return_value = valid_info

            response = client.post(
                "/api/video-info",
                json={"url": valid_url, "cookies": "# Netscape HTTP Cookie File\n"},
            )

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
                    "cookies": "# Netscape HTTP Cookie File\n",
                },
            )
            assert response.status_code == 503
            assert "in progress" in response.json()["detail"]
        finally:
            # Always restore so other tests aren't affected
            DownloadQueue._active = False

    def test_cookie_flow_end_to_end(self):
        """Test complete flow with user-provided cookies."""
        test_url = "https://youtube.com/watch?v=test123"
        test_cookies = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tCONSENT\tYES+1"

        mock_info = {
            "title": "Test Video with Cookies",
            "uploader": "Test Channel",
            "duration": 240,
            "thumbnail_url": "https://i.ytimg.com/test.jpg",
            "formats": ["mp3", "wav"],
            "qualities": {"0": "High (320kbps)", "5": "Medium (192kbps)"},
        }

        # Step 1: Fetch video info with cookies
        with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get_info:
            mock_get_info.return_value = mock_info

            response = client.post(
                "/api/video-info",
                json={"url": test_url, "cookies": test_cookies},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Video with Cookies"

            # Verify cookies were passed to downloader
            mock_get_info.assert_called_once()
            call_args = mock_get_info.call_args
            assert call_args[0][0] == test_url
            assert call_args[1]["cookies"] == test_cookies

        # Step 2: Download with cookies
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_path = _make_fake_audio_file(tmp_dir, "Test Video with Cookies.mp3")

            with patch("api.routes.download_audio", new_callable=AsyncMock) as mock_download:
                mock_download.return_value = fake_path

                response = client.post(
                    "/api/download",
                    json={
                        "url": test_url,
                        "format": "mp3",
                        "quality": "0",
                        "cookies": test_cookies,
                    },
                )

                assert response.status_code == 200
                assert "audio" in response.headers.get("content-type", "")

                # Verify cookies were passed to downloader
                mock_download.assert_called_once()
                call_args = mock_download.call_args
                assert call_args[1]["cookies"] == test_cookies

    def test_cookie_flow_without_cookies(self):
        """Test that endpoints reject requests without cookies (cookies now required)."""
        test_url = "https://youtube.com/watch?v=test456"

        # Verify video info rejects missing cookies with 422 validation error
        response = client.post(
            "/api/video-info",
            json={"url": test_url},  # No cookies field
        )

        assert response.status_code == 422
        data = response.json()
        assert "cookies" in str(data).lower()

        # Verify download also rejects missing cookies
        response = client.post(
            "/api/download",
            json={"url": test_url, "format": "mp3", "quality": "0"},  # No cookies field
        )

        assert response.status_code == 422
        data = response.json()
        assert "cookies" in str(data).lower()
