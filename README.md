# Audio Fetch Desktop

A native desktop application for downloading YouTube audio with automatic cookie extraction and multi-tier fallback strategies.

## Features

- **Native Desktop Window**: Qt-based application with embedded web interface
- **Single Instance Lock**: Prevents multiple instances from running simultaneously
- **Auto Cookie Extraction**: Automatically extracts browser cookies for YouTube authentication (Chrome, Firefox, Edge, Brave)
- **3-Tier Download Strategy**: Progressive fallback system for robust downloading
- **Quit Confirmation**: Warns before closing if downloads are in progress
- **Cross-Platform**: Runs on Linux, Windows, and macOS
- **Standalone Binary**: Can be packaged as a single executable with PyInstaller

## Prerequisites

- **Python 3.11+** (for running from source)
- **FFmpeg** (for audio format conversion)

### Installing FFmpeg

**Linux (Debian/Ubuntu):**
```bash
sudo apt install ffmpeg
```

**Linux (Arch):**
```bash
sudo pacman -S ffmpeg
```

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Add to PATH

**macOS:**
```bash
brew install ffmpeg
```

## Quick Start

### Option 1: Run from Source
```bash
# Clone the repository
git clone <repository-url>
cd audio-fetch

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python desktop_main.py
```

### Option 2: Build Standalone Binary

**Linux:**
```bash
pip install -r requirements.txt
pyinstaller audio-fetch.spec --clean
./dist/audio-fetch
```

**Windows:**

See [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md) for detailed Windows build instructions.

## How It Works

1. **Application starts** → checks for existing instance via lock file
2. **FastAPI server starts** on configured port (default: 8000)
3. **Qt window opens** with embedded WebEngine browser
4. **User pastes YouTube URL** → app extracts cookies from installed browsers
5. **Download uses 3-tier strategy**:
   - Tier 1: Basic yt-dlp with cookies
   - Tier 2: Advanced yt-dlp options (ignore errors, extract-audio)
   - Tier 3: Mobile client emulation and OAuth2
6. **Files saved** to configured download directory

## Configuration

Configuration is stored in platform-specific locations:

- **Linux**: `~/.config/audio-fetch/config.json`
- **Windows**: `%APPDATA%\audio-fetch\config.json`
- **macOS**: `~/Library/Application Support/audio-fetch/config.json`

### Default Configuration

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

### Configuration Options

- `server.port`: Port for embedded FastAPI server (default: 8000)
- `server.auto_detect_port`: Automatically find available port if default is busy (default: true)
- `download.default_path`: Where downloaded files are saved
- `logging.level`: Log verbosity (DEBUG, INFO, WARNING, ERROR)
- `logging.file`: Path to log file

See [docs/CONFIG_SCHEMA.md](docs/CONFIG_SCHEMA.md) for complete schema documentation.

## YouTube Authentication

YouTube requires authentication to download videos. Audio Fetch handles this automatically:

### Automatic Cookie Extraction

The app automatically extracts cookies from installed browsers:
- Chrome / Chromium
- Firefox
- Microsoft Edge
- Brave

**How it works:**
1. App detects installed browsers on your system
2. When a download starts, cookies are extracted from browser profiles
3. Cookies are passed to yt-dlp for authentication
4. No manual cookie export needed!


## Troubleshooting

### "Audio Fetch is already running"

**Cause:** Another instance is already running, or a stale lock file exists.

**Solution:**
1. Check if the app is running in Task Manager / System Monitor
2. If not running, manually delete the lock file:
   - Linux: `~/.config/audio-fetch/app.lock`
   - Windows: `%APPDATA%\audio-fetch\app.lock`
   - macOS: `~/Library/Application Support/audio-fetch/app.lock`

### "Port 8000 is already in use"

**Cause:** Another application is using port 8000.

**Solution:**
1. Enable auto port detection in config:
   ```json
   {
     "server": {
       "auto_detect_port": true
     }
   }
   ```
2. Or manually specify a different port

### Browser cookies not found

**Cause:** Browser is not installed or cookies cannot be accessed.

**Solution:**
1. Ensure browser (Chrome/Firefox/Edge/Brave) is installed
2. Log in to YouTube at least once
3. Try running app with elevated permissions (may be needed for Firefox)

### Downloads fail with "Sign in to confirm you're not a bot"

**Cause:** YouTube bot detection, cookies expired, or no authentication.

**Solution:**
1. Ensure you're logged in to YouTube in your browser
2. Clear browser cache and log in again
3. The 3-tier strategy will automatically retry with different methods

### Qt/PySide6 errors on Linux

**Cause:** Missing system Qt libraries.

**Solution:**
```bash
# Debian/Ubuntu
sudo apt install libxcb-xinerama0 libxcb-cursor0

# Arch
sudo pacman -S qt6-base
```

### FFmpeg not found

**Cause:** FFmpeg not installed or not in PATH.

**Solution:**
- Install FFmpeg (see Prerequisites section)
- Verify: `ffmpeg -version`
- Without FFmpeg, only m4a format is available

### Logs not appearing

**Cause:** Default log level is WARNING.

**Solution:**
- Change `logging.level` to `INFO` or `DEBUG` in config
- Check log file location: `~/.config/audio-fetch/logs/app.log`

## Development

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/

# Run desktop tests only
pytest tests/desktop/ -v

# Run with coverage
pytest tests/ --cov=desktop --cov=services --cov=api --cov-report=html

# Run specific test file
pytest tests/desktop/test_server_manager.py -v
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

## Architecture

Audio Fetch uses a hybrid architecture:

- **Desktop Layer** (Qt/PySide6): Native window, system integration, process management
- **Server Layer** (FastAPI/Uvicorn): Embedded HTTP server running in background thread
- **UI Layer** (HTML/CSS/JS): Web interface rendered in Qt WebEngine
- **Service Layer** (yt-dlp): Download orchestration with tier strategy

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Release Process

This project uses automated GitHub Actions workflows for releases.

### For Release Managers

See [Release Management Guide](docs/RELEASE.md) for detailed instructions on:
- Triggering releases via GitHub Actions
- Version bump options (patch/minor/major)
- Reviewing and publishing release drafts
- Troubleshooting build issues

### Release Artifacts

Each release includes pre-built binaries:
- **Linux AppImage** - Universal, runs on any Linux distribution
- **Linux .deb** - For Debian/Ubuntu systems
- **Linux .rpm** - For Fedora/RHEL/CentOS systems  
- **Windows Installer** - Setup executable for Windows

Download from the [Releases](../../releases) page.


## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Configuration Schema](docs/CONFIG_SCHEMA.md)
- [Building for Windows](docs/BUILD_WINDOWS.md)
- [Cookie Export Guide](docs/COOKIE_EXPORT_GUIDE.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
