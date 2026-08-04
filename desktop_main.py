"""Entry point for Audio Fetch desktop application.

Manages the lifecycle of the FastAPI server and Qt GUI, including graceful
shutdown on user close or system signals (SIGINT/SIGTERM).
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from desktop.app_window import AudioFetchWindow
from desktop.config_manager import ConfigManager
from desktop.instance_lock import InstanceLock
from desktop.server_manager import ServerManager

logger = logging.getLogger(__name__)


class DesktopApp:
    """Desktop application lifecycle manager.

    Coordinates server startup/shutdown with Qt window lifecycle.

    Attributes:
        server: ServerManager instance
        window: AudioFetchWindow instance
        app: QApplication instance
        instance_lock: InstanceLock instance for single-instance enforcement
    """

    def __init__(self) -> None:
        """Initialize application components."""
        self.server: ServerManager | None = None
        self.window: AudioFetchWindow | None = None
        self.app: QApplication | None = None
        self.instance_lock: InstanceLock | None = None
        self._cleanup_pending = False

    def _get_lock_file_path(self) -> Path:
        """Get platform-specific lock file path.

        Returns:
            Path to lock file in config directory
        """
        config_manager = ConfigManager()
        config_dir = config_manager.get_config_dir()
        return config_dir / "app.lock"

    async def run(self) -> int:
        """Run the desktop application.

        Starts the FastAPI server, creates the main window, and runs the Qt
        event loop until the window is closed or a system signal is received.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Initialize Qt application
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()

            # Check for another running instance
            lock_file = self._get_lock_file_path()
            self.instance_lock = InstanceLock(str(lock_file))

            # Try to acquire lock (port will be set after config loads)
            # For now, use a placeholder - we'll update after getting actual port
            if not self.instance_lock.acquire(port=8000):
                # Another instance is running
                info = self.instance_lock.get_lock_info()
                if info:
                    port = info.get("port", "unknown")
                    message = f"Audio Fetch is already running on port {port}."
                else:
                    message = "Audio Fetch is already running."

                QMessageBox.critical(
                    None,
                    "Already Running",
                    message,
                )
                return 1
            # Load configuration
            config_manager = ConfigManager()
            try:
                config = config_manager.load()
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
                config = config_manager.get_config()

            # Start FastAPI server with config values
            server_port = config["server"]["port"]
            server_auto_detect = config["server"]["auto_detect"]
            logger.info("Starting FastAPI server...")
            self.server = ServerManager(
                host="127.0.0.1", port=server_port, auto_detect=server_auto_detect
            )
            await self.server.start(timeout=10)
            server_url = self.server.get_url()
            logger.info(f"Server started at {server_url}")

            # Create main window with config values
            window_width = config["ui"]["window_width"]
            window_height = config["ui"]["window_height"]
            window_title = config["ui"]["window_title"]
            self.window = AudioFetchWindow(
                server_url=server_url,
                width=window_width,
                height=window_height,
                title=window_title,
            )

            # Connect window close signal to cleanup
            self.window.window_closed.connect(self._on_window_closed)

            # Show window
            self.window.show()

            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Run Qt event loop
            logger.info("Starting Qt event loop...")
            exit_code = self.app.exec()
            logger.info(f"Qt event loop exited with code {exit_code}")

            return exit_code

        except Exception as e:
            logger.error(f"Failed to start application: {e}", exc_info=True)
            await self._cleanup()
            return 1

    def _on_window_closed(self) -> None:
        """Handle window close event.

        Triggers application shutdown and cleanup.
        """
        logger.info("Window closed, shutting down...")
        if self.app:
            self.app.quit()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for SIGINT and SIGTERM.

        Enables graceful shutdown when user presses Ctrl+C or system sends
        termination signal.
        """

        def handle_signal(signum, frame):
            """Signal handler for SIGINT and SIGTERM."""
            logger.info(f"Received signal {signum}, shutting down...")
            if self.app:
                self.app.quit()

        # Register signal handlers
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Note: Ctrl+C will trigger SIGINT. On some systems, we also need to
        # ensure the event loop periodically processes signals. This is handled
        # by Qt's event loop, which checks for signals during processing.

    async def _cleanup(self) -> None:
        """Stop server and clean up resources.

        Ensures server is stopped and all resources are released before exit.
        """
        if self._cleanup_pending:
            return
        self._cleanup_pending = True

        if self.server and self.server.is_running():
            logger.info("Stopping server...")
            try:
                await self.server.stop()
                logger.info("Server stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping server: {e}", exc_info=True)

        # Release instance lock
        if self.instance_lock:
            logger.info("Releasing instance lock...")
            self.instance_lock.release()


async def main() -> int:
    """Main entry point for the desktop application.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    app_manager = DesktopApp()
    try:
        return await app_manager.run()
    finally:
        # Ensure cleanup happens
        await app_manager._cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
