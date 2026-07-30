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
    lines = raw_content.split("\n")
    cleaned_lines = []

    for line in lines:
        # Skip empty lines
        if not line.strip():
            cleaned_lines.append(line)
            continue

        # Handle #HttpOnly_ prefix - these are actual cookies, not comments
        if line.startswith("#HttpOnly_"):
            # Remove the #HttpOnly_ prefix to make it a valid cookie line
            cleaned_line = line[len("#HttpOnly_") :]
            cleaned_lines.append(cleaned_line)
        else:
            # Keep regular comment lines and normal cookie lines as-is
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


@contextlib.contextmanager
def youtube_cookies_context(cookies: str) -> Generator[str, None, None]:
    """
    Context manager that yields the path to a YouTube cookies temp file.

    Args:
        cookies: Netscape-format cookie string from user (required)

    Yields:
        Path to temporary cookie file
    """
    # Clean and write to temp file
    cleaned_cookies = _clean_cookie_content(cookies)
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


async def get_video_info(url: str, cookies: str) -> dict[str, Any]:
    """
    Get video information using yt-dlp.

    Args:
        url: YouTube video URL
        cookies: Netscape-format cookie string (required)
    """
    with youtube_cookies_context(cookies=cookies) as cookie_path:
        ydl_opts: dict[str, Any] = {
            "quiet": False,
            "verbose": True,
            "no_warnings": False,
            "extract_flat": False,
            "nocheckcertificate": True,
            "prefer_insecure": False,
            "cookiefile": cookie_path,
            "js_runtimes": {"node": {}},  # Enable Node.js for JavaScript challenge solving
        }

        logger.info(f"Using provided cookies for {url}")

        try:
            logger.info(f"Extracting info for {url}...")
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
    url: str,
    cookies: str,
    audio_format: str = "mp3",
    quality: str = "0",
    output_dir: str | None = None,
) -> str:
    """
    Download audio from YouTube and optionally convert it.

    Args:
        url: YouTube video URL
        audio_format: Audio format (mp3, m4a, opus, wav, best)
        quality: Quality level (0=highest, 5=medium, 9=lowest)
        output_dir: Directory to save file
        cookies: Netscape-format cookie string (required)
    """
    if not output_dir:
        output_dir = os.getcwd()

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    output_template = str(output_path / "%(title)s.%(ext)s")

    with youtube_cookies_context(cookies=cookies) as cookie_path:
        ydl_opts: dict[str, Any] = {
            "outtmpl": output_template,
            "quiet": False,
            "no_warnings": False,
            "cookiefile": cookie_path,
            "js_runtimes": {"node": {}},  # Enable Node.js for JavaScript challenge solving
        }

        logger.info(f"Using provided cookies for {url}")

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
            logger.error(f"Download failed for {url}: {e}")
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

        return str(filename)
