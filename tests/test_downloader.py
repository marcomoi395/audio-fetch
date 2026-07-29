"""Tests for downloader service."""

from unittest.mock import MagicMock, patch

import pytest
import yt_dlp

from services.downloader import download_audio, format_duration, get_video_info


class TestFormatDuration:
    """Tests for duration formatting helper."""

    def test_format_duration_minutes_only(self):
        """Test formatting duration with minutes and seconds only."""
        assert format_duration(125) == "02:05"

    def test_format_duration_with_hours(self):
        """Test formatting duration with hours."""
        assert format_duration(3725) == "01:02:05"

    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "Unknown"

    def test_format_duration_none(self):
        """Test formatting None duration."""
        assert format_duration(None) == "Unknown"


class TestGetVideoInfo:
    """Tests for get_video_info function."""

    @pytest.mark.asyncio
    async def test_get_video_info_success(self):
        """Test successful video info extraction."""
        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 212,
            "thumbnail": "https://example.com/thumb.jpg",
        }

        # Mock the YoutubeDL context manager and extract_info
        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            # Create a mock instance that acts as a context manager
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__ = lambda self: mock_instance
            mock_instance.__exit__ = lambda self, *args: None
            mock_instance.extract_info = lambda url, download: mock_info

            result = await get_video_info("https://youtube.com/watch?v=test")

            assert result["title"] == "Test Video"
            assert result["uploader"] == "Test Channel"
            assert result["duration"] == 212
            assert result["thumbnail_url"] == "https://example.com/thumb.jpg"
            assert "formats" in result
            assert len(result["formats"]) == 5
            assert "qualities" in result
            assert len(result["qualities"]) == 3

    @pytest.mark.asyncio
    async def test_get_video_info_invalid_url(self):
        """Test video info extraction with invalid URL."""
        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            # Create a mock that raises an exception
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__ = lambda self: mock_instance
            mock_instance.__exit__ = lambda self, *args: None
            mock_instance.extract_info = lambda url, download: (_ for _ in ()).throw(
                Exception("ERROR: Invalid URL")
            )

            with pytest.raises(Exception) as exc_info:
                await get_video_info("invalid-url")

            assert "Invalid URL" in str(exc_info.value)


class TestGetVideoInfoErrorBranches:
    """Test DownloadError message parsing in get_video_info (lines 91-100)."""

    def _make_ydl_mock(self, side_effect):
        """Return a patched YoutubeDL that raises side_effect on extract_info."""
        mock_instance = MagicMock()
        mock_instance.__enter__ = lambda s: mock_instance
        mock_instance.__exit__ = lambda s, *a: None
        mock_instance.extract_info.side_effect = side_effect
        return mock_instance

    @pytest.mark.asyncio
    async def test_video_unavailable(self):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._make_ydl_mock(yt_dlp.utils.DownloadError("Video unavailable"))
            with pytest.raises(Exception, match="Video unavailable"):
                await get_video_info("https://youtube.com/watch?v=x")

    @pytest.mark.asyncio
    async def test_private_video(self):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._make_ydl_mock(
                yt_dlp.utils.DownloadError("This video is private")
            )
            with pytest.raises(Exception, match="private"):
                await get_video_info("https://youtube.com/watch?v=x")

    @pytest.mark.asyncio
    async def test_age_restricted(self):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._make_ydl_mock(
                yt_dlp.utils.DownloadError("age-restricted content")
            )
            with pytest.raises(Exception, match="Age-restricted"):
                await get_video_info("https://youtube.com/watch?v=x")

    @pytest.mark.asyncio
    async def test_live_not_started(self):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._make_ydl_mock(
                yt_dlp.utils.DownloadError("This live event will begin")
            )
            with pytest.raises(Exception, match="livestream"):
                await get_video_info("https://youtube.com/watch?v=x")

    @pytest.mark.asyncio
    async def test_premiere_not_released(self):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._make_ydl_mock(
                yt_dlp.utils.DownloadError("Premieres in 2 hours")
            )
            with pytest.raises(Exception, match="premiere"):
                await get_video_info("https://youtube.com/watch?v=x")

    @pytest.mark.asyncio
    async def test_generic_download_error(self):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._make_ydl_mock(
                yt_dlp.utils.DownloadError("Some random yt-dlp error")
            )
            with pytest.raises(Exception, match="Failed to extract video info"):
                await get_video_info("https://youtube.com/watch?v=x")


class TestDownloadAudioErrorBranches:
    """Test DownloadError message parsing in download_audio (lines 248-265)."""

    def _patch_download(self, side_effect):
        """Patch yt_dlp.YoutubeDL so the inner download() raises side_effect."""
        mock_instance = MagicMock()
        mock_instance.__enter__ = lambda s: mock_instance
        mock_instance.__exit__ = lambda s, *a: None
        # extract_info (called first) succeeds; download() raises
        mock_instance.extract_info.return_value = {
            "id": "abc",
            "title": "T",
            "uploader": "U",
            "duration": 60,
            "thumbnail": "https://x.com/t.jpg",
        }
        mock_instance.download.side_effect = side_effect
        return mock_instance

    @pytest.mark.asyncio
    async def test_download_video_unavailable(self, tmp_path):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._patch_download(yt_dlp.utils.DownloadError("Video unavailable"))
            with pytest.raises(Exception, match="Video unavailable"):
                await download_audio("https://youtube.com/watch?v=x", output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_download_private_video(self, tmp_path):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._patch_download(
                yt_dlp.utils.DownloadError("This video is private")
            )
            with pytest.raises(Exception, match="private"):
                await download_audio("https://youtube.com/watch?v=x", output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_download_postprocessing_error(self, tmp_path):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._patch_download(
                yt_dlp.utils.DownloadError("Postprocessing: ffmpeg failed")
            )
            with pytest.raises(Exception, match="Audio format conversion error"):
                await download_audio("https://youtube.com/watch?v=x", output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_download_ffmpeg_error(self, tmp_path):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._patch_download(yt_dlp.utils.DownloadError("ffmpeg not found"))
            with pytest.raises(Exception, match="FFmpeg error"):
                await download_audio("https://youtube.com/watch?v=x", output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_download_rate_limit(self, tmp_path):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._patch_download(
                yt_dlp.utils.DownloadError("HTTP Error 429: Too Many Requests")
            )
            with pytest.raises(Exception, match="rate limiting"):
                await download_audio("https://youtube.com/watch?v=x", output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_download_network_error(self, tmp_path):
        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = self._patch_download(
                yt_dlp.utils.DownloadError("network connection timed out")
            )
            with pytest.raises(Exception, match="Network connection error"):
                await download_audio("https://youtube.com/watch?v=x", output_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_download_file_not_found_after_download(self, tmp_path):
        """download() succeeds but leaves no audio file → should raise."""
        mock_instance = MagicMock()
        mock_instance.__enter__ = lambda s: mock_instance
        mock_instance.__exit__ = lambda s, *a: None
        mock_instance.extract_info.return_value = {
            "id": "abc",
            "title": "T",
            "uploader": "U",
            "duration": 60,
            "thumbnail": "https://x.com/t.jpg",
        }
        mock_instance.download.return_value = None  # "success", but creates no file

        with patch("services.downloader.yt_dlp.YoutubeDL") as cls:
            cls.return_value = mock_instance
            with pytest.raises(Exception, match="not found"):
                await download_audio("https://youtube.com/watch?v=x", output_dir=str(tmp_path))
