"""API route handlers."""
import tempfile
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models import VideoInfoRequest, VideoInfoResponse, DownloadRequest
from services.downloader import get_video_info, download_audio
from services.queue import DownloadQueue


router = APIRouter()


@router.post("/video-info", response_model=VideoInfoResponse)
async def fetch_video_info(request: VideoInfoRequest):
    """
    Extract video metadata from YouTube URL.
    
    Args:
        request: VideoInfoRequest containing the YouTube URL
        
    Returns:
        VideoInfoResponse with metadata
        
    Raises:
        HTTPException: 400 if extraction fails
    """
    try:
        info = await get_video_info(str(request.url))
        return VideoInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Global download queue instance
download_queue = DownloadQueue()


@router.post("/download")
async def download_audio_endpoint(request: DownloadRequest):
    """
    Download audio from YouTube URL in specified format/quality.
    
    Args:
        request: DownloadRequest containing url, format, and quality
        
    Returns:
        FileResponse streaming the audio file
        
    Raises:
        HTTPException: 400 if download fails, 503 if queue is busy
    """
    # Check if queue is busy
    if download_queue.is_active():
        raise HTTPException(
            status_code=503,
            detail="Another download is in progress. Please wait."
        )
    
    temp_dir = None
    
    try:
        # Acquire queue lock and download
        async with download_queue:
            # Create temp directory for download
            temp_dir = tempfile.mkdtemp()
            
            # Download audio
            file_path = await download_audio(
                url=str(request.url),
                audio_format=request.format,
                quality=request.quality,
                output_dir=temp_dir
            )
            
            # Determine media type
            media_types = {
                'mp3': 'audio/mpeg',
                'm4a': 'audio/mp4',
                'opus': 'audio/opus',
                'wav': 'audio/wav',
                'best': 'audio/mpeg',
            }
            media_type = media_types.get(request.format, 'audio/mpeg')
            
            # Get filename for Content-Disposition
            filename = Path(file_path).name
            
            # Return file response with background cleanup
            def cleanup():
                """Cleanup temp directory after response is sent."""
                try:
                    if temp_dir and Path(temp_dir).exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass  # Ignore cleanup errors
            
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=filename,
                background=cleanup
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions (503 queue busy)
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        # Clean up temp directory on error
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e))
# Endpoints will be added incrementally
