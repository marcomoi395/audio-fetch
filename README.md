# Audio Fetch

A simple YouTube audio downloader with an 8-bit themed web interface.

## Prerequisites

- Python 3.9+
- FFmpeg (for audio conversion)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd audio-fetch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## YouTube Authentication (Required)

YouTube cookies are **required** for all fetch and download operations. You must provide cookies through the web interface:

1. Click "🍪 Add Cookies (Required)" in the input form
2. Paste your YouTube cookies in Netscape format
3. Cookies are stored in your browser and sent with each request

### How to Export Cookies

**Chrome:** Install "Get cookies.txt LOCALLY" extension
**Firefox:** Install "cookies.txt" extension

1. Visit youtube.com while logged in
2. Use the extension to export cookies in Netscape format
3. Copy and paste into the web interface

**Security Note:** Cookies are processed server-side in temporary files and deleted after use. Never share cookies or use untrusted cookie export tools.

For detailed instructions, see `docs/COOKIE_EXPORT_GUIDE.md`.

### PO Token Setup (Bot Detection Bypass)

YouTube now requires PO Tokens in addition to cookies. Audio Fetch automatically handles this using the bgutil plugin.

**For local development**, you need to run the bgutil server:
```bash
./start_bgutil.sh  # In one terminal
./start.sh         # In another terminal
```

**For Docker deployment**, the bgutil server starts automatically.

See `docs/PO_TOKEN_SETUP.md` for detailed setup and troubleshooting.

## Running

```bash
# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the app at `http://localhost:8000`

## Desktop Application

Audio Fetch includes a native desktop application built with PySide6 that wraps the web interface in a standalone executable.

### Features

- **Native Window**: Embedded web UI in a native desktop window
- **Single Instance**: Prevents multiple instances from running simultaneously
- **Quit Confirmation**: Warns before closing if downloads are in progress
- **Auto Cookie Extraction**: Automatically extracts browser cookies for YouTube authentication (Chrome, Firefox, Edge, Brave)
- **3-Tier Download Strategy**: Progressive fallback system for robust downloading
- **System Tray**: (Future feature) Minimize to system tray

### Installation

```bash
# Install desktop dependencies
pip install -r requirements-desktop.txt
```

### Running the Desktop App

```bash
# Run directly with Python
python desktop_main.py
```

The desktop app will:
1. Check for another running instance (shows error if found)
2. Load configuration from `~/.config/audio-fetch/config.json` (Linux) or `%APPDATA%/audio-fetch/config.json` (Windows)
3. Start the FastAPI server on configured port (default 8000)
4. Open the native window with embedded web UI
5. Log to `~/.config/audio-fetch/logs/app.log`

### Building from Source

**Linux:**
```bash
# Install dependencies
pip install -r requirements-desktop.txt

# Build binary
pyinstaller audio-fetch.spec

# Run binary
./dist/audio-fetch
```

**Windows:**

See [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md) for detailed Windows build instructions.

### Configuration

Desktop app configuration is stored in platform-specific locations:

- **Linux**: `~/.config/audio-fetch/config.json`
- **Windows**: `%APPDATA%/audio-fetch/config.json`
- **macOS**: `~/Library/Application Support/audio-fetch/config.json`

Default configuration:
```json
{
  "version": "1.0",
  "server": {
    "port": 8000,
    "auto_detect_port": true
  },
  "download": {
    "default_path": "~/Downloads/audio-fetch"
  },
  "logging": {
    "level": "WARNING",
    "file": "~/.config/audio-fetch/logs/app.log"
  }
}
```

### Troubleshooting

**"Audio Fetch is already running"**
- Another instance is already running
- Check for stale lock file at `~/.config/audio-fetch/app.lock` (Linux) or `%APPDATA%/audio-fetch/app.lock` (Windows)
- If process is dead, manually delete the lock file

**Browser cookies not found**
- Ensure your browser (Chrome/Firefox/Edge/Brave) is installed
- Cookies are extracted automatically when needed
- Fallback: Use web interface to manually add cookies

**Logs not appearing**
- Check `~/.config/audio-fetch/logs/app.log`
- Default log level is WARNING (set to INFO in config for more details)

For more details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Development

### Git Hooks

This project uses git hooks to ensure code quality:

- **pre-commit**: Auto-formats code with `ruff` before each commit
- **pre-push**: Runs tests and validates formatting before pushing

Hooks are automatically active in `.git/hooks/`. See [docs/GIT_HOOKS.md](docs/GIT_HOOKS.md) for details.

### Running Tests

Due to event loop conflicts between `pytest-asyncio` and `pytest-playwright`, tests must be run separately:

```bash
# Run all tests (recommended)
./run_all_tests.sh

# Or run separately:
# Unit tests only
pytest tests/ -m "not e2e" -v

# E2E tests only  
pytest tests/e2e/ -v

# With coverage
pytest tests/ -m "not e2e" --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Type check
mypy . --ignore-missing-imports
```

## Deployment

### Quick Deploy to Render

**Recommended: Docker Deployment (with FFmpeg support)**

1. Push code to GitHub
2. Create new Web Service on [Render](https://dashboard.render.com/)
3. Select **Docker** as environment
4. Set environment variable: `PORT=8000`
5. Deploy!

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed instructions.

### Local Production Mode

```bash
# Install production dependencies only
pip install -r requirements-prod.txt

# Run with production settings
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Production Requirements:**
- FFmpeg installed on server (for MP3/OPUS/WAV conversion)
- Configure CORS via `CORS_ORIGINS` environment variable
- Use reverse proxy (nginx/caddy) for HTTPS in self-hosted setups

**Format Support Without FFmpeg:**
- ✅ m4a (native YouTube format)
- ✅ best (no conversion needed)
- ❌ mp3, opus, wav (requires FFmpeg)

For complete deployment guide including Docker setup, see [docs/RENDER_DEPLOYMENT.md](docs/RENDER_DEPLOYMENT.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
