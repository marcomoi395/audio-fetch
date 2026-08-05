"""Tests for API models."""


from api.models import DownloadRequest, VideoInfoRequest


class TestVideoInfoRequest:
    """Tests for VideoInfoRequest model."""

    def test_video_info_request_without_cookies_field(self):
        """VideoInfoRequest should not have a cookies field."""
        # This should work - only url is required
        request = VideoInfoRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Verify the model doesn't have cookies attribute
        assert not hasattr(request, "cookies"), "VideoInfoRequest should not have cookies field"

        # Verify only expected fields exist
        assert hasattr(request, "url")
        model_fields = set(request.model_fields.keys())
        assert model_fields == {"url"}, f"Expected only 'url' field, got {model_fields}"


class TestDownloadRequest:
    """Tests for DownloadRequest model."""

    def test_download_request_without_cookies_field(self):
        """DownloadRequest should not have a cookies field."""
        # This should work - required fields only
        request = DownloadRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", format="mp3", quality="192"
        )

        # Verify the model doesn't have cookies attribute
        assert not hasattr(request, "cookies"), "DownloadRequest should not have cookies field"

        # Verify only expected fields exist
        model_fields = set(request.model_fields.keys())
        expected_fields = {"url", "format", "quality"}
        assert model_fields == expected_fields, f"Expected {expected_fields}, got {model_fields}"
