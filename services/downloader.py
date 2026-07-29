"""YouTube audio downloader service using yt-dlp."""
import asyncio
from typing import Dict, Optional

import yt_dlp


# Format and quality constants from original AudioDownloader
SUPPORTED_FORMATS = {
    'mp3': 'MP3 (phổ biến nhất, tương thích tốt)',
    'm4a': 'M4A/AAC (chất lượng gốc từ YouTube)',
    'opus': 'OPUS (chất lượng cao, file nhỏ)',
    'wav': 'WAV (không nén, chất lượng tốt nhất nhưng file lớn)',
    'best': 'Định dạng tốt nhất có sẵn (không convert)'
}

QUALITY_LEVELS = {
    '0': 'Cao nhất (320kbps)',
    '5': 'Trung bình (192kbps)',
    '9': 'Thấp (128kbps)'
}


def format_duration(seconds: Optional[int]) -> str:
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


async def get_video_info(url: str) -> Dict[str, any]:
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
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        # Run yt-dlp in thread pool since it's blocking I/O
        loop = asyncio.get_event_loop()
        
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await loop.run_in_executor(None, extract)
        
        # Extract relevant metadata
        return {
            'title': info.get('title', 'Unknown'),
            'uploader': info.get('uploader', 'Unknown'),
            'duration': info.get('duration', 0),
            'thumbnail_url': info.get('thumbnail', ''),
            'formats': list(SUPPORTED_FORMATS.keys()),
            'qualities': QUALITY_LEVELS,
        }
        
    except Exception as e:
        raise Exception(f"Failed to extract video info: {str(e)}")
