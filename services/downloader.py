"""YouTube audio downloader service using yt-dlp."""

import asyncio
import logging

from typing import Any

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
    Extract video metadata from YouTube URL without downloading.

    Args:
        url: YouTube video URL

    Returns:
        Dictionary containing video metadata

    Raises:
        Exception: If URL is invalid or extraction fails
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    try:
        # Run yt-dlp in thread pool since it's blocking I/O
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await asyncio.to_thread(extract)

        # Extract relevant metadata
        return {
            "title": info.get("title", "Unknown"),
            "uploader": info.get("uploader", "Unknown"),
            "duration": info.get("duration", 0),
            "thumbnail_url": info.get("thumbnail", ""),
            "formats": list(SUPPORTED_FORMATS.keys()),
            "qualities": QUALITY_LEVELS,
        }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        # Parse common yt-dlp errors for user-friendly messages
        if "Video unavailable" in error_msg:
            raise Exception("Video unavailable. It may have been deleted or set to private.") from e
        elif "This video is private" in error_msg:
            raise Exception("This video is private and cannot be downloaded.") from e
        elif "age-restricted" in error_msg.lower():
            raise Exception("Age-restricted video. Cannot download this content.") from e
        elif "This live event will begin" in error_msg:
            raise Exception(
                "This livestream hasn't started yet. Please try again when it's live."
            ) from e
        elif "Premieres in" in error_msg:
            raise Exception(
                "This video will premiere later. Please try again when it's released."
            ) from e
        else:
            raise Exception(f"Failed to extract video info: {error_msg}") from e
    except Exception as e:
        # Generic error fallback
        raise Exception(f"Unknown error: {e!s}") from e


async def download_audio(
    url: str, audio_format: str = "mp3", quality: str = "0", output_dir: str | None = None
) -> str:
    """
    Download audio from YouTube URL.

    Args:
        url: YouTube video URL
        audio_format: Audio format (mp3, m4a, opus, wav, best)
        quality: Audio quality (0=highest, 5=medium, 9=low)
        output_dir: Directory to save file (temp dir if None)

    Returns:
        Path to downloaded audio file

    Raises:
        Exception: If download fails
    """
    import tempfile
    from pathlib import Path

    # Create temp directory if not provided
    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Output template - single file only (no playlist support for web)
    output_template = str(output_path / "%(id)s.%(ext)s")

    # Configure yt-dlp options
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,  # Web version doesn't support playlists
        "quiet": True,
        "no_warnings": True,
    }

    # Configure post-processor based on format
    postprocessors: list[dict[str, str]] = []
    if audio_format != "best":
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": quality,
            }
        )

    # Add metadata embedding (always enabled for web)
    postprocessors.append(
        {
            "key": "FFmpegMetadata",
            "add_metadata": "True",
        }
    )

    # Add thumbnail embedding (always enabled for web)
    postprocessors.append(
        {
            "key": "EmbedThumbnail",
        }
    )

    ydl_opts["postprocessors"] = postprocessors
    ydl_opts["writethumbnail"] = True

    try:
        # Run yt-dlp in thread pool since it's blocking I/O
        def download() -> str:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info to get final filename
                info = ydl.extract_info(url, download=False)

                # Download the audio
                ydl.download([url])

                # Sanitize title for filename (keep Unicode, remove only problematic chars)
                title = info.get("title", "audio")
                # Remove only characters that are illegal in filenames
                illegal_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
                safe_title = title
                for char in illegal_chars:
                    safe_title = safe_title.replace(char, "_")

                # Strip whitespace and underscores from both ends
                safe_title = safe_title.strip().strip("_")

                if not safe_title or len(safe_title) < 2:
                    safe_title = info.get("id", "audio")

                # Find the actual downloaded file (yt-dlp may change extension)
                # Filter for audio files only (exclude thumbnails, etc.)
                import glob

                video_id = info.get("id", "unknown")
                pattern = str(output_path / f"{video_id}.*")
                all_files = glob.glob(pattern)

                logger.debug("Looking for files matching: %s", pattern)
                logger.debug("Found files: %s", all_files)
                logger.debug("Safe title: %s", safe_title)

                # Filter for audio extensions only
                audio_extensions = [".mp3", ".m4a", ".opus", ".wav", ".webm", ".ogg"]
                audio_files = [
                    f for f in all_files if any(f.lower().endswith(ext) for ext in audio_extensions)
                ]

                logger.debug("Audio files after filter: %s", audio_files)

                if audio_files:
                    # Get the actual downloaded audio file
                    actual_file = Path(audio_files[0])
                    final_ext = actual_file.suffix
                    final_path = output_path / f"{safe_title}{final_ext}"

                    logger.debug("Renaming %s -> %s", actual_file, final_path)

                    # Rename file
                    if actual_file.exists():
                        actual_file.rename(final_path)
                        logger.debug("Rename successful, returning: %s", final_path)
                        return str(final_path)
                    else:
                        logger.debug("File doesn't exist: %s", actual_file)

                # Fallback: return any matching file or raise error
                if all_files:
                    logger.debug("Using fallback, returning first file: %s", all_files[0])
                    return str(all_files[0])

                logger.debug("No files found at all!")
                raise Exception(f"Downloaded file not found in {output_path}. Pattern: {pattern}")

        file_path = await asyncio.to_thread(download)
        return file_path

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        # Parse common yt-dlp errors for user-friendly messages
        if "Video unavailable" in error_msg:
            raise Exception("Video unavailable. It may have been deleted or set to private.") from e
        elif "This video is private" in error_msg:
            raise Exception("This video is private and cannot be downloaded.") from e
        elif "Postprocessing" in error_msg:
            raise Exception("Audio format conversion error. Please try a different format.") from e
        elif "FFmpeg" in error_msg or "ffmpeg" in error_msg:
            raise Exception(
                "FFmpeg error while processing audio. Please check FFmpeg installation."
            ) from e
        elif "HTTP Error 429" in error_msg:
            raise Exception(
                "YouTube is rate limiting downloads. Please try again in a few minutes."
            ) from e
        elif "network" in error_msg.lower() or "timed out" in error_msg.lower():
            raise Exception(
                "Network connection error. Please check your internet connection and try again."
            ) from e
        else:
            raise Exception(f"Download error: {error_msg}") from e
    except Exception as e:
        # Generic error fallback
        if "Failed to download audio" not in str(e):
            raise Exception(f"Unknown error: {e!s}") from e
        raise
