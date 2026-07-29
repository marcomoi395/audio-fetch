"""Tests for download API endpoint."""
import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO

from main import app


client = TestClient(app)


class TestDownloadEndpoint:
    """Tests for /api/download endpoint."""
    
    def test_download_success(self):
        """Test successful audio download."""
        # Mock the download process
        mock_file_content = b"fake audio data"
        
        with patch('api.routes.download_audio') as mock_download:
            # Mock download_audio to return a mock file path
            mock_download.return_value = '/tmp/fake/audio.mp3'
            
            with patch('api.routes.FileResponse') as mock_file_response:
                mock_response = MagicMock()
                mock_file_response.return_value = mock_response
                
                response = client.post(
                    '/api/download',
                    json={
                        'url': 'https://youtube.com/watch?v=test',
                        'format': 'mp3',
                        'quality': '0'
                    }
                )
                
                # FileResponse should have been created
                mock_file_response.assert_called_once()
    
    def test_download_queue_busy(self):
        """Test download when queue is busy (503 error)."""
        with patch('api.routes.download_queue') as mock_queue:
            # Simulate queue being busy
            mock_queue.__aenter__.side_effect = asyncio.TimeoutError()
            
            response = client.post(
                '/api/download',
                json={
                    'url': 'https://youtube.com/watch?v=test',
                    'format': 'mp3',
                    'quality': '0'
                }
            )
            
            assert response.status_code == 503
            data = response.json()
            assert 'detail' in data
    
    def test_download_invalid_format(self):
        """Test download with invalid format."""
        response = client.post(
            '/api/download',
            json={
                'url': 'https://youtube.com/watch?v=test',
                'format': 'invalid_format',
                'quality': '0'
            }
        )
        
        # Should return 400 or 422 for invalid format
        assert response.status_code in [400, 422]
    
    def test_download_missing_fields(self):
        """Test download with missing required fields."""
        response = client.post('/api/download', json={})
        
        assert response.status_code == 422  # Validation error
