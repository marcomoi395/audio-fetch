"""Tests for API models."""

import pytest
from pydantic import ValidationError

from api.models import DownloadRequest, VideoInfoRequest


class TestVideoInfoRequest:
    """Tests for VideoInfoRequest model."""

    def test_requires_cookies_field(self):
        """Test that cookies field is required."""
        with pytest.raises(ValidationError) as exc_info:
            VideoInfoRequest(url="https://youtube.com/watch?v=test")  # type: ignore[call-arg,arg-type]

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("cookies",) for error in errors)
        assert any(error["type"] == "missing" for error in errors)

    def test_accepts_empty_cookies_at_model_level(self):
        """Test that model accepts empty cookies (route validation will reject)."""
        # Pydantic model accepts empty string - route validation handles this
        request = VideoInfoRequest(url="https://youtube.com/watch?v=test", cookies="")  # type: ignore[arg-type]
        assert request.cookies == ""

    def test_accepts_valid_cookies(self):
        """Test that valid cookies are accepted."""
        request = VideoInfoRequest(
            url="https://youtube.com/watch?v=test",  # type: ignore[arg-type]
            cookies="session_token=abc123",
        )
        assert request.cookies == "session_token=abc123"


class TestDownloadRequest:
    """Tests for DownloadRequest model."""

    def test_requires_cookies_field(self):
        """Test that cookies field is required."""
        with pytest.raises(ValidationError) as exc_info:
            DownloadRequest(url="https://youtube.com/watch?v=test", format="m4a", quality="128")  # type: ignore[call-arg,arg-type]

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("cookies",) for error in errors)
        assert any(error["type"] == "missing" for error in errors)

    def test_accepts_empty_cookies_at_model_level(self):
        """Test that model accepts empty cookies (route validation will reject)."""
        # Pydantic model accepts empty string - route validation handles this
        request = DownloadRequest(
            url="https://youtube.com/watch?v=test",  # type: ignore[arg-type]
            format="m4a",
            quality="128",
            cookies="",
        )
        assert request.cookies == ""

    def test_accepts_valid_cookies(self):
        """Test that valid cookies are accepted."""
        request = DownloadRequest(
            url="https://youtube.com/watch?v=test",  # type: ignore[arg-type]
            format="m4a",
            quality="128",
            cookies="session_token=abc123",
        )
        assert request.cookies == "session_token=abc123"
