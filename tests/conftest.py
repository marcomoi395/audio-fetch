"""Shared pytest fixtures for unit/integration tests."""

import pytest

MOCK_VIDEO_INFO = {
    "title": "Test Song",
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


@pytest.fixture()
def mock_video_info(monkeypatch):
    """Override get_video_info to return deterministic data."""
    from unittest.mock import AsyncMock

    import api.routes as routes_module

    mock = AsyncMock(return_value=MOCK_VIDEO_INFO)
    monkeypatch.setattr(routes_module, "get_video_info", mock)
    return mock


@pytest.fixture()
def mock_download_audio(tmp_path, monkeypatch):
    """Override download_audio to create a tiny real file and return its path."""
    from unittest.mock import AsyncMock

    import api.routes as routes_module

    fake_file = tmp_path / "Test Song.mp3"
    fake_file.write_bytes(b"\x00" * 16)

    mock = AsyncMock(return_value=str(fake_file))
    monkeypatch.setattr(routes_module, "download_audio", mock)
    return mock
