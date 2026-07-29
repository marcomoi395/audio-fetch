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
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        # Parse common yt-dlp errors for user-friendly messages
        if "Video unavailable" in error_msg:
            raise Exception("Video không khả dụng. Có thể video đã bị xóa hoặc chuyển sang riêng tư.")
        elif "This video is private" in error_msg:
            raise Exception("Video này ở chế độ riêng tư và không thể tải xuống.")
        elif "age-restricted" in error_msg.lower():
            raise Exception("Video giới hạn độ tuổi. Không thể tải xuống video này.")
        elif "This live event will begin" in error_msg:
            raise Exception("Đây là livestream chưa bắt đầu. Vui lòng thử lại sau khi stream đang phát.")
        elif "Premieres in" in error_msg:
            raise Exception("Video này sẽ được công chiếu sau. Vui lòng thử lại khi video đã phát.")
        else:
            raise Exception(f"Lỗi trích xuất thông tin: {error_msg}")
    except Exception as e:
        # Generic error fallback
        raise Exception(f"Lỗi không xác định: {str(e)}")


async def download_audio(
    url: str,
    audio_format: str = 'mp3',
    quality: str = '0',
    output_dir: str = None
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
    output_template = str(output_path / '%(title)s.%(ext)s')
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'noplaylist': True,  # Web version doesn't support playlists
        'quiet': True,
        'no_warnings': True,
    }
    
    # Configure post-processor based on format
    if audio_format != 'best':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': quality,
        }]
    
    # Add metadata embedding (always enabled for web)
    if 'postprocessors' not in ydl_opts:
        ydl_opts['postprocessors'] = []
    ydl_opts['postprocessors'].append({
        'key': 'FFmpegMetadata',
        'add_metadata': True,
    })
    
    # Add thumbnail embedding (always enabled for web)
    ydl_opts['postprocessors'].append({
        'key': 'EmbedThumbnail',
    })
    ydl_opts['writethumbnail'] = True
    
    try:
        # Run yt-dlp in thread pool since it's blocking I/O
        loop = asyncio.get_event_loop()
        
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info to get final filename
                info = ydl.extract_info(url, download=False)
                
                # Download the audio
                ydl.download([url])
                
                # Determine the actual output file path
                title = info.get('title', 'audio')
                # yt-dlp changes the extension after post-processing
                actual_format = audio_format if audio_format != 'best' else info.get('ext', 'webm')
                output_file = output_path / f"{title}.{actual_format}"
                
                return str(output_file)
        
        file_path = await loop.run_in_executor(None, download)
        return file_path
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        # Parse common yt-dlp errors for user-friendly messages
        if "Video unavailable" in error_msg:
            raise Exception("Video không khả dụng. Có thể video đã bị xóa hoặc chuyển sang riêng tư.")
        elif "This video is private" in error_msg:
            raise Exception("Video này ở chế độ riêng tư và không thể tải xuống.")
        elif "Postprocessing" in error_msg:
            raise Exception("Lỗi chuyển đổi định dạng audio. Vui lòng thử định dạng khác.")
        elif "FFmpeg" in error_msg or "ffmpeg" in error_msg:
            raise Exception("Lỗi FFmpeg khi xử lý audio. Vui lòng kiểm tra FFmpeg đã được cài đặt.")
        elif "HTTP Error 429" in error_msg:
            raise Exception("YouTube đang giới hạn tải xuống. Vui lòng thử lại sau vài phút.")
        elif "network" in error_msg.lower() or "timed out" in error_msg.lower():
            raise Exception("Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet và thử lại.")
        else:
            raise Exception(f"Lỗi tải xuống: {error_msg}")
    except Exception as e:
        # Generic error fallback
        if "Failed to download audio" not in str(e):
            raise Exception(f"Lỗi không xác định: {str(e)}")
        raise
