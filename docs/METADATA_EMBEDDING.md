# Metadata Embedding trong Audio Files

## Tổng quan

Audio Fetch tự động nhúng metadata đầy đủ vào các file audio đã tải xuống, bao gồm thông tin về tác giả, tên bài hát, thumbnail và nhiều thông tin khác từ video YouTube gốc.

## Metadata được nhúng

### Thông tin cơ bản

Khi tải xuống audio từ YouTube, các metadata sau được tự động nhúng vào file:

1. **Title (Tên bài hát)**: Tiêu đề video YouTube
2. **Artist (Tác giả/Uploader)**: Tên kênh YouTube đã đăng video
3. **Album**: Tên kênh (nếu có)
4. **Date (Ngày phát hành)**: Ngày video được đăng
5. **Comment**: URL video gốc
6. **Thumbnail (Ảnh bìa)**: Hình ảnh thumbnail từ YouTube

### Metadata bổ sung

Ngoài các thông tin cơ bản, yt-dlp cũng nhúng thêm:

- **Duration**: Độ dài bài hát
- **Genre**: Thể loại (nếu YouTube cung cấp)
- **Description**: Mô tả video
- **Uploader ID**: ID kênh YouTube
- **View Count**: Số lượt xem
- **Like Count**: Số lượt thích

## Cách hoạt động

### Postprocessors Pipeline

Audio Fetch sử dụng 3 postprocessors của yt-dlp theo thứ tự:

```
1. FFmpegExtractAudio      → Chuyển đổi sang định dạng mong muốn (mp3, m4a, opus, wav)
2. FFmpegThumbnailsConvertor → Chuyển đổi thumbnail sang JPG
3. EmbedThumbnail          → Nhúng thumbnail vào file audio
4. FFmpegMetadata          → Nhúng toàn bộ metadata vào file
```

### Code Implementation

```python
# Enable thumbnail download
ydl_opts["writethumbnail"] = True

# Add postprocessors
postprocessors = []

# 1. Audio extraction/conversion
postprocessors.append({
    "key": "FFmpegExtractAudio",
    "preferredcodec": "mp3",
    "preferredquality": "320"
})

# 2. Thumbnail conversion
postprocessors.append({
    "key": "FFmpegThumbnailsConvertor",
    "format": "jpg",
})

# 3. Embed thumbnail
postprocessors.append({
    "key": "EmbedThumbnail",
})

# 4. Embed metadata
postprocessors.append({
    "key": "FFmpegMetadata",
    "add_metadata": True,
})

ydl_opts["postprocessors"] = postprocessors
```

## Hỗ trợ định dạng

Metadata embedding được hỗ trợ cho các định dạng sau:

| Định dạng | Thumbnail | Metadata | Ghi chú |
|-----------|-----------|----------|---------|
| MP3       | ✅        | ✅       | ID3v2 tags |
| M4A       | ✅        | ✅       | iTunes metadata |
| OPUS      | ✅        | ✅       | Vorbis comments |
| WAV       | ❌        | ⚠️       | Limited metadata support |
| BEST      | ✅        | ✅       | Giữ nguyên container gốc |

### Lưu ý về WAV

Format WAV có hỗ trợ metadata hạn chế. Nếu bạn cần metadata đầy đủ, nên sử dụng MP3 hoặc M4A.

## Xem metadata

### Trên Windows

1. **Windows Media Player**: Chuột phải → Properties → Details
2. **VLC Media Player**: Tools → Media Information (Ctrl+I)
3. **Mp3tag**: Mở file và xem trong cửa sổ chính

### Trên Linux

```bash
# Sử dụng ffprobe
ffprobe -v quiet -print_format json -show_format "song.mp3"

# Sử dụng exiftool
exiftool "song.mp3"

# Sử dụng mediainfo
mediainfo "song.mp3"
```

### Trên macOS

1. **Finder**: Get Info (Cmd+I)
2. **iTunes/Music**: File → Get Info
3. **VLC**: Window → Media Information (Cmd+I)

## Ví dụ output metadata

```json
{
  "format": {
    "filename": "Rick Astley - Never Gonna Give You Up.mp3",
    "format_name": "mp3",
    "duration": "213.024000",
    "tags": {
      "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
      "artist": "Rick Astley",
      "album": "Rick Astley",
      "date": "2009-10-25",
      "comment": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "description": "The official video for "Never Gonna Give You Up" by Rick Astley...",
      "genre": "Music"
    }
  }
}
```

## Troubleshooting

### Metadata không hiển thị

1. **Kiểm tra player hỗ trợ**: Một số player không đọc được tất cả metadata tags
2. **Thử player khác**: VLC thường có hỗ trợ metadata tốt nhất
3. **Kiểm tra bằng command line**: Sử dụng `ffprobe` hoặc `exiftool`

### Thumbnail không hiển thị

1. **Format limitation**: WAV không hỗ trợ embedded thumbnail
2. **Player limitation**: Một số player cũ không hiển thị thumbnail
3. **File size**: Thumbnail quá lớn có thể không được nhúng

### Metadata bị mất sau khi copy

Một số công cụ copy file có thể loại bỏ metadata. Sử dụng:
- **Windows**: Copy bình thường giữ nguyên metadata
- **Linux**: `cp -p` để preserve metadata
- **macOS**: Copy bình thường giữ nguyên metadata

## API Changes

Không có thay đổi API. Metadata embedding được tự động áp dụng cho tất cả downloads.

### Request example

```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "mp3",
    "quality": "0"
  }'
```

File trả về sẽ tự động có đầy đủ metadata và thumbnail.

## Testing

Tests cho metadata embedding:

```bash
# Chạy tất cả metadata tests
pytest tests/test_metadata_embedding.py -v

# Chạy toàn bộ test suite
pytest tests/ -v
```

## Tài liệu tham khảo

- [yt-dlp Postprocessors](https://github.com/yt-dlp/yt-dlp#post-processing-options)
- [FFmpeg Metadata](https://ffmpeg.org/ffmpeg-formats.html#Metadata)
- [ID3v2 Tags](https://id3.org/id3v2.4.0-frames)
- [Vorbis Comments](https://www.xiph.org/vorbis/doc/v-comment.html)
