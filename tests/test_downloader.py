"""Tests for downloader service."""
import pytest
from unittest.mock import AsyncMock, patch

from services.downloader import get_video_info, format_duration


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
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'duration': 212,
            'thumbnail': 'https://example.com/thumb.jpg',
        }
        
        # Mock the YoutubeDL context manager and extract_info
        with patch('services.downloader.yt_dlp.YoutubeDL') as mock_ydl_class:
            # Create a mock instance that acts as a context manager
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__ = lambda self: mock_instance
            mock_instance.__exit__ = lambda self, *args: None
            mock_instance.extract_info = lambda url, download: mock_info
            
            result = await get_video_info('https://youtube.com/watch?v=test')
            
            assert result['title'] == 'Test Video'
            assert result['uploader'] == 'Test Channel'
            assert result['duration'] == 212
            assert result['thumbnail_url'] == 'https://example.com/thumb.jpg'
            assert 'formats' in result
            assert len(result['formats']) == 5
            assert 'qualities' in result
            assert len(result['qualities']) == 3
    
    @pytest.mark.asyncio
    async def test_get_video_info_invalid_url(self):
        """Test video info extraction with invalid URL."""
        with patch('services.downloader.yt_dlp.YoutubeDL') as mock_ydl_class:
            # Create a mock that raises an exception
            mock_instance = mock_ydl_class.return_value
            mock_instance.__enter__ = lambda self: mock_instance
            mock_instance.__exit__ = lambda self, *args: None
            mock_instance.extract_info = lambda url, download: (_ for _ in ()).throw(
                Exception("ERROR: Invalid URL")
            )
            
            with pytest.raises(Exception) as exc_info:
                await get_video_info('invalid-url')
            
            assert "Invalid URL" in str(exc_info.value)
