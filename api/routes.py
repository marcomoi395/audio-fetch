"""API route handlers."""
from fastapi import APIRouter, HTTPException

from api.models import VideoInfoRequest, VideoInfoResponse
from services.downloader import get_video_info


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
# Endpoints will be added incrementally
