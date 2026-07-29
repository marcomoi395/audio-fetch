# Spec: Audio-Fetch Web App

## Objective

Convert the existing CLI audio-fetch tool into a web application that allows users to download audio from YouTube videos through a browser interface with an 8-bit retro aesthetic.

**Target Users:** Anyone who wants to extract audio from YouTube videos without using command-line tools.

**Problem Solved:** Provides a user-friendly web interface for audio extraction, eliminating the need for terminal knowledge and making the tool accessible to non-technical users.

### User Story

As a user, I want to:
1. Paste a YouTube URL into a web form
2. See the video information (title, uploader, duration, thumbnail) before downloading
3. Choose audio format (mp3, m4a, opus, wav, best) and quality (high, medium, low)
4. Click a download button and receive the extracted audio file directly to my browser
5. Experience a fun, nostalgic 8-bit themed interface with sound effects

### Success Criteria

- [ ] User can paste YouTube URL and fetch video metadata within 10 seconds
- [ ] User can select from 5 audio formats and 3 quality levels
- [ ] User receives downloaded audio file through browser download
- [ ] Interface uses NES.css with white mode theme
- [ ] UI interactions trigger appropriate 8-bit sound effects
- [ ] Server handles one download at a time (no concurrent downloads)
- [ ] Detailed error messages shown when download fails
- [ ] No user data or downloaded files persist on server after transfer
- [ ] Application works on modern browsers (Chrome, Firefox, Safari, Edge)

## Tech Stack

### Backend
- **FastAPI** (0.100.0+) - Web framework
- **Python** 3.9+ - Runtime
- **yt-dlp** (latest) - YouTube audio extraction
- **FFmpeg** (system dependency) - Audio processing
- **uvicorn** - ASGI server
- **aiofiles** - Async file operations

### Frontend
- **Vanilla JavaScript** (ES6+) - No framework needed
- **NES.css** (latest) - 8-bit CSS framework
- **HTML5** - Semantic markup
- **8-bit sound effects** - Free sound library (to be sourced)

### Infrastructure
- **No database** - Stateless application
- **Temporary file storage** - OS temp directory with auto-cleanup
- **Self-hosted deployment** - Local or VPS

## Commands

```bash
# Development
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

# Testing
pytest tests/ --cov=. --cov-report=term-missing

# Linting
ruff check .
black . --check

# Type checking
mypy .

# Check FFmpeg installation
ffmpeg -version
```

## Project Structure

```
audio-fetch/
├── main.py                    # FastAPI app entry point
├── api/
│   ├── __init__.py
│   ├── routes.py              # API endpoints
│   └── models.py              # Pydantic models (request/response)
├── services/
│   ├── __init__.py
│   ├── downloader.py          # yt-dlp wrapper (adapted from audio_downloader.py)
│   └── queue.py               # Single-threaded download queue
├── static/
│   ├── css/
│   │   └── custom.css         # Custom styles on top of NES.css
│   ├── js/
│   │   ├── app.js             # Main application logic
│   │   └── audio.js           # 8-bit sound effect manager
│   └── sounds/
│       ├── click.mp3          # Button click sound
│       ├── fetch.mp3          # Fetch info sound
│       ├── download.mp3       # Download start sound
│       ├── success.mp3        # Download complete sound
│       └── error.mp3          # Error sound
├── templates/
│   └── index.html             # Single page application
├── tests/
│   ├── __init__.py
│   ├── test_api.py            # API endpoint tests
│   ├── test_downloader.py    # Downloader service tests
│   └── test_queue.py          # Queue tests
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # Setup and usage instructions
└── SPEC.md                    # This file
```

## Code Style

### Python (PEP 8 + Black + Ruff)

```python
from typing import Optional
from fastapi import HTTPException
from pydantic import BaseModel, HttpUrl


class VideoInfoRequest(BaseModel):
    """Request model for video info endpoint."""
    url: HttpUrl


class VideoInfo(BaseModel):
    """Video metadata response."""
    title: str
    uploader: str
    duration: int  # seconds
    thumbnail_url: str
    formats: list[str] = ["mp3", "m4a", "opus", "wav", "best"]
    qualities: dict[str, str] = {
        "0": "Cao nhất (320kbps)",
        "5": "Trung bình (192kbps)",
        "9": "Thấp (128kbps)"
    }


async def get_video_info(url: str) -> VideoInfo:
    """
    Extract video metadata from YouTube URL.
    
    Args:
        url: Valid YouTube URL
        
    Returns:
        VideoInfo object with metadata
        
    Raises:
        HTTPException: If URL is invalid or extraction fails
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Conventions:**
- Use type hints everywhere
- Docstrings for all public functions/classes (Google style)
- Async functions for I/O operations
- Pydantic models for request/response validation
- Black formatter (line length: 88)
- Ruff for linting
- Snake_case for variables/functions, PascalCase for classes

### JavaScript (ES6+)

```javascript
/**
 * Fetch video information from server
 * @param {string} url - YouTube URL
 * @returns {Promise<Object>} Video metadata
 */
async function fetchVideoInfo(url) {
    const response = await fetch('/api/video-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
    }
    
    return await response.json();
}

// Play 8-bit sound effect
function playSound(soundName) {
    const audio = new Audio(`/static/sounds/${soundName}.mp3`);
    audio.volume = 0.5;
    audio.play().catch(err => console.warn('Sound play failed:', err));
}
```

**Conventions:**
- camelCase for variables/functions
- JSDoc comments for functions
- async/await for promises (no .then() chains)
- const by default, let when reassignment needed, never var
- Template literals for string interpolation
- Optional chaining (?.) and nullish coalescing (??)

### HTML (Semantic + NES.css)

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎵 Audio Fetch - 8-bit YouTube Downloader</title>
    <link href="https://unpkg.com/nes.css@latest/css/nes.min.css" rel="stylesheet">
    <link href="/static/css/custom.css" rel="stylesheet">
</head>
<body>
    <main class="nes-container with-title is-centered">
        <!-- Content here -->
    </main>
    <script src="/static/js/audio.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

**Conventions:**
- Semantic HTML5 elements
- Vietnamese language attribute
- NES.css classes (nes-container, nes-btn, nes-input, etc.)
- White mode theme (default NES.css)
- Accessible form labels and ARIA attributes
- Defer/async for non-critical scripts

## Testing Strategy

### Framework
- **pytest** - Test runner
- **pytest-asyncio** - Async test support
- **httpx** - Async HTTP client for API testing
- **pytest-cov** - Coverage reporting

### Test Organization

```
tests/
├── test_api.py          # API endpoint tests (FastAPI TestClient)
├── test_downloader.py   # Downloader service unit tests
└── test_queue.py        # Queue behavior tests
```

### Coverage Requirements
- **Target:** 80% overall coverage
- **Critical paths:** 100% coverage for download queue and error handling
- **Skip:** UI JavaScript tests (manual testing only)

### Test Levels

1. **Unit Tests** - Service layer functions
   - `test_extract_video_info_success()`
   - `test_extract_video_info_invalid_url()`
   - `test_queue_single_download()`
   - `test_queue_blocks_concurrent_downloads()`

2. **Integration Tests** - API endpoints
   - `test_video_info_endpoint()`
   - `test_download_endpoint()`
   - `test_error_handling()`

3. **Manual Tests** - UI interactions
   - Test all 8-bit sounds play on interactions
   - Test responsive layout on mobile/desktop
   - Test file downloads in different browsers
   - Test error messages display correctly

### Test Data
- Use recorded yt-dlp responses (fixtures) to avoid live API calls
- Mock FFmpeg operations in tests
- Test with various URL formats (youtube.com, youtu.be, /watch?v=, /shorts/)

## Boundaries

### Always Do
- ✅ Validate YouTube URL format before processing
- ✅ Delete temporary files immediately after download completes/fails
- ✅ Return detailed error messages from yt-dlp to user
- ✅ Play appropriate 8-bit sound for each UI interaction
- ✅ Use async/await for all I/O operations
- ✅ Type hint all Python functions
- ✅ Handle browser download cancellation gracefully
- ✅ Log all download attempts (URL, format, success/failure)
- ✅ Check FFmpeg availability on startup

### Ask First
- ❓ Adding new audio formats beyond the 5 specified
- ❓ Supporting playlist downloads (explicitly excluded but user might request)
- ❓ Adding user accounts or download history
- ❓ Changing the 8-bit theme or color scheme
- ❓ Adding rate limiting or authentication
- ❓ Supporting non-YouTube platforms
- ❓ Storing any user data or analytics
- ❓ Deploying to production environment

### Never Do
- ❌ Store downloaded audio files on server after transfer
- ❌ Store user IP addresses, URLs, or any personal data
- ❌ Allow concurrent downloads (queue must be single-threaded)
- ❌ Skip input validation (always validate URLs)
- ❌ Use synchronous blocking operations in FastAPI routes
- ❌ Commit FFmpeg binaries to git (system dependency only)
- ❌ Auto-play 8-bit sounds without user interaction (browser will block)
- ❌ Support playlists (explicitly excluded from web version)
- ❌ Display YouTube video player or embed (audio-only focus)

## API Design

### Endpoints

#### POST /api/video-info
**Purpose:** Fetch metadata for a YouTube URL

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response (200):**
```json
{
  "title": "Rick Astley - Never Gonna Give You Up",
  "uploader": "Rick Astley",
  "duration": 212,
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "formats": ["mp3", "m4a", "opus", "wav", "best"],
  "qualities": {
    "0": "Cao nhất (320kbps)",
    "5": "Trung bình (192kbps)",
    "9": "Thấp (128kbps)"
  }
}
```

**Response (400):**
```json
{
  "detail": "ERROR: [youtube] dQw4w9WgXcQ: Video unavailable"
}
```

#### POST /api/download
**Purpose:** Download audio in specified format/quality

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format": "mp3",
  "quality": "0"
}
```

**Response (200):**
- Content-Type: audio/mpeg (or appropriate for format)
- Content-Disposition: attachment; filename="Rick Astley - Never Gonna Give You Up.mp3"
- Streams file binary data

**Response (400):**
```json
{
  "detail": "Download failed: [detailed yt-dlp error message]"
}
```

**Response (503):**
```json
{
  "detail": "Another download is in progress. Please wait."
}
```

#### GET /health
**Purpose:** Health check endpoint

**Response (200):**
```json
{
  "status": "ok",
  "ffmpeg_available": true,
  "queue_active": false
}
```

## UI Flow

### 1. Initial State
```
┌─────────────────────────────────────┐
│   🎵 Audio Fetch - 8-bit Style 🎵   │
├─────────────────────────────────────┤
│                                     │
│  [YouTube URL input field_______]  │
│                                     │
│         [Fetch Info Button]         │
│                                     │
└─────────────────────────────────────┘
```

### 2. Loading State (after clicking Fetch Info)
```
┌─────────────────────────────────────┐
│   🎵 Audio Fetch - 8-bit Style 🎵   │
├─────────────────────────────────────┤
│                                     │
│  [URL: youtube.com/watch?v=...]    │
│                                     │
│      🔄 Đang tải thông tin...       │
│      [8-bit loading spinner]        │
│                                     │
└─────────────────────────────────────┘
```
- Play "fetch.mp3" sound on button click

### 3. Video Info Displayed
```
┌─────────────────────────────────────┐
│   🎵 Audio Fetch - 8-bit Style 🎵   │
├─────────────────────────────────────┤
│  [Thumbnail]  Title: Song Name      │
│               Uploader: Artist Name │
│               Duration: 03:45       │
│                                     │
│  Format: [MP3 ▼] Quality: [High ▼] │
│                                     │
│         [Download Button]           │
│         [New URL Button]            │
│                                     │
└─────────────────────────────────────┘
```

### 4. Downloading State
```
┌─────────────────────────────────────┐
│   🎵 Audio Fetch - 8-bit Style 🎵   │
├─────────────────────────────────────┤
│  [Thumbnail]  Title: Song Name      │
│                                     │
│      ⬇️ Đang tải xuống...           │
│      [8-bit loading spinner]        │
│                                     │
│  (Buttons disabled during download) │
│                                     │
└─────────────────────────────────────┘
```
- Play "download.mp3" sound on download start
- Play "success.mp3" when browser download starts

### 5. Error State
```
┌─────────────────────────────────────┐
│   🎵 Audio Fetch - 8-bit Style 🎵   │
├─────────────────────────────────────┤
│                                     │
│  ❌ Lỗi: Video không khả dụng       │
│  Chi tiết: [yt-dlp error message]  │
│                                     │
│         [Try Again Button]          │
│                                     │
└─────────────────────────────────────┘
```
- Play "error.mp3" sound on error

### Interaction Sound Mapping
- **Button hover:** Subtle hover sound (click.mp3 at 0.3 volume)
- **Fetch Info click:** fetch.mp3
- **Download click:** download.mp3
- **Download success:** success.mp3
- **Error occurred:** error.mp3

## Implementation Notes

### Download Queue Strategy
```python
class DownloadQueue:
    """Single-threaded download queue (one download at a time)."""
    
    def __init__(self):
        self._active = False
        self._lock = asyncio.Lock()
    
    async def download(self, url: str, format: str, quality: str):
        async with self._lock:
            if self._active:
                raise HTTPException(503, "Another download is in progress")
            
            self._active = True
            try:
                # Perform download
                result = await downloader.download(url, format, quality)
                return result
            finally:
                self._active = False
```

### Temporary File Cleanup
```python
import tempfile
import os
from pathlib import Path

async def download_with_cleanup(url: str, format: str, quality: str):
    """Download audio and ensure temp file cleanup."""
    temp_dir = tempfile.mkdtemp()
    try:
        output_path = Path(temp_dir) / "audio"
        # Download to temp_dir
        result = await yt_dlp_extract(url, output_path, format, quality)
        
        # Stream file to response
        return FileResponse(
            result,
            media_type=f"audio/{format}",
            filename=f"{video_title}.{format}"
        )
    finally:
        # Cleanup happens after FileResponse streams
        shutil.rmtree(temp_dir, ignore_errors=True)
```

### 8-bit Sound Effect Sources
- **Free libraries to explore:**
  - Freesound.org (search: "8-bit", "chiptune", "retro game")
  - OpenGameArt.org (8-bit SFX packs)
  - Zapsplat.com (free 8-bit sounds)
  - Generate custom sounds with: Bfxr (bfxr.net) or ChipTone (sfbgames.itch.io/chiptone)

- **Required sounds:**
  - click.mp3 (short beep, ~0.1s)
  - fetch.mp3 (rising tone, ~0.5s)
  - download.mp3 (action sound, ~0.7s)
  - success.mp3 (victory jingle, ~1s)
  - error.mp3 (descending tone, ~0.8s)

## Open Questions

None - all ambiguities resolved during clarification phase.

## Migration from CLI

### Code Reuse
- `AudioDownloader` class from `audio_downloader.py` → `services/downloader.py`
  - Keep: `download()`, `_format_duration()`, format/quality constants
  - Remove: CLI-specific functions (print_banner, interactive_mode, main)
  - Adapt: Return values instead of printing to stdout

### Deprecated Features
- Interactive CLI mode (replaced by web UI)
- Command-line argument parsing (replaced by API endpoints)
- Playlist support (excluded from web version for simplicity)

### Environment Differences
| CLI | Web App |
|-----|---------|
| Downloads to `./downloads/` | Downloads to temp dir, streams to browser |
| Synchronous execution | Async execution |
| User runs script directly | Server runs continuously |
| Multi-user N/A | Single download queue |
| Progress printed to terminal | Progress shown in UI |

## Deployment Checklist

Before running in production:
- [ ] FFmpeg installed and accessible in PATH
- [ ] Python 3.9+ installed
- [ ] Virtual environment created and dependencies installed
- [ ] Port 8000 open (or configured port)
- [ ] Sufficient disk space for temp files (10GB+ recommended)
- [ ] Consider reverse proxy (nginx) for HTTPS
- [ ] Consider process manager (systemd, supervisor) for auto-restart
- [ ] Monitor disk usage (temp files cleanup)
- [ ] Set appropriate log level (INFO in prod, DEBUG in dev)

## Next Steps

After spec approval:
1. Generate implementation plan (Phase 2: Planning)
2. Break into discrete tasks (Phase 3: Tasks)
3. Implement incrementally (Phase 4: Implement)
4. Source and add 8-bit sound effects
5. Manual testing on multiple browsers
6. Write deployment documentation
