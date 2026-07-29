"""Single-threaded download queue using asyncio.Lock."""

import asyncio


class DownloadQueue:
    """
    Single-threaded download queue to prevent concurrent downloads.

    Uses asyncio.Lock to ensure only one download happens at a time.
    Implements singleton pattern so all instances share the same lock.
    """

    _lock: asyncio.Lock | None = None
    _active: bool = False

    def __init__(self):
        """Initialize the download queue with shared lock."""
        # Singleton pattern: all instances share the same lock
        if DownloadQueue._lock is None:
            DownloadQueue._lock = asyncio.Lock()

    def is_active(self) -> bool:
        """
        Check if a download is currently in progress.

        Returns:
            True if download is active, False otherwise
        """
        return DownloadQueue._active

    async def __aenter__(self):
        """
        Acquire the download lock (async context manager entry).

        Returns:
            self
        """
        assert DownloadQueue._lock is not None  # Guaranteed by __init__
        await DownloadQueue._lock.acquire()
        DownloadQueue._active = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Release the download lock (async context manager exit).

        Ensures lock is released even if an exception occurs.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred

        Returns:
            False to propagate exceptions
        """
        DownloadQueue._active = False
        assert DownloadQueue._lock is not None  # Guaranteed by __init__
        DownloadQueue._lock.release()
        return False


# Download queue will be implemented to prevent concurrent downloads
