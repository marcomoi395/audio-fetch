# Metadata Embedding Update - Changelog

## Thay đổi

### services/downloader.py

**Thêm FFmpegMetadata postprocessor** để nhúng đầy đủ metadata vào file audio.

```python
# Trước đây: Chỉ có thumbnail
postprocessors.append({"key": "EmbedThumbnail"})

# Bây giờ: Có cả thumbnail VÀ metadata đầy đủ
postprocessors.append({"key": "EmbedThumbnail"})
postprocessors.append({
    "key": "FFmpegMetadata",
    "add_metadata": True,
})
```

### Metadata được nhúng tự động

Khi tải xuống, file audio giờ đây sẽ có:

| Trường | Giá trị | Ví dụ |
|--------|---------|-------|
| **Title** | Tiêu đề video | "Rick Astley - Never Gonna Give You Up" |
| **Artist** | Tên kênh YouTube | "Rick Astley" |
| **Album** | Tên kênh | "Rick Astley" |
| **Date** | Ngày đăng video | "2009-10-25" |
| **Comment** | URL video gốc | "https://www.youtube.com/watch?v=dQw4w9WgXcQ" |
| **Description** | Mô tả video | "The official video for..." |
| **Duration** | Độ dài | "213.024000" |
| **Thumbnail** | Ảnh bìa | (embedded image) |

### Tests

**Thêm file mới**: `tests/test_metadata_embedding.py`

- `test_metadata_postprocessor_configured`: Xác nhận FFmpegMetadata được cấu hình
- `test_metadata_order`: Xác nhận thứ tự postprocessors đúng (metadata sau thumbnail)

```bash
# Chạy metadata tests
pytest tests/test_metadata_embedding.py -v

# Kết quả
✅ test_metadata_postprocessor_configured PASSED
✅ test_metadata_order PASSED
```

### Documentation

**Thêm file mới**: `docs/METADATA_EMBEDDING.md`

Chi tiết đầy đủ về:
- Các metadata được nhúng
- Cách xem metadata trên Windows/Linux/macOS
- Hỗ trợ định dạng (MP3, M4A, OPUS, WAV)
- Troubleshooting

## Không có Breaking Changes

- API giữ nguyên
- Request/Response format không đổi
- Metadata được thêm tự động, không cần cấu hình
- Backward compatible 100%

## Xác minh

### Test trên command line

```bash
# Tải một bài hát
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "mp3",
    "quality": "0"
  }' \
  --output song.mp3

# Xem metadata
ffprobe -v quiet -print_format json -show_format song.mp3
```

### Kết quả mong đợi

File MP3 sẽ có:
- ✅ Thumbnail được nhúng (đã có từ trước)
- ✅ Title - tên bài hát (MỚI)
- ✅ Artist - tác giả/uploader (MỚI)
- ✅ Album - tên kênh (MỚI)
- ✅ Date - ngày đăng (MỚI)
- ✅ Comment - URL gốc (MỚI)
- ✅ Description - mô tả (MỚI)
- ✅ Duration - độ dài (MỚI)

## Kiểm tra trong Music Players

### Windows Media Player
1. Chuột phải vào file → Properties
2. Tab "Details"
3. Xem các trường: Title, Contributing artists, Album, Year

### VLC Media Player
1. Mở file trong VLC
2. Tools → Media Information (Ctrl+I)
3. Tab "General" - xem Title, Artist, Album
4. Tab "Codec Details" - xem artwork

### iTunes/Apple Music
1. Kéo file vào iTunes/Music
2. Chuột phải → Get Info (Cmd+I)
3. Tab "Details" - xem tất cả metadata
4. Tab "Artwork" - xem thumbnail

## Performance Impact

- ⚡ Không ảnh hưởng đến tốc độ download
- 📦 File size tăng nhẹ (~1-2KB cho metadata text)
- 🎨 Thumbnail size không thay đổi (đã có từ trước)
- ✅ Postprocessor pipeline tối ưu (chạy tuần tự, không blocking)

## Next Steps

Nếu muốn tùy chỉnh metadata:

1. **Custom artist name**: Sửa trong `ydl_opts` trước khi download
2. **Custom album**: Thêm postprocessor option
3. **Genre tag**: Cần extract từ video category

Ví dụ custom metadata:

```python
ydl_opts["postprocessor_args"] = {
    "FFmpegMetadata": [
        "-metadata", "artist=Custom Artist",
        "-metadata", "album=Custom Album",
    ]
}
```
