"""Tests for ConfigManager - TDD approach for configuration management."""

import json
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from desktop.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir() -> Path:
    """Create temporary config directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "audio-fetch"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def default_config() -> dict:
    """Return expected default configuration structure."""
    return {
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


class TestConfigManagerDefaults:
    """Test default configuration loading behavior."""

    def test_load_default_config_if_none_exists(self, temp_config_dir, default_config):
        """Test that default config is loaded when no config file exists.

        This tests the RED → GREEN cycle:
        - If no config file exists at get_config_path(), load() should return defaults
        - Defaults should match the expected schema
        """
        config_path = temp_config_dir / "config.json"

        with patch.object(ConfigManager, "get_config_path", return_value=config_path):
            manager = ConfigManager()
            loaded_config = manager.load()

            assert loaded_config is not None
            assert loaded_config["server"]["port"] == 8000
            assert loaded_config["server"]["host"] == "127.0.0.1"
            assert loaded_config["downloads"]["default_path"] == "~/Downloads/AudioFetch"
            assert loaded_config["ui"]["window_width"] == 1200
            assert loaded_config["logging"]["level"] == "WARNING"

    def test_read_existing_config(self, temp_config_dir, default_config):
        """Test reading and parsing an existing config file.

        Scenario:
        - Create a valid config file in temp directory
        - load() should read and parse it correctly
        - Config values should be accessible
        """
        config_path = temp_config_dir / "config.json"
        custom_config = default_config.copy()
        custom_config["server"]["port"] = 9000
        custom_config["ui"]["window_width"] = 1400

        # Write custom config to file
        config_path.write_text(json.dumps(custom_config, indent=2))

        with patch.object(ConfigManager, "get_config_path", return_value=config_path):
            manager = ConfigManager()
            loaded_config = manager.load()

            assert loaded_config["server"]["port"] == 9000
            assert loaded_config["ui"]["window_width"] == 1400
            # Other values should remain as defaults
            assert loaded_config["logging"]["level"] == "WARNING"

    def test_write_config(self, temp_config_dir, default_config):
        """Test writing configuration to disk.

        Scenario:
        - Create ConfigManager instance
        - Modify some config values
        - Call save() to persist changes
        - Verify file exists and contains correct data
        """
        config_path = temp_config_dir / "config.json"

        with patch.object(ConfigManager, "get_config_path", return_value=config_path):
            manager = ConfigManager()

            # Modify config
            custom_config = default_config.copy()
            custom_config["server"]["port"] = 8888
            custom_config["ui"]["window_title"] = "Custom Title"

            # Save config
            manager.save(custom_config)

            # Verify file was created and contains the data
            assert config_path.exists()
            saved_data = json.loads(config_path.read_text())
            assert saved_data["server"]["port"] == 8888
            assert saved_data["ui"]["window_title"] == "Custom Title"


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_validation_rejects_invalid_json(self, temp_config_dir):
        """Test that load() gracefully handles invalid JSON.

        Scenario:
        - Config file contains malformed JSON
        - load() should detect this and fall back to defaults
        - Should log a warning
        - Should NOT raise an exception
        """
        config_path = temp_config_dir / "config.json"
        config_path.write_text("{ invalid json content }")

        with patch.object(ConfigManager, "get_config_path", return_value=config_path):
            manager = ConfigManager()
            loaded_config = manager.load()

            # Should still load defaults instead of crashing
            assert loaded_config is not None
            assert loaded_config["server"]["port"] == 8000

    def test_validation_rejects_missing_required_fields(self, temp_config_dir):
        """Test that load() validates required config fields.

        Scenario:
        - Config file is valid JSON but missing required top-level keys
        - validate_schema() should detect missing fields
        - load() should fall back to defaults or raise ConfigError
        """
        config_path = temp_config_dir / "config.json"
        incomplete_config = {
            "server": {"port": 8000}
            # Missing: downloads, tier_strategy, ui, logging
        }
        config_path.write_text(json.dumps(incomplete_config))

        with patch.object(ConfigManager, "get_config_path", return_value=config_path):
            manager = ConfigManager()

            # Should either validate and reject, or load with defaults merged
            is_valid = manager.validate_schema(incomplete_config)
            assert is_valid is False

    def test_malformed_json_uses_defaults(self, temp_config_dir, default_config):
        """Test that malformed JSON causes fallback to defaults.

        Scenario:
        - Config file contains JSON with unclosed braces
        - load() catches JSONDecodeError
        - Returns default config instead
        - Logs warning (optional for now)
        """
        config_path = temp_config_dir / "config.json"
        config_path.write_text('{"server": {"port": 8000}')  # Missing closing braces

        with patch.object(ConfigManager, "get_config_path", return_value=config_path):
            manager = ConfigManager()
            loaded_config = manager.load()

            # Should fall back to defaults, not crash
            assert loaded_config is not None
            assert "server" in loaded_config
            assert "downloads" in loaded_config
            assert "tier_strategy" in loaded_config


class TestPlatformSpecificPaths:
    """Test platform-specific configuration path handling."""

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific test")
    def test_platform_paths_linux(self, temp_config_dir):
        """Test config path resolution on Linux.

        Linux should follow XDG Base Directory Specification:
        - XDG_CONFIG_HOME if set, otherwise ~/.config
        - Config file: ~/.config/audio-fetch/config.json
        """
        manager = ConfigManager()
        config_path = manager.get_config_path()

        # Should be in a reasonable location on Linux
        assert config_path.is_absolute()
        # Should contain audio-fetch in the path
        assert "audio-fetch" in str(config_path)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_platform_paths_windows(self, temp_config_dir):
        """Test config path resolution on Windows.

        Windows should use %APPDATA%:
        - %APPDATA%\\audio-fetch\\config.json
        """
        manager = ConfigManager()
        config_path = manager.get_config_path()

        # Should be an absolute path
        assert config_path.is_absolute()
        # Should contain audio-fetch in the path
        assert "audio-fetch" in str(config_path)

    def test_platform_paths_respects_xdg_config_home(self):
        """Test that get_config_path() respects XDG_CONFIG_HOME on Linux.

        Scenario:
        - Set XDG_CONFIG_HOME to a custom path
        - get_config_path() should use that path
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_config_home = Path(tmpdir) / "custom-config"
            custom_config_home.mkdir(parents=True)

            with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(custom_config_home)}):
                manager = ConfigManager()
                config_path = manager.get_config_path()

                # Should be under the custom XDG_CONFIG_HOME on Linux
                if platform.system() == "Linux":
                    assert str(custom_config_home) in str(config_path)
