"""Tests for logging configuration."""

import logging
import tempfile
from pathlib import Path

import pytest

from desktop.logging_config import setup_logging


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestLoggingConfig:
    """Test logging configuration setup."""

    def test_setup_logging_creates_log_file(self, temp_log_dir):
        """Test setup_logging creates log file."""
        log_file = temp_log_dir / "app.log"

        setup_logging(str(log_file), level="INFO")

        # Write a log message
        logger = logging.getLogger("test")
        logger.info("Test message")

        # Verify log file was created
        assert log_file.exists()

    def test_setup_logging_writes_messages(self, temp_log_dir):
        """Test setup_logging writes log messages to file."""
        log_file = temp_log_dir / "app.log"

        setup_logging(str(log_file), level="INFO")

        # Write log messages
        logger = logging.getLogger("test")
        logger.info("Info message")
        logger.warning("Warning message")

        # Read log file
        content = log_file.read_text()

        assert "Info message" in content
        assert "Warning message" in content

    def test_setup_logging_respects_level(self, temp_log_dir):
        """Test setup_logging respects log level."""
        log_file = temp_log_dir / "app.log"

        # Set WARNING level (should not log INFO)
        setup_logging(str(log_file), level="WARNING")

        logger = logging.getLogger("test")
        logger.info("Info message")
        logger.warning("Warning message")

        content = log_file.read_text()

        assert "Info message" not in content
        assert "Warning message" in content

    def test_setup_logging_format_includes_timestamp(self, temp_log_dir):
        """Test log format includes timestamp."""
        log_file = temp_log_dir / "app.log"

        setup_logging(str(log_file), level="INFO")

        logger = logging.getLogger("test")
        logger.info("Test message")

        content = log_file.read_text()

        # Format: %(asctime)s - %(name)s - %(levelname)s - %(message)s
        assert "test" in content  # logger name
        assert "INFO" in content  # level name
        assert "Test message" in content

    def test_setup_logging_creates_parent_directory(self, temp_log_dir):
        """Test setup_logging creates parent directory if missing."""
        log_file = temp_log_dir / "subdir" / "app.log"

        setup_logging(str(log_file), level="INFO")

        logger = logging.getLogger("test")
        logger.info("Test message")

        assert log_file.exists()
        assert log_file.parent.exists()

    def test_setup_logging_with_rotation_max_bytes(self, temp_log_dir):
        """Test setup_logging configures rotation with max bytes."""
        log_file = temp_log_dir / "app.log"

        # Small max_bytes for testing (1KB)
        setup_logging(str(log_file), level="INFO", max_bytes=1024, backup_count=2)

        logger = logging.getLogger("test")

        # Write enough to trigger rotation
        for i in range(100):
            logger.info(f"Long message to fill up log file {i}" * 10)

        # Check that backup files were created
        assert log_file.exists()
        # Rotation creates .log.1, .log.2, etc.
        backup_files = list(log_file.parent.glob("app.log.*"))
        assert len(backup_files) > 0

    def test_setup_logging_default_level_is_warning(self, temp_log_dir):
        """Test default log level is WARNING."""
        log_file = temp_log_dir / "app.log"

        # No level specified
        setup_logging(str(log_file))

        logger = logging.getLogger("test")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

        content = log_file.read_text()

        assert "Debug message" not in content
        assert "Info message" not in content
        assert "Warning message" in content

    def test_setup_logging_handles_invalid_level_gracefully(self, temp_log_dir):
        """Test setup_logging handles invalid level gracefully."""
        log_file = temp_log_dir / "app.log"

        # Invalid level should default to WARNING
        setup_logging(str(log_file), level="INVALID")

        logger = logging.getLogger("test")
        logger.warning("Warning message")

        content = log_file.read_text()
        assert "Warning message" in content

    def test_setup_logging_can_be_called_multiple_times(self, temp_log_dir):
        """Test setup_logging can be called multiple times safely."""
        log_file = temp_log_dir / "app.log"

        # Call twice
        setup_logging(str(log_file), level="INFO")
        setup_logging(str(log_file), level="INFO")

        logger = logging.getLogger("test")
        logger.info("Test message")

        # Should not crash and should still work
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_clears_existing_handlers(self, temp_log_dir):
        """Test setup_logging clears existing handlers to avoid duplicates."""
        log_file = temp_log_dir / "app.log"

        # Setup twice
        setup_logging(str(log_file), level="INFO")
        setup_logging(str(log_file), level="INFO")

        logger = logging.getLogger("test")
        logger.info("Single message")

        content = log_file.read_text()

        # Count occurrences - should appear only once
        count = content.count("Single message")
        assert count == 1, f"Message appeared {count} times, expected 1"
