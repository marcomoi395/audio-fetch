"""Pytest fixtures for desktop application tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create temporary config directory for tests.

    Yields:
        Path to temporary config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "audio-fetch"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def temp_log_dir() -> Generator[Path, None, None]:
    """Create temporary log directory for tests.

    Yields:
        Path to temporary log directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "logs"
        log_dir.mkdir(parents=True)
        yield log_dir


@pytest.fixture
def mock_config_data() -> dict:
    """Return mock configuration data for tests.

    Returns:
        Dictionary with valid config structure
    """
    return {
        "version": "1.0",
        "server": {"port": 8000, "auto_detect_port": True},
        "download": {"default_path": "~/Downloads/audio-fetch"},
        "tier_strategy": {
            "browser": "chrome",
            "fallback_browsers": ["firefox", "edge", "brave"],
            "enable_tier2": True,
            "enable_tier3": False,
        },
        "ui": {"window_width": 1200, "window_height": 800},
        "logging": {
            "level": "WARNING",
            "file": "~/.config/audio-fetch/logs/app.log",
            "max_bytes": 10485760,
            "backup_count": 3,
        },
    }
