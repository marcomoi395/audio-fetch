"""Tests for download API endpoint."""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestDownloadEndpoint:
    """Tests for /api/download endpoint."""

    def test_download_success(self):
        """Test successful audio download."""
        # Mock the download process

        with patch("api.routes.download_audio") as mock_download:
            # Mock download_audio to return a mock file path
            mock_download.return_value = "/tmp/fake/audio.mp3"

            with patch("api.routes.FileResponse") as mock_file_response:
                mock_response = MagicMock()
                mock_file_response.return_value = mock_response

                client.post(
                    "/api/download",
                    json={
                        "url": "https://youtube.com/watch?v=test",
                        "format": "mp3",
                        "quality": "0",
                        "cookies": "# Netscape HTTP Cookie File\n",
                    },
                )

                # FileResponse should have been created
                mock_file_response.assert_called_once()

    def test_download_queue_busy(self):
        """Test download when queue is busy (503 error)."""
        with patch("api.routes.download_queue") as mock_queue:
            # Simulate queue being busy
            mock_queue.__aenter__.side_effect = asyncio.TimeoutError()

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
            data = response.json()
            assert "detail" in data

    def test_download_invalid_format(self):
        """Test download with invalid format."""
        response = client.post(
            "/api/download",
            json={
                "url": "https://youtube.com/watch?v=test",
                "format": "invalid_format",
                "quality": "0",
                "cookies": "# Netscape HTTP Cookie File\n",
            },
        )

        # Should return 400 or 422 for invalid format
        assert response.status_code in [400, 422]

    def test_download_missing_fields(self):
        """Test download with missing required fields."""
        response = client.post("/api/download", json={})

        assert response.status_code == 422  # Validation error


class TestDownloadFilenameAndCleanup:
    """Tests for ascii filename fallback and temp-dir cleanup paths."""

    def _fake_file(self, tmp_dir: str, name: str = "audio.mp3") -> str:
        path = os.path.join(tmp_dir, name)
        with open(path, "wb") as f:
            f.write(b"\x00" * 8)
        return path

    def test_ascii_fallback_when_title_is_all_non_ascii(self):
        """Filename header uses 'download.mp3' when title strips to empty ASCII."""
        # Chinese/Vietnamese title → NFKD encode → all bytes stripped → empty ascii_name
        with tempfile.TemporaryDirectory() as tmp_dir:
            # File named with non-ASCII chars stripped → empty → fallback
            fake_path = self._fake_file(tmp_dir, "日本語タイトル.mp3")

            with patch("api.routes.download_audio", new_callable=AsyncMock) as mock_dl:
                mock_dl.return_value = fake_path

                response = client.post(
                    "/api/download",
                    json={
                        "url": "https://youtube.com/watch?v=test",
                        "format": "mp3",
                        "quality": "0",
                        "cookies": "# Netscape HTTP Cookie File\n",
                    },
                )

                assert response.status_code == 200
                cd = response.headers.get("content-disposition", "")
                assert "download.mp3" in cd

    def test_ascii_preserved_when_title_has_ascii_chars(self):
        """Filename header keeps ASCII portion of a mixed title."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_path = self._fake_file(tmp_dir, "My Song.mp3")

            with patch("api.routes.download_audio", new_callable=AsyncMock) as mock_dl:
                mock_dl.return_value = fake_path

                response = client.post(
                    "/api/download",
                    json={
                        "url": "https://youtube.com/watch?v=test",
                        "format": "mp3",
                        "quality": "0",
                        "cookies": "# Netscape HTTP Cookie File\n",
                    },
                )

                assert response.status_code == 200
                cd = response.headers.get("content-disposition", "")
                assert "My Song.mp3" in cd

    def test_cleanup_on_download_exception(self):
        """Temp dir is removed when download_audio raises an exception."""
        created_dirs = []

        real_mkdtemp = tempfile.mkdtemp

        def tracking_mkdtemp():
            d = real_mkdtemp()
            created_dirs.append(d)
            return d

        with patch("api.routes.tempfile.mkdtemp", side_effect=tracking_mkdtemp):
            with patch("api.routes.download_audio", new_callable=AsyncMock) as mock_dl:
                mock_dl.side_effect = Exception("download failed")

                response = client.post(
                    "/api/download",
                    json={
                        "url": "https://youtube.com/watch?v=test",
                        "format": "mp3",
                        "quality": "0",
                        "cookies": "# Netscape HTTP Cookie File\n",
                    },
                )

                assert response.status_code == 400
                # temp dir must have been cleaned up
                for d in created_dirs:
                    assert not os.path.exists(d), f"Temp dir not cleaned: {d}"

    def test_cleanup_on_503_queue_busy(self):
        """503 path: HTTPException re-raise still cleans up any created temp dir."""
        from services.queue import DownloadQueue

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
        finally:
            DownloadQueue._active = False
