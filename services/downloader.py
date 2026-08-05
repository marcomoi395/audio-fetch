"""YouTube audio downloader service using yt-dlp."""

import asyncio
import logging
import os
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

from desktop.cookie_extractor import CookieExtractor
from desktop.tier_strategy import DownloadTier, TierStrategy

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
    Get video information using yt-dlp with tier-based approach.

    Args:
        url: YouTube video URL
    """
    ydl_opts: dict[str, Any] = {
        "quiet": False,
        "verbose": True,
        "no_warnings": False,
        "extract_flat": False,
        "nocheckcertificate": True,
        "prefer_insecure": False,
        "js_runtimes": {"node": {}},  # Enable Node.js for JavaScript challenge solving
    }

    logger.info(f"Fetching info without cookies for {url}")
    # Use basic spoofing for no-cookie requests
    ydl_opts["extractor_args"] = {
        "youtube": {
            "player_client": ["mweb", "web"],
        },
    }

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
    audio_format: str = "mp3",
    quality: str = "0",
    output_dir: str | None = None,
    cookies_from_browser: str | None = None,
    player_client: list[str] | None = None,
) -> str:
    """
    Download audio from YouTube and optionally convert it.

    Args:
        url: YouTube video URL
        audio_format: Audio format (mp3, m4a, opus, wav, best)
        quality: Quality level (0=highest, 5=medium, 9=lowest)
        output_dir: Directory to save file
        cookies_from_browser: Browser name for cookie extraction (chrome, firefox, etc)
        player_client: Custom player clients for yt-dlp (e.g., ["ios"], ["android"])
    """
    if not output_dir:
        output_dir = os.getcwd()

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    output_template = str(output_path / "%(title)s.%(ext)s")

    ydl_opts: dict[str, Any] = {
        "outtmpl": output_template,
        "quiet": False,
        "no_warnings": False,
    }

    # Configure authentication method
    if cookies_from_browser:
        # Tier 2: Use browser cookie extraction
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
        logger.info(f"Using cookies from browser: {cookies_from_browser}")

    # Configure player client
    if player_client:
        # Custom player client (e.g., Tier 3)
        ydl_opts["extractor_args"] = {
            "youtube": {
                "player_client": player_client,
            },
        }
        logger.info(f"Using player clients: {player_client}")
    elif not cookies_from_browser:
        # Default Tier 1: Android client (fast, reliable, no auth needed)
        # High quality (format 399+251: 1080p video + opus 160kbps audio)
        logger.info("🥇 TIER 1 CONFIG: Using Android client (default, no auth)")
        ydl_opts["extractor_args"] = {
            "youtube": {
                "player_client": ["android"],
            },
        }
        logger.info("   └─ Player client: ['android']")
        logger.info("   └─ Auth: None required")
        logger.info("   └─ Expected quality: High (format 399+251)")

    # Enable thumbnail download (postprocessors handle embedding)
    ydl_opts["writethumbnail"] = True

    # Configure format-specific postprocessors
    postprocessors = []

    if audio_format == "best":
        # For best format, no audio conversion needed
        pass
    elif audio_format == "m4a":
        # For m4a, extract audio to ensure proper container
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        )
    elif audio_format == "opus":
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "opus",
            }
        )
    elif audio_format == "wav":
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        )
    else:  # mp3
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        )
        # Set quality for mp3
        if quality == "0":
            postprocessors[0]["preferredquality"] = "320"
        elif quality == "5":
            postprocessors[0]["preferredquality"] = "192"
        else:
            postprocessors[0]["preferredquality"] = "128"

    # Add thumbnail conversion and embedding
    postprocessors.append(
        {
            "key": "FFmpegThumbnailsConvertor",
            "format": "jpg",
        }
    )
    postprocessors.append(
        {
            "key": "EmbedThumbnail",
        }
    )

    ydl_opts["postprocessors"] = postprocessors

    try:
        logger.info("📥 Starting yt-dlp download:")
        logger.info(f"   └─ URL: {url}")
        logger.info(f"   └─ Format: {audio_format}")
        logger.info(f"   └─ Quality: {quality}")
        logger.info(
            f"   └─ Player client: {ydl_opts.get('extractor_args', {}).get('youtube', {}).get('player_client', 'default')}"
        )
        logger.info(f"   └─ Browser cookies: {bool(cookies_from_browser)}")
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


async def download_audio_with_tiers(
    url: str,
    quality: str,
    format_name: str,
    output_dir: str,
    cookies: str,
    strategy: TierStrategy,
) -> dict[str, Any]:
    """Download audio with tier-based fallback strategy.

    Implements progressive escalation through three tiers:
    - Tier 1: Simple requests with spoofing (3 attempts)
    - Tier 2: Browser cookie authentication (if enabled)
    - Tier 3: Advanced mobile client strategies (if enabled)

    Args:
        url: YouTube video URL
        quality: Audio quality level
        format_name: Output format
        output_dir: Output directory
        cookies: Optional cookie string
        strategy: TierStrategy instance for fallback logic

    Returns:
        dict with keys:
            - success: bool
            - tier_used: DownloadTier or None
            - attempts: int
            - browser_used: str or None (for Tier 2)
            - file_path: str (if success)
            - error: str (if failure)
    """
    total_attempts = 0

    # Tier 1: Progressive attempts with basic spoofing
    logger.info("")
    logger.info(f"{'=' * 70}")
    logger.info("🥇 TIER 1: ANDROID CLIENT (Default Strategy)")
    logger.info(f"{'=' * 70}")
    logger.info(f"Starting Tier 1 download: {url}")
    logger.info(f"   └─ Max attempts: {strategy.get_max_attempts(DownloadTier.TIER_1_SIMPLE)}")
    logger.info("   └─ Strategy: Android client, no authentication")
    logger.info("   └─ Expected: 95% success, ~1-2 seconds")
    max_tier1_attempts = strategy.get_max_attempts(DownloadTier.TIER_1_SIMPLE)

    for attempt in range(1, max_tier1_attempts + 1):
        total_attempts += 1

        try:
            logger.info("")
            logger.info(f"🔄 Tier 1 attempt {attempt}/{max_tier1_attempts}")
            file_path = await download_audio(
                url=url,
                audio_format=format_name,
                quality=quality,
                output_dir=output_dir,
            )

            logger.info("")
            logger.info(f"✅ TIER 1 SUCCEEDED on attempt {attempt}/{max_tier1_attempts}")
            logger.info(f"   └─ File: {file_path}")
            logger.info(f"   └─ Total attempts: {total_attempts}")
            return {
                "success": True,
                "tier_used": DownloadTier.TIER_1_SIMPLE,
                "attempts": total_attempts,
                "browser_used": None,
                "file_path": file_path,
            }

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"❌ Tier 1 attempt {attempt} failed:")
            logger.warning(f"   └─ Error: {error_msg[:200]}")  # Truncate long errors

            # Check if we should escalate immediately on error message
            if strategy.should_escalate_on_error(error_msg):
                logger.warning("⚡ Escalation condition detected!")
                logger.warning("   └─ Breaking out of Tier 1 attempts")
                logger.warning(f"   └─ Reason: {error_msg[:100]}")
                break  # Break immediately to escalate to next tier

    # Tier 2: Browser cookie authentication
    if strategy.tier2_enabled:
        logger.info("")
        logger.info(f"{'=' * 70}")
        logger.info("🥈 TIER 2: BROWSER COOKIES (Fallback Strategy)")
        logger.info(f"{'=' * 70}")
        logger.warning("Escalating to Tier 2: Browser cookie authentication")

        extractor = CookieExtractor()
        installed_browsers = extractor.find_installed_browsers()

        if not installed_browsers:
            logger.warning("No browsers found for Tier 2, skipping to Tier 3")
        else:
            for browser_type in installed_browsers:
                browser_name = extractor.browser_to_string(browser_type)
                total_attempts += 1

                try:
                    logger.info("")
                    logger.info(f"🔄 Tier 2: Trying browser {browser_name}")
                    logger.info(f"   └─ Extracting cookies from {browser_name}")
                    # For Tier 2, use yt-dlp's --cookies-from-browser
                    file_path = await download_audio(
                        url=url,
                        cookies_from_browser=browser_name.lower(),  # Extract from browser
                        audio_format=format_name,
                        quality=quality,
                        output_dir=output_dir,
                    )

                    logger.info("")
                    logger.info(f"✅ TIER 2 SUCCEEDED with browser: {browser_name}")
                    logger.info(f"   └─ File: {file_path}")
                    logger.info(f"   └─ Total attempts: {total_attempts}")
                    return {
                        "success": True,
                        "tier_used": DownloadTier.TIER_2_COOKIES,
                        "attempts": total_attempts,
                        "browser_used": browser_name,
                        "file_path": file_path,
                    }

                except Exception as e:
                    logger.warning(f"❌ Tier 2 failed with browser {browser_name}:")
                    logger.warning(f"   └─ Error: {str(e)[:200]}")
                    continue

            logger.warning("All Tier 2 browsers exhausted")
    else:
        logger.info("Tier 2 disabled, escalating to Tier 3")

    # Tier 3: Advanced mobile client strategies
    if strategy.tier3_enabled:
        if not strategy.tier2_enabled:
            logger.warning("Tier 2 disabled, escalating to Tier 3")
        else:
            logger.info("")
            logger.info(f"{'=' * 70}")
            logger.info("🥉 TIER 3: ANDROID + MWEB (Last Resort)")
            logger.info(f"{'=' * 70}")
            logger.warning("Escalating to Tier 3: Advanced strategies")
        try:
            logger.info("Tier 3 attempt with advanced strategies")
            logger.info("   └─ Player clients: ['android', 'mweb']")
            logger.info("   └─ Multiple client fallback")
            # For Tier 3, use mobile clients that sometimes bypass restrictions
            file_path = await download_audio(
                url=url,
                audio_format=format_name,
                quality=quality,
                output_dir=output_dir,
                player_client=["android", "mweb"],  # Android + mobile web fallback
            )

            logger.info("")
            logger.info("✅ TIER 3 SUCCEEDED (Last resort)")
            logger.info(f"   └─ File: {file_path}")
            logger.info(f"   └─ Total attempts: {total_attempts}")
            return {
                "success": True,
                "tier_used": DownloadTier.TIER_3_ADVANCED,
                "attempts": total_attempts,
                "browser_used": None,
                "file_path": file_path,
            }

        except Exception as e:
            logger.error("")
            logger.error("❌ TIER 3 FAILED (All tiers exhausted)")
            logger.error(f"   └─ Error: {str(e)[:200]}")

    # All tiers exhausted
    logger.error("")
    logger.error(f"{'=' * 70}")
    logger.error("💥 ALL TIERS FAILED - DOWNLOAD UNSUCCESSFUL")
    logger.error(f"{'=' * 70}")
    logger.error("❌ Download failed after all tier strategies exhausted")
    logger.error(f"   └─ Total attempts: {total_attempts}")
    logger.error(f"   └─ URL: {url}")
    return {
        "success": False,
        "tier_used": None,
        "attempts": total_attempts,
        "browser_used": None,
        "error": "All download tiers exhausted",
    }
