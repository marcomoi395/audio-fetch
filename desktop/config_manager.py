"""Configuration management for audio-fetch desktop application.

Handles loading, validating, saving, and providing access to application configuration.
Follows XDG Base Directory Specification on Linux, %APPDATA% on Windows.
"""

import json
import logging
import os
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration schema
DEFAULT_CONFIG = {
    "server": {"port": 8000, "host": "127.0.0.1", "auto_detect": True},
    "downloads": {"default_path": "~/Downloads/AudioFetch"},
    "tier_strategy": {"browser": "chrome", "fallback_enabled": True, "tier_1_attempts": 3},
    "ui": {"window_width": 1200, "window_height": 800, "window_title": "Audio Fetch"},
    "logging": {
        "level": "WARNING",
        "file": "~/.local/share/audio-fetch/logs/app.log",
        "max_bytes": 10485760,
        "backup_count": 3,
    },
}

# Required top-level configuration keys
REQUIRED_FIELDS = {"server", "downloads", "tier_strategy", "ui", "logging"}


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""

    pass


class ConfigManager:
    """Manages application configuration loading, validation, and persistence.

    Provides platform-aware configuration path resolution and graceful fallback
    to defaults when configuration is missing or malformed.
    """

    def __init__(self):
        """Initialize ConfigManager with lazy loading of configuration."""
        self._config: dict | None = None
        self._config_path: Path | None = None

    def get_config_path(self) -> Path:
        """Get platform-specific configuration file path.

        Follows XDG Base Directory Specification on Linux:
        - Uses XDG_CONFIG_HOME if set, otherwise ~/.config
        - Returns: ~/.config/audio-fetch/config.json

        On Windows:
        - Uses %APPDATA% environment variable
        - Returns: %APPDATA%\\audio-fetch\\config.json
        Returns:
            Path object pointing to config.json location

        Raises:
            ConfigError: If unable to determine config path
        """
        if self._config_path is not None:
            return self._config_path

        system = platform.system()

        if system == "Linux":
            # Follow XDG Base Directory Specification
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                config_dir = Path(xdg_config_home) / "audio-fetch"
            else:
                config_dir = Path.home() / ".config" / "audio-fetch"
        elif system == "Windows":
            # Use %APPDATA% on Windows
            appdata = os.environ.get("APPDATA")
            if not appdata:
                appdata = str(Path.home() / "AppData" / "Roaming")
            config_dir = Path(appdata) / "audio-fetch"
        elif system == "Darwin":
            # macOS uses ~/.config like Linux
            config_dir = Path.home() / ".config" / "audio-fetch"
        else:
            # Fallback for unknown systems
            config_dir = Path.home() / ".audio-fetch"

        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)

        self._config_path = config_dir / "config.json"
        return self._config_path

    def validate_schema(self, config: dict) -> bool:
        """Validate that config has required top-level fields.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if config contains all required fields, False otherwise
        """
        if not isinstance(config, dict):
            return False

        missing_fields = REQUIRED_FIELDS - set(config.keys())
        if missing_fields:
            logger.warning(f"Config missing required fields: {missing_fields}")
            return False

        return True

    def load(self) -> dict:
        """Load configuration from disk or return defaults.

        Attempts to load configuration from the platform-specific path.
        If the file doesn't exist, is malformed, or invalid, returns default config.

        Returns:
            Configuration dictionary with all required fields

        Note:
            - Malformed JSON is logged as warning, not raised
            - Missing required fields cause fallback to defaults
            - Never raises an exception; always returns a valid config
        """
        if self._config is not None:
            return self._config

        config_path = self.get_config_path()

        # If config file doesn't exist, use defaults
        if not config_path.exists():
            logger.info(f"Config file not found at {config_path}, using defaults")
            self._config = DEFAULT_CONFIG.copy()
            return self._config

        try:
            # Try to read and parse config file
            config_text = config_path.read_text(encoding="utf-8")
            config_data = json.loads(config_text)

            # Validate schema
            if not self.validate_schema(config_data):
                logger.warning(f"Config at {config_path} missing required fields, using defaults")
                self._config = DEFAULT_CONFIG.copy()
                return self._config

            self._config = config_data
            return self._config

        except json.JSONDecodeError as e:
            logger.warning(f"Malformed JSON in {config_path}: {e}, using defaults")
            self._config = DEFAULT_CONFIG.copy()
            return self._config

        except OSError as e:
            logger.warning(f"Failed to read config from {config_path}: {e}, using defaults")
            self._config = DEFAULT_CONFIG.copy()
            return self._config

    def save(self, config: dict) -> None:
        """Save configuration to disk.

        Args:
            config: Configuration dictionary to persist

        Raises:
            ConfigError: If unable to write to config file
        """
        config_path = self.get_config_path()

        try:
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write config as formatted JSON
            config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

            logger.info(f"Configuration saved to {config_path}")
            self._config = config

        except OSError as e:
            msg = f"Failed to save config to {config_path}: {e}"
            logger.error(msg)
            raise ConfigError(msg) from e

    def get_config(self) -> dict:
        """Get current configuration, loading if necessary.

        Returns:
            Current configuration dictionary
        """
        if self._config is None:
            self.load()
        return self._config
