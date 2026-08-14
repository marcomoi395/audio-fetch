"""Single instance enforcement using lock files."""

import os
from pathlib import Path


class InstanceLock:
    """Manages single instance enforcement via lock file.

    Creates a lock file containing PID and port number. Detects stale locks
    by checking if the PID is still running.

    Example:
        lock = InstanceLock("/path/to/app.lock")
        if lock.acquire(port=8000):
            try:
                # Run application
                pass
            finally:
                lock.release()

        # Or use as context manager
        with InstanceLock("/path/to/app.lock") as lock:
            if lock.acquire(port=8000):
                # Run application
                pass
    """

    def __init__(self, lock_file_path: str) -> None:
        """Initialize InstanceLock.

        Args:
            lock_file_path: Path to lock file
        """
        self.lock_file = Path(lock_file_path)
        self._acquired = False

    def acquire(self, port: int) -> bool:
        """Acquire lock for this instance.

        Args:
            port: Port number this instance will use

        Returns:
            True if lock acquired, False if another instance is running
        """
        # Check if lock file exists
        if self.lock_file.exists():
            # Try to read existing lock
            info = self.get_lock_info()
            if info is not None:
                pid = info.get("pid")
                if pid and self._is_process_running(pid):
                    # Another instance is running
                    return False

            # Lock is stale, remove it
            try:
                self.lock_file.unlink()
            except OSError:
                pass

        # Create lock file
        try:
            # Create parent directory if needed
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)

            # Write PID and port
            current_pid = os.getpid()
            lock_content = f"pid:{current_pid}\nport:{port}"
            self.lock_file.write_text(lock_content)

            # Set secure permissions (owner read/write only) on Unix
            if os.name != "nt":
                self.lock_file.chmod(0o600)

            self._acquired = True
            return True

        except (OSError, PermissionError):
            return False

    def release(self) -> None:
        """Release lock by removing lock file."""
        if not self._acquired:
            return

        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
            self._acquired = False
        except OSError:
            pass

    def get_lock_info(self) -> dict | None:
        """Get information from lock file.

        Returns:
            Dictionary with 'pid' and 'port' keys, or None if file missing/invalid
        """
        if not self.lock_file.exists():
            return None

        try:
            content = self.lock_file.read_text()
            lines = content.strip().split("\n")

            info = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    if key == "pid":
                        info["pid"] = int(value)
                    elif key == "port":
                        info["port"] = int(value)

            # Validate we got both fields
            if "pid" in info and "port" in info:
                return info

            return None

        except (OSError, ValueError):
            return None

    def _is_process_running(self, pid: int) -> bool:
        """Check if process with given PID is running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        try:
            # Send signal 0 to check if process exists
            # This doesn't actually send a signal, just checks permissions
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release lock."""
        self.release()
        return False
