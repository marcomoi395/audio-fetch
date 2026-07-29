# Audio Fetch - YouTube Audio Downloader

Tải audio chất lượng cao từ YouTube.

## Cách dùng

```bash
# Interactive mode
./run.sh

# Tải trực tiếp
./run.sh "https://www.youtube.com/watch?v=VIDEO_ID"

# Với options
./run.sh "URL" --format mp3 --quality 0
./run.sh "URL" --format m4a
./run.sh "URL" --playlist
```

## Options

- `--format <format>` - mp3, m4a, opus, wav, best (mặc định: mp3)
- `--quality <0-9>` - 0=cao nhất, 5=trung bình, 9=thấp
- `--playlist` - Tải toàn bộ playlist
- `--output <dir>` - Thư mục lưu file (mặc định: downloads)
- `--no-thumbnail` - Không nhúng ảnh
- `--no-metadata` - Không nhúng metadata
- `--help` - Hiển thị hướng dẫn

## Yêu cầu

- Python 3.8+
- FFmpeg (để convert audio)
- Đã cài sẵn trong venv: yt-dlp

## File được lưu ở đâu?

Mặc định: `downloads/`
