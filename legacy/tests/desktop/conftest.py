"""Pytest fixtures for desktop application tests."""

import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create Qt application instance for tests.

    This is a session-scoped fixture that creates a single QApplication
    instance for all GUI tests. Qt requires exactly one QApplication
    instance per process.

    Yields:
        QApplication instance
    """
    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # QApplication cleanup happens automatically at process exit


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
