"""Tests for download queue service."""

import asyncio

import pytest

from services.queue import DownloadQueue


class TestDownloadQueue:
    """Tests for single-threaded download queue."""

    @pytest.mark.asyncio
    async def test_queue_allows_single_download(self):
        """Test that queue allows a single download."""
        queue = DownloadQueue()

        assert not queue.is_active()

        async with queue:
            assert queue.is_active()

        assert not queue.is_active()

    @pytest.mark.asyncio
    async def test_queue_blocks_concurrent_downloads(self):
        """Test that queue blocks concurrent downloads."""
        queue = DownloadQueue()
        download_order = []

        async def mock_download(name: str, delay: float):
            async with queue:
                download_order.append(f"{name}_start")
                await asyncio.sleep(delay)
                download_order.append(f"{name}_end")

        # Start two downloads concurrently
        await asyncio.gather(mock_download("first", 0.1), mock_download("second", 0.05))

        # First download should complete before second starts
        assert download_order == ["first_start", "first_end", "second_start", "second_end"]

    @pytest.mark.asyncio
    async def test_queue_releases_lock_on_exception(self):
        """Test that queue releases lock even when exception occurs."""
        queue = DownloadQueue()

        try:
            async with queue:
                assert queue.is_active()
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Lock should be released
        assert not queue.is_active()

        # Should be able to acquire again
        async with queue:
            assert queue.is_active()

    @pytest.mark.asyncio
    async def test_queue_singleton_behavior(self):
        """Test that multiple instances share the same lock."""
        queue1 = DownloadQueue()
        queue2 = DownloadQueue()

        # Both instances should reference the same lock
        assert queue1._lock is queue2._lock
