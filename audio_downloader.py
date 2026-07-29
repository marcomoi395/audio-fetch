#!/usr/bin/env python3
"""
Audio Downloader from YouTube using yt-dlp
Công cụ tải audio từ YouTube với chất lượng cao
"""

import sys
import os
from pathlib import Path
import yt_dlp


class AudioDownloader:
    """Class để tải audio từ YouTube"""
    
    SUPPORTED_FORMATS = {
        'mp3': 'MP3 (phổ biến nhất, tương thích tốt)',
        'm4a': 'M4A/AAC (chất lượng gốc từ YouTube)',
        'opus': 'OPUS (chất lượng cao, file nhỏ)',
        'wav': 'WAV (không nén, chất lượng tốt nhất nhưng file lớn)',
        'best': 'Định dạng tốt nhất có sẵn (không convert)'
    }
    
    QUALITY_LEVELS = {
        '0': 'Cao nhất (320kbps cho MP3)',
        '5': 'Trung bình (192kbps cho MP3)',
        '9': 'Thấp (128kbps cho MP3)'
    }
    
    def __init__(self, output_dir='downloads'):
        """
        Khởi tạo AudioDownloader
        
        Args:
            output_dir: Thư mục lưu file tải về
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def download(self, url, audio_format='mp3', quality='0', 
                 embed_thumbnail=True, embed_metadata=True,
                 playlist=False):
        """
        Tải audio từ YouTube URL
        
        Args:
            url: YouTube URL
            audio_format: Định dạng audio (mp3, m4a, opus, wav, best)
            quality: Chất lượng audio (0=cao nhất, 5=trung bình, 9=thấp)
            embed_thumbnail: Nhúng ảnh thumbnail vào file
            embed_metadata: Nhúng metadata (tiêu đề, tác giả, v.v.)
            playlist: Tải toàn bộ playlist hay chỉ video đầu tiên
        
        Returns:
            bool: True nếu tải thành công, False nếu thất bại
        """
        
        # Tạo output template
        if playlist:
            output_template = str(self.output_dir / '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s')
        else:
            output_template = str(self.output_dir / '%(title)s.%(ext)s')
        
        # Cấu hình yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'noplaylist': not playlist,
            'quiet': False,
            'no_warnings': False,
        }
        
        # Cấu hình post-processor dựa trên định dạng
        if audio_format != 'best':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': quality,
            }]
        
        # Thêm metadata embedding
        if embed_metadata:
            if 'postprocessors' not in ydl_opts:
                ydl_opts['postprocessors'] = []
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            })
        
        # Thêm thumbnail embedding
        if embed_thumbnail:
            if 'postprocessors' not in ydl_opts:
                ydl_opts['postprocessors'] = []
            ydl_opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
            })
            # Cần tải thumbnail trước
            ydl_opts['writethumbnail'] = True
        
        try:
            print(f"\n{'='*60}")
            print(f"Đang tải từ: {url}")
            print(f"Định dạng: {audio_format.upper()}")
            print(f"Chất lượng: {self.QUALITY_LEVELS.get(quality, 'Tùy chỉnh')}")
            print(f"Thư mục lưu: {self.output_dir.absolute()}")
            print(f"{'='*60}\n")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Lấy thông tin video trước
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    # Đây là playlist
                    video_count = len(info['entries'])
                    print(f"📋 Phát hiện playlist với {video_count} video")
                    
                    if not playlist:
                        print(f"⚠️  Chỉ tải video đầu tiên (dùng --playlist để tải toàn bộ)")
                    else:
                        print(f"📥 Đang tải {video_count} video...")
                else:
                    # Video đơn lẻ
                    print(f"🎵 {info.get('title', 'Unknown')}")
                    print(f"👤 {info.get('uploader', 'Unknown')}")
                    print(f"⏱️  {self._format_duration(info.get('duration', 0))}")
                
                # Bắt đầu tải
                print(f"\n⬇️  Đang tải...\n")
                ydl.download([url])
                
                print(f"\n{'='*60}")
                print(f"✅ Tải thành công!")
                print(f"📁 File được lưu tại: {self.output_dir.absolute()}")
                print(f"{'='*60}\n")
                
                return True
                
        except yt_dlp.utils.DownloadError as e:
            print(f"\n❌ Lỗi khi tải: {str(e)}\n")
            return False
        except Exception as e:
            print(f"\n❌ Lỗi không xác định: {str(e)}\n")
            return False
    
    @staticmethod
    def _format_duration(seconds):
        """Format duration từ giây sang MM:SS hoặc HH:MM:SS"""
        if not seconds:
            return "Unknown"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


def print_banner():
    """In banner chào mừng"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║            🎵 YOUTUBE AUDIO DOWNLOADER 🎵                ║
    ║                                                           ║
    ║              Tải audio chất lượng cao từ YouTube         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """In hướng dẫn sử dụng"""
    help_text = """
    📖 HƯỚNG DẪN SỬ DỤNG:
    
    Cách 1: Chạy interactive mode
        python audio_downloader.py
    
    Cách 2: Truyền URL trực tiếp
        python audio_downloader.py <youtube_url>
    
    Cách 3: Với options
        python audio_downloader.py <youtube_url> --format mp3 --quality 0
    
    📋 OPTIONS:
        --format <format>      Định dạng audio: mp3, m4a, opus, wav, best (mặc định: mp3)
        --quality <level>      Chất lượng: 0 (cao nhất), 5 (trung bình), 9 (thấp) (mặc định: 0)
        --no-thumbnail         Không nhúng ảnh thumbnail
        --no-metadata          Không nhúng metadata
        --playlist             Tải toàn bộ playlist (mặc định: chỉ tải video đầu tiên)
        --output <dir>         Thư mục lưu file (mặc định: downloads)
        --help                 Hiển thị hướng dẫn này
    
    📝 VÍ DỤ:
        python audio_downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
        python audio_downloader.py <url> --format m4a --quality 0
        python audio_downloader.py <url> --playlist --format opus
        python audio_downloader.py <url> --output my_music --no-thumbnail
    """
    print(help_text)


def interactive_mode():
    """Chế độ interactive để nhập thông tin"""
    downloader = AudioDownloader()
    
    print_banner()
    
    while True:
        print("\n" + "="*60)
        url = input("📎 Nhập YouTube URL (hoặc 'q' để thoát): ").strip()
        
        if url.lower() in ['q', 'quit', 'exit']:
            print("\n👋 Tạm biệt!\n")
            break
        
        if not url:
            print("⚠️  URL không được để trống!")
            continue
        
        # Chọn định dạng
        print("\n🎵 Chọn định dạng audio:")
        for idx, (fmt, desc) in enumerate(AudioDownloader.SUPPORTED_FORMATS.items(), 1):
            print(f"  {idx}. {fmt.upper()}: {desc}")
        
        format_choice = input("\nNhập số (mặc định: 1 - MP3): ").strip()
        if not format_choice:
            format_choice = '1'
        
        try:
            format_idx = int(format_choice) - 1
            audio_format = list(AudioDownloader.SUPPORTED_FORMATS.keys())[format_idx]
        except (ValueError, IndexError):
            print("⚠️  Lựa chọn không hợp lệ, sử dụng MP3")
            audio_format = 'mp3'
        
        # Chọn chất lượng
        if audio_format != 'best':
            print("\n⚡ Chọn chất lượng:")
            for quality, desc in AudioDownloader.QUALITY_LEVELS.items():
                print(f"  {quality}. {desc}")
            
            quality = input("\nNhập số (mặc định: 0 - Cao nhất): ").strip()
            if quality not in AudioDownloader.QUALITY_LEVELS:
                quality = '0'
        else:
            quality = '0'
        
        # Tùy chọn bổ sung
        playlist = input("\n📋 Tải toàn bộ playlist? (y/N): ").strip().lower() == 'y'
        
        # Tải
        success = downloader.download(
            url=url,
            audio_format=audio_format,
            quality=quality,
            playlist=playlist
        )
        
        if success:
            another = input("\n🔄 Tải video khác? (Y/n): ").strip().lower()
            if another == 'n':
                print("\n👋 Tạm biệt!\n")
                break
        else:
            retry = input("\n🔄 Thử lại? (Y/n): ").strip().lower()
            if retry == 'n':
                print("\n👋 Tạm biệt!\n")
                break


def main():
    """Main function"""
    args = sys.argv[1:]
    
    # Kiểm tra --help
    if '--help' in args or '-h' in args:
        print_banner()
        print_help()
        return
    
    # Parse arguments
    url = None
    audio_format = 'mp3'
    quality = '0'
    embed_thumbnail = True
    embed_metadata = True
    playlist = False
    output_dir = 'downloads'
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg.startswith('http'):
            url = arg
        elif arg == '--format' and i + 1 < len(args):
            audio_format = args[i + 1].lower()
            i += 1
        elif arg == '--quality' and i + 1 < len(args):
            quality = args[i + 1]
            i += 1
        elif arg == '--no-thumbnail':
            embed_thumbnail = False
        elif arg == '--no-metadata':
            embed_metadata = False
        elif arg == '--playlist':
            playlist = True
        elif arg == '--output' and i + 1 < len(args):
            output_dir = args[i + 1]
            i += 1
        
        i += 1
    
    # Validate format
    if audio_format not in AudioDownloader.SUPPORTED_FORMATS:
        print(f"⚠️  Định dạng '{audio_format}' không hợp lệ!")
        print(f"📋 Các định dạng hỗ trợ: {', '.join(AudioDownloader.SUPPORTED_FORMATS.keys())}")
        return
    
    # Nếu không có URL, chạy interactive mode
    if not url:
        interactive_mode()
    else:
        # Command-line mode
        print_banner()
        downloader = AudioDownloader(output_dir=output_dir)
        downloader.download(
            url=url,
            audio_format=audio_format,
            quality=quality,
            embed_thumbnail=embed_thumbnail,
            embed_metadata=embed_metadata,
            playlist=playlist
        )


if __name__ == '__main__':
    main()
