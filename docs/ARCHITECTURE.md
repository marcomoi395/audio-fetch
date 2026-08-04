# Audio Fetch Desktop Application - Architecture

## System Overview

Audio Fetch Desktop is a PySide6-based desktop application that embeds the FastAPI web UI in a native window. The architecture follows a clean separation between the backend API server and the frontend desktop wrapper.

```
┌─────────────────────────────────────────────────────────┐
│                  Desktop Application                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │         PySide6 QMainWindow                        │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │     QWebEngineView (Chromium Renderer)       │ │ │
│  │  │                                              │ │ │
│  │  │     FastAPI Web UI (HTML/CSS/JS)            │ │ │
│  │  │     http://127.0.0.1:8000                    │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │         ServerManager (Background Thread)          │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │     Uvicorn FastAPI Server                   │ │ │
│  │  │     Port: 8000 (auto-detect if busy)         │ │ │
│  │  │                                              │ │ │
│  │  │  ┌────────────────────────────────────────┐ │ │ │
│  │  │  │  API Routes                            │ │ │ │
│  │  │  │  - /api/video-info                     │ │ │ │
│  │  │  │  - /api/download                       │ │ │ │
│  │  │  │  - /api/queue                          │ │ │ │
│  │  │  └────────────────────────────────────────┘ │ │ │
│  │  │                                              │ │ │
│  │  │  ┌────────────────────────────────────────┐ │ │ │
│  │  │  │  Downloader Service                    │ │ │ │
│  │  │  │  (yt-dlp + 3-tier strategy)            │ │ │ │
│  │  │  └────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Component Interaction

### Startup Flow

1. **desktop_main.py** initializes `DesktopApp`
2. **InstanceLock** checks for running instances
3. **ConfigManager** loads/creates configuration
4. **Logging** initialized with rotation
5. **ServerManager** starts FastAPI in background thread
6. **AudioFetchWindow** creates Qt window with QWebEngineView
7. **QWebEngineView** loads `http://127.0.0.1:8000`

### Shutdown Flow

1. User closes window or presses Ctrl+C
2. **AudioFetchWindow.closeEvent()** checks for active downloads
3. If downloads active → show QMessageBox confirmation
4. If user confirms → emit `window_closed` signal
5. **DesktopApp._cleanup()** stops server and releases lock
6. Qt application exits

## Key Components

### 1. AudioFetchWindow (`desktop/app_window.py`)

**Purpose:** Main application window with embedded web UI

**Key Features:**
- QWebEngineView embeds Chromium renderer
- No modifications to HTML/CSS/JS (zero UI changes)
- Quit confirmation dialog when downloads in progress
- Communicates with backend via HTTP (checks `/api/queue`)

**Signals:**
- `window_closed`: Emitted when window closes (triggers cleanup)

### 2. ServerManager (`desktop/server_manager.py`)

**Purpose:** Manages FastAPI server lifecycle

**Key Features:**
- Runs Uvicorn in background thread (not blocking Qt event loop)
- Auto-detects free port (8000-8100 range)
- Socket-based readiness check (waits for server to accept connections)
- Graceful shutdown via `shutdown()` method

**Thread Safety:**
- Server runs in separate thread
- Qt UI updates via signals/slots (never direct from worker thread)

### 3. InstanceLock (`desktop/instance_lock.py`)

**Purpose:** Enforces single instance of desktop app

**Key Features:**
- Lock file stores PID + port
- Detects stale locks (checks if PID still running via `os.kill(pid, 0)`)
- Secure permissions (0o600 on Unix)
- Context manager support for automatic cleanup

**Lock File Location:**
- Linux: `~/.config/audio-fetch/app.lock`
- Windows: `%APPDATA%/audio-fetch/app.lock`
- macOS: `~/Library/Application Support/audio-fetch/app.lock`

### 4. ConfigManager (`desktop/config_manager.py`)

**Purpose:** Platform-specific configuration management

**Key Features:**
- JSON-based configuration with defaults
- Platform-specific paths (Linux/Windows/macOS)
- Validation and migration support
- Creates parent directories automatically

**Config Structure:**
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
  "tier_strategy": {
    "browser": "chrome",
    "fallback_browsers": ["firefox", "edge", "brave"],
    "enable_tier2": true,
    "enable_tier3": false
  },
  "logging": {
    "level": "WARNING",
    "file": "~/.config/audio-fetch/logs/app.log",
    "max_bytes": 10485760,
    "backup_count": 3
  }
}
```

### 5. TierStrategy (`desktop/tier_strategy.py`)

**Purpose:** Progressive 3-tier fallback for robust YouTube downloads

**Tier 1: Simple (3 attempts)**
- Basic yt-dlp flags
- Fast, no cookies
- Works for most public videos

**Tier 2: Browser Cookies (multiple browsers)**
- Extract cookies from Chrome/Firefox/Edge/Brave
- Authenticates as logged-in user
- Bypasses some age restrictions

**Tier 3: Advanced (optional)**
- Mobile user agents
- PO token generation (bgutil)
- Bypasses bot detection

**Escalation Logic:**
- 403/429 errors → immediate escalation
- Other errors → retry current tier
- Success → stop, return result

### 6. CookieExtractor (`desktop/cookie_extractor.py`)

**Purpose:** Cross-platform browser cookie extraction

**Supported Browsers:**
- Chrome
- Firefox
- Brave
- Edge

**Platform Support:**
- Linux: Detects browser paths, decrypts cookies
- Windows: Uses Windows DPAPI for decryption
- macOS: Uses Keychain for decryption

**Profile Detection:**
- Searches for Default, Profile 1, Profile 2, etc.
- Returns first valid cookie database found

### 7. Logging (`desktop/logging_config.py`)

**Purpose:** Centralized logging with rotation

**Key Features:**
- RotatingFileHandler (10MB max, 3 backups)
- WARNING level default (configurable)
- Console handler for ERROR and above
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

**Log Location:**
- Linux: `~/.config/audio-fetch/logs/app.log`
- Windows: `%APPDATA%/audio-fetch/logs/app.log`
- macOS: `~/Library/Application Support/audio-fetch/logs/app.log`

## Thread Model

### Main Thread (Qt Event Loop)
- Handles UI events
- Renders QWebEngineView
- Processes signals/slots
- **NEVER** blocks for I/O

### Background Thread (FastAPI Server)
- Runs Uvicorn ASGI server
- Handles HTTP requests
- Executes download operations
- **NEVER** updates UI directly (uses signals)

### Communication
- Qt → FastAPI: HTTP requests (via QWebEngineView)
- FastAPI → Qt: Not used (UI polls via HTTP)
- ServerManager → DesktopApp: Python signals/threading events

## Security Considerations

1. **Lock File Permissions:** 0o600 on Unix (owner read/write only)
2. **Cookie Storage:** Temporary files deleted after use
3. **Local-only Server:** Binds to 127.0.0.1 (not exposed externally)
4. **No Remote Code Execution:** Embedded UI is static HTML/CSS/JS

## Packaging (PyInstaller)

### audio-fetch.spec Configuration

**Hidden Imports:**
- FastAPI: `fastapi`, `uvicorn`, `starlette`, `pydantic`
- PySide6: `PySide6.QtWebEngineCore`, `PySide6.QtWebEngineWidgets`
- yt-dlp: `yt_dlp`, `certifi`

**Data Files:**
- Static files: `static/*`
- Templates: `templates/*`

**Binary Size:**
- Linux: ~266MB (includes Qt WebEngine)
- Windows: ~300MB (estimated)

### Build Process

**Linux:**
```bash
pyinstaller audio-fetch.spec
./dist/audio-fetch
```

**Windows:**
See `docs/BUILD_WINDOWS.md` for detailed instructions.

## Testing Strategy

### Unit Tests
- Each component tested in isolation
- Mocked dependencies (no real browser/network access)
- Coverage target: >80%

### Integration Tests
- Basic: Start server, check readiness
- Config: Load/save configuration
- Lock: Single instance enforcement

### Manual Tests
- Launch app → window opens
- Download video → check queue
- Close during download → confirmation dialog
- Launch second instance → error dialog
- Check logs → rotation working

## Future Enhancements

- System tray support (minimize to tray)
- Auto-updater integration
- Notification system for completed downloads
- Custom themes (8-bit, modern, dark mode)
- Keyboard shortcuts
- Download history persistence
