"""Integration tests for audio-fetch desktop app config system.

Tests config integration end-to-end:
- Missing config creates default
- Existing config is respected
- Window size from config is applied
- Port from config is used
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from desktop.app_window import AudioFetchWindow
from desktop.config_manager import DEFAULT_CONFIG, ConfigManager
from desktop.server_manager import ServerManager


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests.

    Yields:
        QApplication instance
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for tests.

    Yields:
        Path to temporary config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "audio-fetch"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def config_file_path(temp_config_dir):
    """Path to config file in temp directory.

    Args:
        temp_config_dir: Temporary config directory

    Returns:
        Path to config.json
    """
    return temp_config_dir / "config.json"


@pytest.fixture
def valid_config_data():
    """Return valid test configuration data.

    Returns:
        Dictionary with valid config structure
    """
    return {
        "server": {"port": 9001, "host": "127.0.0.1", "auto_detect": False},
        "downloads": {"default_path": "~/Downloads/AudioFetch"},
        "tier_strategy": {"browser": "chrome", "fallback_enabled": True, "tier_1_attempts": 3},
        "ui": {"window_width": 1400, "window_height": 900, "window_title": "Test Audio Fetch"},
        "logging": {
            "level": "DEBUG",
            "file": "~/.local/share/audio-fetch/logs/app.log",
            "max_bytes": 10485760,
            "backup_count": 3,
        },
    }


class TestConfigIntegration:
    """Integration tests for config system with app components."""

    @pytest.mark.asyncio
    async def test_app_startup_with_missing_config_creates_default(self, temp_config_dir):
        """Test that app startup with missing config creates default.

        When no config file exists, ConfigManager should:
        1. Load DEFAULT_CONFIG
        2. Return the default configuration
        3. Config can then be saved explicitly if needed
        """
        # Patch get_config_path to use temp directory
        with patch.object(ConfigManager, "get_config_path") as mock_path:
            config_file = temp_config_dir / "config.json"
            mock_path.return_value = config_file

            # Create manager and load (should return default)
            manager = ConfigManager()
            config = manager.load()

            # Verify default config was returned
            assert config is not None
            assert "server" in config
            assert "ui" in config
            assert "downloads" in config
            assert "tier_strategy" in config
            assert "logging" in config

            # Verify defaults match expectations
            assert config["server"]["port"] == DEFAULT_CONFIG["server"]["port"]
            assert config["ui"]["window_width"] == DEFAULT_CONFIG["ui"]["window_width"]
            assert config["ui"]["window_height"] == DEFAULT_CONFIG["ui"]["window_height"]

            # Now explicitly save the config to disk
            manager.save(config)
            assert config_file.exists()
            with open(config_file) as f:
                saved_config = json.load(f)
            assert saved_config["server"]["port"] == DEFAULT_CONFIG["server"]["port"]

    @pytest.mark.asyncio
    async def test_app_startup_with_existing_config_respects_settings(
        self, temp_config_dir, valid_config_data, config_file_path
    ):
        """Test that app startup respects existing config file.

        When config file exists, ConfigManager should:
        1. Load the saved config from disk
        2. NOT override with defaults
        3. Return the loaded configuration
        """
        # Write custom config to disk
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, "w") as f:
            json.dump(valid_config_data, f)

        # Patch get_config_path to use our test config
        with patch.object(ConfigManager, "get_config_path") as mock_path:
            mock_path.return_value = config_file_path

            # Create manager and load
            manager = ConfigManager()
            config = manager.load()

            # Verify custom config was loaded, not defaults
            assert config is not None
            assert config["server"]["port"] == 9001
            assert config["server"]["auto_detect"] is False
            assert config["ui"]["window_width"] == 1400
            assert config["ui"]["window_height"] == 900
            assert config["ui"]["window_title"] == "Test Audio Fetch"
            assert config["logging"]["level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_app_respects_window_size_from_config(
        self, temp_config_dir, config_file_path, qapp
    ):
        """Test that app respects window size settings from config.

        When AudioFetchWindow is initialized, it should:
        1. Accept width/height from config
        2. Apply those dimensions to the window
        3. Verify window has correct size
        """
        # Custom config with specific window dimensions
        window_config = {
            "server": {"port": 8000, "host": "127.0.0.1", "auto_detect": True},
            "downloads": {"default_path": "~/Downloads/AudioFetch"},
            "tier_strategy": {"browser": "chrome", "fallback_enabled": True, "tier_1_attempts": 3},
            "ui": {"window_width": 1600, "window_height": 1000, "window_title": "Test Window"},
            "logging": {
                "level": "WARNING",
                "file": "~/.local/share/audio-fetch/logs/app.log",
                "max_bytes": 10485760,
                "backup_count": 3,
            },
        }

        # Write config and load it
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, "w") as f:
            json.dump(window_config, f)

        with patch.object(ConfigManager, "get_config_path") as mock_path:
            mock_path.return_value = config_file_path

            manager = ConfigManager()
            config = manager.load()

            # Extract UI config and create window
            ui_config = config["ui"]
            window = AudioFetchWindow(
                server_url="http://127.0.0.1:8000",
                width=ui_config["window_width"],
                height=ui_config["window_height"],
                title=ui_config["window_title"],
            )

            # Verify window has correct dimensions from config
            assert window.width() == 1600
            assert window.height() == 1000
            assert window.windowTitle() == "Test Window"

            window.close()

    @pytest.mark.asyncio
    async def test_app_respects_port_from_config(self, temp_config_dir, config_file_path):
        """Test that app respects server port settings from config.

        When ServerManager is initialized, it should:
        1. Accept port from config
        2. Use that port for server URL
        3. Verify server URL is correctly constructed
        """
        # Custom config with specific port
        port_config = {
            "server": {"port": 9050, "host": "127.0.0.1", "auto_detect": False},
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

        # Write config and load it
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, "w") as f:
            json.dump(port_config, f)

        with patch.object(ConfigManager, "get_config_path") as mock_path:
            mock_path.return_value = config_file_path

            manager = ConfigManager()
            config = manager.load()

            # Extract server config and create manager
            server_config = config["server"]
            server_manager = ServerManager(
                host=server_config["host"],
                port=server_config["port"],
                auto_detect=server_config["auto_detect"],
            )

            # Verify server manager has correct port and URL
            assert server_manager.port == 9050
            assert server_manager.host == "127.0.0.1"
            assert server_manager.get_url() == "http://127.0.0.1:9050"
            assert server_manager.is_running() is False
