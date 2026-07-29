"""Pydantic models for request/response validation."""
from typing import Dict, List
from pydantic import BaseModel, HttpUrl


class VideoInfoRequest(BaseModel):
    """Request model for video info endpoint."""
    url: HttpUrl


class VideoInfoResponse(BaseModel):
    """Response model for video info endpoint."""
    title: str
    uploader: str
    duration: int
    thumbnail_url: str
    formats: List[str]
    qualities: Dict[str, str]
# Response models will be added as endpoints are implemented


class DownloadRequest(BaseModel):
    """Request model for download endpoint."""
    url: HttpUrl
    format: str
    quality: str
