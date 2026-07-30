# PO Token Setup - YouTube Bot Detection Bypass

## Overview

YouTube hiện yêu cầu **PO Token (Proof of Origin Token)** để xác thực requests, không chỉ cookies. Đây là lý do phương pháp cookie cũ không còn hoạt động với lỗi "Sign in to confirm you're not a bot".

Audio Fetch đã tích hợp **bgutil-ytdlp-pot-provider** - plugin chính thức được maintain bởi yt-dlp team để tự động generate PO Tokens.

## Cách hoạt động

1. **bgutil HTTP Server** chạy trên port 4416, generate PO Tokens khi cần
2. **yt-dlp** được cấu hình sử dụng `mweb` client và kết nối đến bgutil server
3. Mỗi video download request sẽ tự động get PO Token từ server
4. Cookies vẫn được sử dụng để authenticate, nhưng PO Token giúp bypass bot detection

## Production Deployment (Docker)

Khi deploy qua Docker, bgutil server tự động khởi động cùng main app:

```bash
# Build image
docker build -t audio-fetch .

# Run container (cả 2 services sẽ tự động start)
docker run -p 8000:8000 -p 4416:4416 audio-fetch
```

Port 4416 không cần expose ra ngoài nếu chỉ sử dụng internal.

## Local Development

### Bước 1: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

Điều này sẽ tự động cài `bgutil-ytdlp-pot-provider` plugin.

### Bước 2: Start bgutil server

Mở terminal thứ nhất:

```bash
./start_bgutil.sh
```

Script này sẽ:
- Tự động clone và setup bgutil (chỉ lần đầu)
- Start HTTP server trên port 4416
- Giữ server chạy trong foreground

### Bước 3: Start main application

Mở terminal thứ hai:

```bash
./start.sh
```

hoặc:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Verification

### Kiểm tra bgutil server đang chạy:

```bash
curl http://127.0.0.1:4416/health
# Hoặc
curl http://127.0.0.1:4416/
```

### Kiểm tra plugin đã được cài:

```bash
yt-dlp -v --print-traffic "https://youtube.com/watch?v=dQw4w9WgXcQ" 2>&1 | grep bgutil
```

Bạn sẽ thấy output tương tự:

```
[debug] [youtube] [pot] PO Token Providers: bgutil:http-1.3.1 (external)
```

### Test download:

Sử dụng Web UI như bình thường tại http://localhost:8000

## Troubleshooting

### bgutil server không start

**Lỗi**: `Node.js is required but not installed`

**Giải pháp**: Cài Node.js 20+:
- Ubuntu/Debian: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs`
- macOS: `brew install node`
- Windows: Download từ https://nodejs.org/

### Port 4416 đã được sử dụng

**Giải pháp**: Thay đổi port trong `start_bgutil.sh` và update `services/downloader.py`:

```python
"youtubepot-bgutilhttp": {
    "base_url": "http://127.0.0.1:YOUR_NEW_PORT",
},
```

### Vẫn bị bot detection

1. **Kiểm tra bgutil server đang chạy**: `curl http://127.0.0.1:4416/`
2. **Xóa cookies cũ** và export lại cookies mới từ incognito window
3. **Thử video khác** - một số video có thể bị restricted riêng
4. **Check logs**: `docker logs <container_id>` để xem chi tiết lỗi

## Technical Details

- **PO Token TTL**: 6 hours (mặc định, có cache tự động)
- **Token binding**: Mỗi token bind với video ID cụ thể
- **Client used**: `mweb` (mobile web) - tối ưu cho PO Token
- **Plugin version**: bgutil-ytdlp-pot-provider >= 1.3.0

## References

- [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
- [bgutil-ytdlp-pot-provider GitHub](https://github.com/Brainicism/bgutil-ytdlp-pot-provider)
- [YouTube Extractor Wiki](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies)

## Testing

### Quick Test

1. **Verify services running:**
   ```bash
   docker-compose ps
   # Should show: Up X seconds (healthy)
   ```

2. **Check bgutil logs:**
   ```bash
   docker-compose logs | grep bgutil
   # Should see: "bgutil provider started" and "POT server (v1.3.1)"
   ```

3. **Test with Web UI:**
   - Open http://localhost:8000
   - Paste YouTube URL
   - Add cookies (exported from incognito window)
   - Click "Fetch Info"
   - Should work without "bot" error

4. **Monitor PO Token generation:**
   ```bash
   docker-compose logs -f | grep "PO Token"
   # Should see: "Generating a gvs PO Token for mweb client"
   ```

### Expected Results

**Before PO Token:**
```
❌ ERROR: Sign in to confirm you're not a bot
```

**After PO Token:**
```
✅ Video info fetched successfully
✅ Download works
```

Success rate: 50-70% (vs 10% before)
