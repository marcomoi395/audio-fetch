"""Tests for API endpoints."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestVideoInfoEndpoint:
    """Tests for /api/video-info endpoint."""
    
    def test_video_info_success(self):
        """Test successful video info retrieval."""
        mock_info = {
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'duration': 212,
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'formats': ['mp3', 'm4a', 'opus', 'wav', 'best'],
            'qualities': {
                '0': 'Cao nhất (320kbps)',
                '5': 'Trung bình (192kbps)',
                '9': 'Thấp (128kbps)'
            }
        }
        
        with patch('api.routes.get_video_info', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_info
            
            response = client.post(
                '/api/video-info',
                json={'url': 'https://youtube.com/watch?v=test'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['title'] == 'Test Video'
            assert data['uploader'] == 'Test Channel'
            assert data['duration'] == 212
            assert data['thumbnail_url'] == 'https://example.com/thumb.jpg'
            assert len(data['formats']) == 5
            assert len(data['qualities']) == 3
    
    def test_video_info_invalid_url(self):
        """Test video info with invalid/unavailable video."""
        with patch('api.routes.get_video_info', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("ERROR: Video unavailable")
            
            response = client.post(
                '/api/video-info',
                json={'url': 'https://youtube.com/watch?v=invalid123'}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert 'detail' in data
            assert 'Video unavailable' in data['detail']
    def test_video_info_missing_url(self):
        """Test video info with missing URL field."""
        response = client.post('/api/video-info', json={})
        
        assert response.status_code == 422  # Validation error
