"""YouTube audio downloader service using yt-dlp."""

import asyncio
import contextlib
import logging
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any


# Ensure Node.js is in PATH for yt-dlp to use
node_paths = [
    "/home/ym/.local/share/nvm/v22.22.2/bin",
    "/usr/local/bin",
    "/usr/bin",
]
for node_path in node_paths:
    if os.path.exists(node_path) and node_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{node_path}:{os.environ.get('PATH', '')}"

import yt_dlp

logger = logging.getLogger(__name__)


# Format and quality constants from original AudioDownloader
SUPPORTED_FORMATS = {
    "mp3": "MP3 (phổ biến nhất, tương thích tốt)",
    "m4a": "M4A/AAC (chất lượng gốc từ YouTube)",
    "opus": "OPUS (chất lượng cao, file nhỏ)",
    "wav": "WAV (không nén, chất lượng tốt nhất nhưng file lớn)",
    "best": "Định dạng tốt nhất có sẵn (không convert)",
}

QUALITY_LEVELS = {"0": "Cao nhất (320kbps)", "5": "Trung bình (192kbps)", "9": "Thấp (128kbps)"}


def _clean_cookie_content(raw_content: str) -> str:
    """
    Clean cookie content to ensure yt-dlp can parse it correctly.
    Removes #HttpOnly_ prefix from cookie lines while preserving actual comments.
    """
    lines = raw_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            cleaned_lines.append(line)
            continue
            
        # Handle #HttpOnly_ prefix - these are actual cookies, not comments
        if line.startswith('#HttpOnly_'):
            # Remove the #HttpOnly_ prefix to make it a valid cookie line
            cleaned_line = line[len('#HttpOnly_'):]
            cleaned_lines.append(cleaned_line)
        else:
            # Keep regular comment lines and normal cookie lines as-is
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


@contextlib.contextmanager
def youtube_cookies_context() -> Generator[str | None, None, None]:
    """
    Context manager that yields the path to a YouTube cookies file, or None if not available.
    Cookies are now OPTIONAL since android client works without them.
    It prefers YOUTUBE_COOKIES_FILE if set.
    Otherwise, it reads YOUTUBE_COOKIES, writes it to a temp file, yields the temp file path,
    and cleans up the temp file on exit.
    """
    cookie_file = os.getenv("YOUTUBE_COOKIES_FILE")
    cookie_raw = os.getenv("YOUTUBE_COOKIES")

    if cookie_file:
        if not os.path.exists(cookie_file):
            logger.warning(f"Cookie file {cookie_file} not found, continuing without cookies.")
            yield None
        else:
            yield cookie_file
        return

    if cookie_raw:
        # Clean cookie content to remove #HttpOnly_ prefixes
        cleaned_cookies = _clean_cookie_content(cookie_raw)
        
        fd, temp_path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(cleaned_cookies)
            yield temp_path
        finally:
            try:
                os.unlink(temp_path)
            except OSError as e:
                logger.error(f"Failed to delete temp cookie file {temp_path}: {e}")
        return

    # No cookies available - that's OK, android client doesn't need them
    logger.info("No cookies configured, using android client which doesn't require cookies.")
    yield None


def format_duration(seconds: int | None) -> str:
    """
    Format duration from seconds to MM:SS or HH:MM:SS.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if not seconds:
        return "Unknown"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"
async def get_video_info(url: str) -> dict[str, Any]:
    """
    Get video information using yt-dlp.
    Uses android client by default which works without cookies.
    """
    with youtube_cookies_context() as cookie_path:
        ydl_opts: dict[str, Any] = {
            "quiet": False,
            "verbose": True,
            "no_warnings": False,
            "extract_flat": False,
            # Use android client which works without cookies
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                }
            },
            # Additional options
            "nocheckcertificate": True,
            "prefer_insecure": False,
        }
        
        # Only add cookiefile if cookies are available
        # Note: android client doesn't support cookies anyway
        if cookie_path:
            logger.info("Cookies available but android client doesn't use them")

        try:
            logger.info(f"Extracting info for {url} using android client...")
            info = await asyncio.to_thread(_extract_info_sync, url, ydl_opts)
            return info
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Failed to extract info for {url}: {e}")
            raise Exception(str(e)) from e


def _extract_info_sync(url: str, opts: dict[str, Any]) -> dict[str, Any]:
    """Synchronous helper for get_video_info to run in thread."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise Exception("Could not extract video info")
        return {
            "title": info.get("title", "Unknown Title"),
            "uploader": info.get("uploader", "Unknown Artist"),
            "duration": int(info.get("duration") or 0),
            "thumbnail_url": info.get("thumbnail") or "",
            "formats": list(SUPPORTED_FORMATS.keys()),
            "qualities": QUALITY_LEVELS,
        }


async def download_audio(
    url: str, audio_format: str = "mp3", quality: str = "0", output_dir: str | None = None
) -> str:
    """
    Download audio from YouTube and optionally convert it.
    """
    if not output_dir:
        output_dir = os.getcwd()

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    output_template = str(output_path / "%(title)s.%(ext)s")

    with youtube_cookies_context() as cookie_path:
        # Base yt-dlp options - use android client which works without cookies
        ydl_opts: dict[str, Any] = {
            "outtmpl": output_template,
            "quiet": False,
            "no_warnings": False,
            # Use android client which works without cookies
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                }
            },
        }

        # Add format conversion options if needed
        if audio_format != "best" and audio_format != "m4a":
            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                }
            ]

            # Map quality levels based on standard yt-dlp expectations
            # Note: yt-dlp uses 0 for best, 9 for worst
            if quality == "0":
                postprocessors[0]["preferredquality"] = "320"
            elif quality == "5":
                postprocessors[0]["preferredquality"] = "192"
            elif quality == "9":
                postprocessors[0]["preferredquality"] = "128"

            ydl_opts["postprocessors"] = postprocessors

        try:
            logger.info(f"Starting download for {url} in format {audio_format}...")
            return await asyncio.to_thread(_download_sync, url, ydl_opts)
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Failed to download {url}: {e}")
            raise Exception(str(e)) from e


def _download_sync(url: str, opts: dict[str, Any]) -> str:
    """Synchronous helper for download_audio to run in thread."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise Exception("Could not extract video info for download")

        # yt-dlp replaces the extension after conversion
        filename = ydl.prepare_filename(info)

        # If there's a postprocessor converting audio, the output extension changes
        if "postprocessors" in opts:
            for pp in opts["postprocessors"]:
                if pp.get("key") == "FFmpegExtractAudio":
                    base = os.path.splitext(filename)[0]
                    codec = pp.get("preferredcodec", "mp3")
                    filename = f"{base}.{codec}"

        return filename
