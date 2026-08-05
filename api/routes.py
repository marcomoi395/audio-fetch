import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from api.models import DownloadRequest, VideoInfoRequest, VideoInfoResponse
from desktop.tier_strategy import TierStrategy
from services.downloader import download_audio_with_tiers, get_video_info
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
        HTTPException: 400 if extraction fails or cookies are invalid
    """
    # Cookies are optional - will use tier-based approach if not provided

    try:
        info = await get_video_info(str(request.url), cookies=request.cookies)
        return VideoInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
        HTTPException: 400 if download fails or cookies are invalid, 503 if queue is busy
    """
    # Cookies are optional - will use tier-based approach if not provided

    # Check if queue is busy
    if download_queue.is_active():
        raise HTTPException(status_code=503, detail="Another download is in progress. Please wait.")

    temp_dir = None

    try:
        async with download_queue:
            # Create temp directory for download
            temp_dir = tempfile.mkdtemp()

            # Initialize tier strategy (enable all tiers for maximum success rate)
            strategy = TierStrategy(
                browser="chrome",
                tier2_enabled=True,
                tier3_enabled=True,
            )

            # Download audio using tier-based approach with fallback
            result = await download_audio_with_tiers(
                url=str(request.url),
                quality=request.quality,
                format_name=request.format,
                output_dir=temp_dir,
                strategy=strategy,
            )

            # Check if download succeeded
            if not result["success"]:
                raise Exception(result.get("error", "Download failed after all tiers"))

            file_path = result["file_path"]

            # Determine media type
            media_types = {
                "mp3": "audio/mpeg",
                "m4a": "audio/mp4",
                "opus": "audio/opus",
                "wav": "audio/wav",
                "best": "audio/mpeg",
            }
            media_type = media_types.get(request.format, "audio/mpeg")

            # Get filename for Content-Disposition with proper Unicode encoding
            filename = Path(file_path).name

            # Define cleanup function
            def cleanup():
                """Cleanup temp directory after response is sent."""
                try:
                    if temp_dir and Path(temp_dir).exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass  # Ignore cleanup errors

            # Create FileResponse
            response = FileResponse(
                path=file_path, media_type=media_type, background=BackgroundTask(cleanup)
            )

            # Set Content-Disposition with UTF-8 support (RFC 5987)
            import unicodedata
            import urllib.parse

            # Convert to ASCII fallback - strip accents
            ascii_name = (
                unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
            )
            # Fallback when no real stem survives ASCII stripping
            p = Path(ascii_name)
            if not p.suffix or not p.stem.strip().lstrip("."):
                ascii_name = "download.mp3"

            # UTF-8 encoded filename for modern browsers (RFC 5987)
            utf8_encoded = urllib.parse.quote(filename)

            # Set both for maximum compatibility
            response.headers["Content-Disposition"] = (
                f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_encoded}"
            )
            return response

    except HTTPException:
        # Re-raise HTTP exceptions (503 queue busy)
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        # Clean up temp directory on error
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e)) from e


# Endpoints will be added incrementally
