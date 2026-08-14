"""Tests for downloader service."""

from unittest.mock import patch

import pytest
import yt_dlp

from services.downloader import (
    download_audio,
    format_duration,
    get_video_info,
)


class TestFormatDuration:
    """Tests for duration formatting helper."""

    def test_format_duration_minutes_only(self):
        assert format_duration(125) == "02:05"

    def test_format_duration_with_hours(self):
        assert format_duration(3725) == "01:02:05"

    def test_format_duration_zero(self):
        assert format_duration(0) == "Unknown"

    def test_format_duration_none(self):
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

        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_instance.extract_info.return_value = mock_info

            result = await get_video_info("https://youtube.com/watch?v=test")

            assert result["title"] == "Test Video"
            assert result["uploader"] == "Test Channel"
            assert result["duration"] == 212
            assert result["thumbnail_url"] == "https://example.com/thumb.jpg"
            assert "formats" in result
            assert "qualities" in result

    @pytest.mark.asyncio
    async def test_get_video_info_invalid_url(self):
        """Test video info extraction with invalid URL propagates yt-dlp error."""
        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError(
                "ERROR: Invalid URL"
            )

            with pytest.raises(Exception, match="Invalid URL"):
                await get_video_info("invalid-url")


class TestDownloadAudio:
    """Test download_audio function."""

    @pytest.mark.asyncio
    async def test_download_audio_success(self, tmp_path):
        """Test successful audio download execution."""
        mock_info = {
            "title": "Test Video",
            "ext": "m4a",
        }

        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_instance.extract_info.return_value = mock_info
            mock_instance.prepare_filename.return_value = str(tmp_path / "Test Video.m4a")

            result = await download_audio(
                "https://youtube.com/watch?v=test",
                audio_format="m4a",
                output_dir=str(tmp_path),
            )

            assert "Test Video.m4a" in result

    @pytest.mark.asyncio
    async def test_download_audio_with_postprocessor(self, tmp_path):
        """Test download audio handles postprocessor extension substitution."""
        mock_info = {
            "title": "Test Video",
            "ext": "webm",
        }

        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_instance.extract_info.return_value = mock_info
            mock_instance.prepare_filename.return_value = str(tmp_path / "Test Video.webm")

            result = await download_audio(
                "https://youtube.com/watch?v=test",
                audio_format="mp3",
                output_dir=str(tmp_path),
            )

            assert result.endswith(".mp3")

    @pytest.mark.asyncio
    async def test_download_audio_error(self, tmp_path):
        """Test download audio error handling."""
        with patch("services.downloader.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError("Video unavailable")

            with pytest.raises(Exception, match="Video unavailable"):
                await download_audio(
                    "https://youtube.com/watch?v=test",
                    output_dir=str(tmp_path),
                )
