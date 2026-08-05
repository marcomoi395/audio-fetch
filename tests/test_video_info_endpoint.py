"""Tests to verify /video-info endpoint doesn't pass cookies parameter."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


@pytest.fixture
def client():
    """Create test client."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.mark.asyncio
async def test_video_info_endpoint_no_cookies_passed():
    """Verify /video-info endpoint doesn't pass cookies to get_video_info."""
    with patch("api.routes.get_video_info", new_callable=AsyncMock) as mock_get_info:
        mock_get_info.return_value = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 120,
            "thumbnail_url": "https://example.com/thumb.jpg",
            "formats": ["mp3", "m4a"],
            "qualities": {"0": "320kbps", "5": "192kbps", "9": "128kbps"},
        }

        from api.models import VideoInfoRequest
        from api.routes import fetch_video_info

        request = VideoInfoRequest(url="https://youtube.com/watch?v=test")
        await fetch_video_info(request)

        # Verify get_video_info was called with only url parameter
        mock_get_info.assert_called_once()
        call_args = mock_get_info.call_args

        # Should have only 1 positional argument (url)
        assert len(call_args.args) == 1
        assert call_args.args[0] == "https://youtube.com/watch?v=test"

        # Should have no keyword arguments (no cookies=)
        assert len(call_args.kwargs) == 0
