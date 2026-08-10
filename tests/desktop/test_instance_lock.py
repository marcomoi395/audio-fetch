"""Tests for InstanceLock single instance enforcement."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from desktop.instance_lock import InstanceLock


@pytest.fixture
def temp_lock_dir():
    """Create temporary directory for lock files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestInstanceLock:
    """Test InstanceLock functionality."""

    def test_acquire_lock_when_none_exists(self, temp_lock_dir):
        """Test acquiring lock when no lock file exists."""
        lock_file = temp_lock_dir / "app.lock"
        lock = InstanceLock(str(lock_file))

        assert lock.acquire(port=8000) is True
        assert lock_file.exists()

    def test_lock_file_contains_pid_and_port(self, temp_lock_dir):
        """Test lock file contains PID and port number."""
        lock_file = temp_lock_dir / "app.lock"
        lock = InstanceLock(str(lock_file))

        lock.acquire(port=8000)

        content = lock_file.read_text()
        assert "pid:" in content
        assert "port:8000" in content

    def test_release_lock_removes_file(self, temp_lock_dir):
        """Test releasing lock removes lock file."""
        lock_file = temp_lock_dir / "app.lock"
        lock = InstanceLock(str(lock_file))

        lock.acquire(port=8000)
        assert lock_file.exists()

        lock.release()
        assert not lock_file.exists()

    def test_acquire_fails_when_instance_running(self, temp_lock_dir):
        """Test acquiring lock fails when another instance is running."""
        lock_file = temp_lock_dir / "app.lock"

        # First instance
        lock1 = InstanceLock(str(lock_file))
        assert lock1.acquire(port=8000) is True

        # Second instance (should fail)
        lock2 = InstanceLock(str(lock_file))
        assert lock2.acquire(port=8001) is False

    def test_acquire_succeeds_with_stale_lock(self, temp_lock_dir):
        """Test acquiring lock succeeds when lock file contains dead PID."""
        lock_file = temp_lock_dir / "app.lock"

        # Create stale lock with non-existent PID
        lock_file.write_text("pid:999999\nport:8000")

        lock = InstanceLock(str(lock_file))
        assert lock.acquire(port=8000) is True

    def test_is_process_running_returns_true_for_current_process(self):
        """Test is_process_running returns True for current process."""
        current_pid = os.getpid()
        lock = InstanceLock("/tmp/test.lock")

        assert lock._is_process_running(current_pid) is True

    def test_is_process_running_returns_false_for_invalid_pid(self):
        """Test is_process_running returns False for non-existent PID."""
        lock = InstanceLock("/tmp/test.lock")

        # PID 999999 is extremely unlikely to exist
        assert lock._is_process_running(999999) is False

    def test_get_lock_info_returns_none_when_no_lock(self, temp_lock_dir):
        """Test get_lock_info returns None when lock file doesn't exist."""
        lock_file = temp_lock_dir / "app.lock"
        lock = InstanceLock(str(lock_file))

        assert lock.get_lock_info() is None

    def test_get_lock_info_returns_pid_and_port(self, temp_lock_dir):
        """Test get_lock_info returns PID and port from lock file."""
        lock_file = temp_lock_dir / "app.lock"
        lock = InstanceLock(str(lock_file))

        lock.acquire(port=8000)
        info = lock.get_lock_info()

        assert info is not None
        assert "pid" in info
        assert info["port"] == 8000

    def test_get_lock_info_handles_malformed_lock(self, temp_lock_dir):
        """Test get_lock_info handles malformed lock file gracefully."""
        lock_file = temp_lock_dir / "app.lock"
        lock_file.write_text("invalid content")

        lock = InstanceLock(str(lock_file))
        info = lock.get_lock_info()

        # Should return None for malformed file
        assert info is None

    def test_context_manager_releases_lock(self, temp_lock_dir):
        """Test using InstanceLock as context manager releases lock."""
        lock_file = temp_lock_dir / "app.lock"

        with InstanceLock(str(lock_file)) as lock:
            assert lock.acquire(port=8000) is True
            assert lock_file.exists()

        # After context exit, lock should be released
        assert not lock_file.exists()

    def test_release_when_not_acquired(self, temp_lock_dir):
        """Test releasing lock when not acquired doesn't crash."""
        lock_file = temp_lock_dir / "app.lock"
        lock = InstanceLock(str(lock_file))

        # Should not crash
        lock.release()

    def test_acquire_creates_parent_directory(self, temp_lock_dir):
        """Test acquiring lock creates parent directory if missing."""
        lock_file = temp_lock_dir / "subdir" / "app.lock"
        lock = InstanceLock(str(lock_file))

        assert lock.acquire(port=8000) is True
        assert lock_file.exists()
        assert lock_file.parent.exists()

    def test_lock_file_permissions_secure(self, temp_lock_dir):
        """Test lock file has secure permissions (owner read/write only)."""
        lock_file = temp_lock_dir / "app.lock"
        lock = InstanceLock(str(lock_file))

        lock.acquire(port=8000)

        # On Unix, check permissions are 0o600 (owner read/write only)
        if os.name != "nt":  # Skip on Windows
            stat_info = lock_file.stat()
            permissions = stat_info.st_mode & 0o777
            assert permissions == 0o600

    def test_acquire_with_permission_error(self, temp_lock_dir):
        """Test acquiring lock handles permission errors gracefully."""
        lock_file = temp_lock_dir / "app.lock"

        with patch("pathlib.Path.write_text", side_effect=PermissionError):
            lock = InstanceLock(str(lock_file))
            assert lock.acquire(port=8000) is False
