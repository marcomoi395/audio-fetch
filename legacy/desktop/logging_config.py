"""Logging configuration for Audio Fetch desktop application."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_file: str,
    level: str = "WARNING",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 3,
) -> None:
    """Configure application logging with rotation.

    Sets up a rotating file handler that writes logs to the specified file
    with automatic rotation when the file reaches max_bytes.

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum bytes per log file before rotation (default 10MB)
        backup_count: Number of backup files to keep (default 3)

    Example:
        setup_logging(
            "~/.config/audio-fetch/logs/app.log",
            level="WARNING",
            max_bytes=10485760,
            backup_count=3
        )
    """
    # Create parent directory if needed
    log_path = Path(log_file).expanduser().resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.WARNING)

    # Get root logger
    root_logger = logging.getLogger()

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Set level
    root_logger.setLevel(numeric_level)

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)

    # Create console handler for ERROR and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Apply formatter to handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_path} (level={level})")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
