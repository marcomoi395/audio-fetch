# Audio Fetch 🎵

8-bit themed YouTube audio downloader with a retro NES aesthetic.

## Features

- 🎮 **8-bit Retro UI** - NES.css themed interface with pixel-perfect design
- 🎵 **Multiple Formats** - MP3, M4A, Opus, WAV support
- ⚡ **Quality Options** - Best, high, medium, low quality selection
- 🔊 **Sound Effects** - 8-bit audio feedback on all interactions
- 📱 **Responsive Design** - Works on desktop and mobile
- 🇻🇳 **Vietnamese UI** - Localized for Vietnamese users
- 🔒 **Single-threaded Queue** - One download at a time, no concurrency issues
- ⚠️ **User-friendly Errors** - Clear Vietnamese error messages

## Tech Stack

### Backend
- **FastAPI** - Modern async web framework
- **yt-dlp** - YouTube download library
- **FFmpeg** - Audio processing
- **Python 3.9+** - Runtime

### Frontend
- **Vanilla JavaScript** - No framework overhead
- **NES.css** - 8-bit pixel UI framework
- **Responsive CSS Grid** - Mobile-first layout

## Prerequisites

- Python 3.9 or higher
- FFmpeg installed and in PATH
- pip (Python package manager)

## Installation

### 1. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### 2. Clone Repository

```bash
git clone <repository-url>
cd audio-fetch
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open browser at `http://localhost:8000`

### Production Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
audio-fetch/
├── api/                    # API layer
│   ├── models.py          # Pydantic models
│   └── routes.py          # FastAPI routes
├── services/              # Business logic
│   ├── downloader.py     # yt-dlp integration
│   └── queue.py          # Download queue
├── static/                # Frontend assets
│   ├── css/
│   │   └── custom.css    # Custom styles
│   ├── js/
│   │   ├── app.js        # Main application logic
│   │   └── audio.js      # Sound effects manager
│   └── sounds/           # 8-bit sound files
├── templates/             # HTML templates
│   └── index.html        # Main page
├── tests/                 # Test suite
│   ├── test_api.py
│   ├── test_download.py
│   ├── test_downloader.py
│   ├── test_integration.py
│   ├── test_health.py
│   └── test_queue.py
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## API Endpoints

### GET /
Main application page

### GET /health
Health check endpoint
```json
{
  "status": "ok",
  "ffmpeg_available": true,
  "queue_active": false
}
```

### POST /api/video-info
Extract video information
```json
{
  "url": "https://youtube.com/watch?v=..."
}
```

Response:
```json
{
  "title": "Video Title",
  "uploader": "Channel Name",
  "duration": 180,
  "thumbnail_url": "https://...",
  "formats": ["mp3", "m4a", "opus", "wav", "best"],
  "qualities": {"0": "Best", "5": "Medium", "9": "Low"}
}
```

### POST /api/download
Download audio file
```json
{
  "url": "https://youtube.com/watch?v=...",
  "format": "mp3",
  "quality": "0"
}
```

Returns audio file as download.

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_integration.py -v
```

## Sound Effects

Place 8-bit sound files in `static/sounds/`:
- `click.mp3` - Button clicks
- `fetch.mp3` - Fetch start
- `download.mp3` - Download start
- `success.mp3` - Success
- `error.mp3` - Error

**Recommended sources:**
- Freesound.org (search "8-bit")
- OpenGameArt.org
- Bfxr.net (generate custom sounds)

See `static/sounds/README.md` for details.

## Configuration

### CORS
Edit `main.py` to specify allowed origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Change this
    ...
)
```

### Port
Change port in uvicorn command or set via environment:
```bash
PORT=8080 uvicorn main:app
```

## Troubleshooting

### FFmpeg Not Found
```
Error: FFmpeg not found
```
**Solution:** Install FFmpeg and ensure it's in PATH.

### Download Fails
```
Lỗi tải xuống: ...
```
**Solution:** Check error message. Common issues:
- Video is private/unavailable
- Age-restricted content
- Network connectivity
- Rate limiting (wait and retry)

### Queue Busy (503)
```
Another download is in progress
```
**Solution:** Wait for current download to complete. Only one download at a time.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
