# Configuration Schema Documentation

## Overview

The Audio Fetch application uses a JSON-based configuration system stored in `config/default_config.json`. This document describes all available configuration options, their purposes, valid values, and platform-specific considerations.

### Configuration System

The configuration system is organized into five main sections:
1. **server** - HTTP server settings and port configuration
2. **downloads** - Download behavior and storage locations
3. **tier_strategy** - Browser selection and fallback strategy
4. **ui** - Desktop application window settings
5. **logging** - Application logging configuration

All paths support tilde expansion (`~`) for home directories and environment variables.

---

## Server Configuration

### Purpose
Controls the HTTP server that runs the audio download backend. The server hosts the REST API and handles download requests.

### Options

#### `port` (integer, default: 8000)
The TCP port on which the server listens.
- Valid range: 1024-65535 (avoid ports < 1024 which require admin privileges)
- Example: `"port": 8080`

#### `host` (string, default: "127.0.0.1")
The network interface the server binds to.
- `"127.0.0.1"` - Listen only on localhost (secure, local only)
- `"0.0.0.0"` - Listen on all interfaces (allows remote connections)
- `"192.168.1.100"` - Bind to specific IP address
- Default `127.0.0.1` is recommended for security

#### `auto_detect` (boolean, default: true)
Automatically detect and use available ports if the specified port is in use.
- `true` - Search for next available port starting from `port`
- `false` - Fail if specified port is unavailable
- Useful for running multiple instances

### Example
```json
"server": {
  "port": 8000,
  "host": "127.0.0.1",
  "auto_detect": true
}
```

---

## Downloads Configuration

### Purpose
Configures download behavior and specifies where downloaded audio files are stored.

### Options

#### `default_path` (string, default: "~/Downloads/AudioFetch")
The default directory where downloaded audio files are saved.
- Supports tilde expansion: `~/Downloads/AudioFetch` expands to user's home directory
- Supports environment variables: `$HOME/music` or `${HOME}/music`
- Directory is created automatically if it doesn't exist
- User must have write permissions

### Platform-Specific Defaults

**Linux:**
- `~/.local/share/audio-fetch/downloads` (follows XDG standards)
- Alternative: `~/Music/AudioFetch`

**macOS:**
- `~/Music/AudioFetch`
- Alternative: `~/Downloads/AudioFetch`

**Windows:**
- `%USERPROFILE%\Music\AudioFetch` (expands to C:\Users\YourUsername\Music\...)
- Alternative: `%USERPROFILE%\Downloads\AudioFetch`

### Example
```json
"downloads": {
  "default_path": "~/Downloads/AudioFetch"
}
```

---

## Tier Strategy Configuration

### Purpose
Defines browser selection strategy and fallback behavior for audio extraction. The application uses tiered browser attempts to maximize compatibility.

### Options

#### `browser` (string, default: "chrome")
Primary browser engine to use for audio extraction.
- `"chrome"` - Use Google Chrome/Chromium
- `"firefox"` - Use Mozilla Firefox
- `"chromium"` - Use open-source Chromium (if Chrome unavailable)
- `"safari"` - Use Safari (macOS only)

#### `fallback_enabled` (boolean, default: true)
Enable automatic fallback to alternative browsers if primary fails.
- `true` - Try secondary/tertiary browsers if primary fails
- `false` - Fail immediately if primary browser unavailable
- Increases success rate at cost of slightly longer processing

#### `tier_1_attempts` (integer, default: 3)
Number of retry attempts before moving to next tier browser.
- Valid range: 1-10
- Higher values increase success rate for flaky connections
- Lower values reduce processing time
- Recommended: 2-3 for balanced performance

### Tier Order
1. Primary browser (specified in `browser` option)
2. Secondary browser (auto-selected based on platform)
3. Tertiary browser (fallback option)

### Example
```json
"tier_strategy": {
  "browser": "chrome",
  "fallback_enabled": true,
  "tier_1_attempts": 3
}
```

---

## UI Configuration

### Purpose
Configures the desktop application window behavior and appearance.

### Options

#### `window_width` (integer, default: 1200)
Desktop window width in pixels.
- Minimum: 800 pixels
- Recommended: 1200-1920 pixels
- Example: `"window_width": 1400`

#### `window_height` (integer, default: 800)
Desktop window height in pixels.
- Minimum: 600 pixels
- Recommended: 800-1080 pixels
- Example: `"window_height": 900`

#### `window_title` (string, default: "Audio Fetch")
The title bar text for the desktop application window.
- Can include version info: `"Audio Fetch v1.0"`
- Custom titles for multiple instances: `"Audio Fetch - Instance 2"`

### Example
```json
"ui": {
  "window_width": 1200,
  "window_height": 800,
  "window_title": "Audio Fetch"
}
```

---

## Logging Configuration

### Purpose
Controls application logging verbosity, output format, and file rotation for troubleshooting and monitoring.

### Options

#### `level` (string, default: "WARNING")
Logging output level (minimum severity to log).
- `"DEBUG"` - Very verbose, logs all internal operations
- `"INFO"` - General informational messages
- `"WARNING"` - Only warnings and errors (recommended for production)
- `"ERROR"` - Only error messages
- `"CRITICAL"` - Only critical errors

Log level hierarchy: DEBUG < INFO < WARNING < ERROR < CRITICAL

#### `file` (string, default: "~/.local/share/audio-fetch/logs/app.log")
Path to the application log file.
- Supports tilde and environment variable expansion
- Parent directories created automatically
- User must have write permissions

#### `max_bytes` (integer, default: 10485760)
Maximum size of a single log file in bytes before rotation.
- Default: 10485760 bytes (10 MB)
- Example: 5242880 for 5 MB, 20971520 for 20 MB
- Smaller values increase rotation frequency

#### `backup_count` (integer, default: 3)
Number of rotated log files to keep.
- Default: 3 (keeps app.log plus 3 backups: app.log.1, app.log.2, app.log.3)
- Older files are deleted when count exceeded
- Higher values use more disk space

### Log Rotation
When a log file exceeds `max_bytes`, it's renamed to `app.log.1`, previous `.1` becomes `.2`, etc. Files older than `backup_count` are deleted.

### Platform-Specific Log Locations

**Linux (XDG Base Directory Specification):**
- `~/.local/share/audio-fetch/logs/app.log`
- Alternative: `~/.config/audio-fetch/logs/app.log`

**macOS:**
- `~/Library/Logs/AudioFetch/app.log`
- Alternative: `~/.audio-fetch/logs/app.log`

**Windows:**
- `%APPDATA%\AudioFetch\logs\app.log` (usually C:\Users\YourUsername\AppData\Roaming\AudioFetch\logs\...)
- Alternative: `%LOCALAPPDATA%\AudioFetch\logs\app.log`

### Example
```json
"logging": {
  "level": "WARNING",
  "file": "~/.local/share/audio-fetch/logs/app.log",
  "max_bytes": 10485760,
  "backup_count": 3
}
```

---
## Example Configurations

### Basic Configuration (Default)
Suitable for most users on standard setups:
```json
{
  "server": {
    "port": 8000,
    "host": "127.0.0.1",
    "auto_detect": true
  },
  "downloads": {
    "default_path": "~/Downloads/AudioFetch"
  },
  "tier_strategy": {
    "browser": "chrome",
    "fallback_enabled": true,
    "tier_1_attempts": 3
  },
  "ui": {
    "window_width": 1200,
    "window_height": 800,
    "window_title": "Audio Fetch"
  },
  "logging": {
    "level": "WARNING",
    "file": "~/.local/share/audio-fetch/logs/app.log",
    "max_bytes": 10485760,
    "backup_count": 3
  }
}
```

### Development Configuration
Enhanced logging for debugging:
```json
{
  "server": {
    "port": 8000,
    "host": "127.0.0.1",
    "auto_detect": true
  },
  "downloads": {
    "default_path": "~/Downloads/AudioFetch"
  },
  "tier_strategy": {
    "browser": "chrome",
    "fallback_enabled": true,
    "tier_1_attempts": 5
  },
  "ui": {
    "window_width": 1400,
    "window_height": 900,
    "window_title": "Audio Fetch - Dev"
  },
  "logging": {
    "level": "DEBUG",
    "file": "~/.local/share/audio-fetch/logs/app.log",
    "max_bytes": 5242880,
    "backup_count": 5
  }
}
```

### Linux XDG Configuration
Follows Linux XDG Base Directory specification:
```json
{
  "server": {
    "port": 8000,
    "host": "127.0.0.1",
    "auto_detect": true
  },
  "downloads": {
    "default_path": "$HOME/.local/share/audio-fetch/downloads"
  },
  "tier_strategy": {
    "browser": "chromium",
    "fallback_enabled": true,
    "tier_1_attempts": 3
  },
  "ui": {
    "window_width": 1200,
    "window_height": 800,
    "window_title": "Audio Fetch"
  },
  "logging": {
    "level": "INFO",
    "file": "$HOME/.local/share/audio-fetch/logs/app.log",
    "max_bytes": 10485760,
    "backup_count": 3
  }
}
```

### macOS Configuration
Optimized for macOS with Safari fallback:
```json
{
  "server": {
    "port": 8000,
    "host": "127.0.0.1",
    "auto_detect": true
  },
  "downloads": {
    "default_path": "~/Music/AudioFetch"
  },
  "tier_strategy": {
    "browser": "chrome",
    "fallback_enabled": true,
    "tier_1_attempts": 3
  },
  "ui": {
    "window_width": 1200,
    "window_height": 800,
    "window_title": "Audio Fetch"
  },
  "logging": {
    "level": "WARNING",
    "file": "~/Library/Logs/AudioFetch/app.log",
    "max_bytes": 10485760,
    "backup_count": 3
  }
}
```

### Windows Configuration
Optimized for Windows with APPDATA paths:
```json
{
  "server": {
    "port": 8000,
    "host": "127.0.0.1",
    "auto_detect": true
  },
  "downloads": {
    "default_path": "%USERPROFILE%\\Music\\AudioFetch"
  },
  "tier_strategy": {
    "browser": "chrome",
    "fallback_enabled": true,
    "tier_1_attempts": 3
  },
  "ui": {
    "window_width": 1200,
    "window_height": 800,
    "window_title": "Audio Fetch"
  },
  "logging": {
    "level": "WARNING",
    "file": "%APPDATA%\\AudioFetch\\logs\\app.log",
    "max_bytes": 10485760,
    "backup_count": 3
  }
}
```

### High-Performance Configuration
Optimized for speed with minimal logging:
```json
{
  "server": {
    "port": 8000,
    "host": "127.0.0.1",
    "auto_detect": false
  },
  "downloads": {
    "default_path": "~/Downloads/AudioFetch"
  },
  "tier_strategy": {
    "browser": "chrome",
    "fallback_enabled": false,
    "tier_1_attempts": 1
  },
  "ui": {
    "window_width": 1200,
    "window_height": 800,
    "window_title": "Audio Fetch"
  },
  "logging": {
    "level": "ERROR",
    "file": "~/.local/share/audio-fetch/logs/app.log",
    "max_bytes": 10485760,
    "backup_count": 2
  }
}
```

---

## Configuration Loading and Validation

### Loading Order
1. Built-in defaults (hardcoded in application)
2. `config/default_config.json` (user-provided defaults)
3. Environment variable overrides (if applicable)
4. Command-line arguments (if applicable)

### Path Expansion
All path-based configuration values support:
- **Tilde expansion**: `~/path` → `/home/username/path` (Unix/Linux/macOS)
- **Environment variables**: `$VAR` or `${VAR}` → environment variable value
- **Windows variables**: `%USERPROFILE%`, `%APPDATA%`, `%LOCALAPPDATA%`

### Validation
- JSON syntax is validated on load
- Invalid JSON causes application startup failure with error message
- Out-of-range values for numeric options are logged as warnings
- Missing optional fields use built-in defaults

---

## Troubleshooting

### Configuration not loading
**Symptom:** Application uses default values, config file ignored
**Solutions:**
- Verify `config/default_config.json` exists
- Check JSON syntax: `python -m json.tool config/default_config.json`
- Verify file permissions (readable by application user)
- Check application startup logs

### Port already in use
**Symptom:** Error "Port 8000 already in use"
**Solutions:**
- Set `"auto_detect": true` to find next available port
- Change `"port"` to different value (e.g., 8001, 8080)
- Kill process using port: `lsof -i :8000` (Unix/Linux/macOS)

### Logs not being written
**Symptom:** Log file not created or empty
**Solutions:**
- Verify directory exists and is writable: `mkdir -p ~/.local/share/audio-fetch/logs`
- Check `"level"` setting (DEBUG/INFO generate more logs than WARNING)
- Verify `"file"` path is absolute or correctly expands with `~`
- Check file permissions

### Downloads saving to wrong location
**Symptom:** Files saved to unexpected directory
**Solutions:**
- Verify `"default_path"` contains correct directory
- Check tilde expansion: `echo ~` to see home directory
- Verify path exists and has write permissions
- Check for environment variable conflicts if using `$VAR` syntax

### Browser not found
**Symptom:** "Browser not found" error during extraction
**Solutions:**
- Verify specified browser is installed: `which chrome` / `which firefox`
- Set `"fallback_enabled": true` to use alternative browsers
- Try alternative browser: change `"browser"` to "firefox" or "chromium"
- Increase `"tier_1_attempts"` for unstable connections

---

## Platform-Specific Notes

### Linux
- Follows XDG Base Directory Specification
- Config: `~/.config/audio-fetch/` (if used)
- Data: `~/.local/share/audio-fetch/`
- Logs: `~/.local/share/audio-fetch/logs/`
- Tilde expansion works with `$HOME`

### macOS
- Application Support directory: `~/Library/Application Support/AudioFetch/`
- Logs: `~/Library/Logs/AudioFetch/`
- Music directory: `~/Music/`
- Requires permissions for microphone access (if recording)

### Windows
- User data: `%APPDATA%\AudioFetch\` (usually `C:\Users\Username\AppData\Roaming\...`)
- Local data: `%LOCALAPPDATA%\AudioFetch\` (usually `C:\Users\Username\AppData\Local\...`)
- Music: `%USERPROFILE%\Music\`
- Paths use backslashes or forward slashes

---

## Version History

### v1.0 (Current)
- Initial configuration schema
- Support for server, downloads, tier_strategy, ui, logging sections
- Platform-specific path templates
- Log rotation support

---
