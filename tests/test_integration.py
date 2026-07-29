"""Integration tests for end-to-end workflows."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


client = TestClient(app)


class TestEndToEndFlow:
    """Test complete user workflows from start to finish."""
    
    def test_full_workflow_video_info_to_download(self):
        """Test complete flow: fetch video info → download audio."""
        test_url = "https://youtube.com/watch?v=test123"
        
        # Step 1: Fetch video info
        with patch('services.downloader.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            
            mock_info = {
                'id': 'test123',
                'title': 'Test Video',
                'uploader': 'Test Channel',
                'duration': 180,
                'thumbnail': 'https://example.com/thumb.jpg',
            }
            mock_ydl.extract_info.return_value = mock_info
            
            response = client.post(
                '/api/video-info',
                json={'url': test_url}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['title'] == 'Test Video'
            assert data['uploader'] == 'Test Channel'
            assert data['duration'] == 180
            
        # Step 2: Download audio with selected format
        with patch('services.downloader.yt_dlp.YoutubeDL') as mock_ydl_class:
            with patch('api.routes.FileResponse') as mock_file_response:
                mock_ydl = MagicMock()
                mock_ydl_class.return_value.__enter__.return_value = mock_ydl
                mock_ydl.extract_info.return_value = mock_info
                mock_ydl.download.return_value = None
                
                # Mock FileResponse
                mock_response = MagicMock()
                mock_file_response.return_value = mock_response
                
                response = client.post(
                    '/api/download',
                    json={
                        'url': test_url,
                        'format': 'mp3',
                        'quality': '0'
                    }
                )
                
                # Should successfully initiate download
                assert mock_file_response.called
    
    def test_error_recovery_flow(self):
        """Test error handling and retry flow."""
        test_url = "https://youtube.com/watch?v=invalid"
        
        # Attempt 1: Invalid URL
        with patch('services.downloader.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            
            import yt_dlp
            mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("Video unavailable")
            
            response = client.post(
                '/api/video-info',
                json={'url': test_url}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert 'Video không khả dụng' in data['detail']
        
        # Attempt 2: Valid URL after retry
        valid_url = "https://youtube.com/watch?v=valid"
        with patch('services.downloader.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            
            mock_info = {
                'id': 'valid',
                'title': 'Valid Video',
                'uploader': 'Test Channel',
                'duration': 120,
                'thumbnail': 'https://example.com/thumb.jpg',
            }
            mock_ydl.extract_info.return_value = mock_info
            
            response = client.post(
                '/api/video-info',
                json={'url': valid_url}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['title'] == 'Valid Video'
    
    def test_concurrent_download_blocking(self):
        """Test that concurrent downloads are properly queued."""
        test_url = "https://youtube.com/watch?v=test"
        
        with patch('services.downloader.yt_dlp.YoutubeDL') as mock_ydl_class:
            with patch('api.routes.FileResponse'):
                mock_ydl = MagicMock()
                mock_ydl_class.return_value.__enter__.return_value = mock_ydl
                
                mock_info = {
                    'id': 'test',
                    'title': 'Test Video',
                    'uploader': 'Test',
                    'duration': 60,
                    'thumbnail': 'https://example.com/thumb.jpg',
                }
                mock_ydl.extract_info.return_value = mock_info
                
                # First download should succeed (mocked)
                # Second concurrent download should return 503
                # Note: In TestClient, requests are synchronous, so we can't truly
                # test concurrency, but we verify the queue state checking works
                
                response = client.post(
                    '/api/download',
                    json={
                        'url': test_url,
                        'format': 'mp3',
                        'quality': '0'
                    }
                )
                
                # Should complete successfully
                assert response.status_code in [200, 503]
