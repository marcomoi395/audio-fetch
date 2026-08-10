"""FastAPI server lifecycle manager for desktop application."""

import asyncio
import logging
import socket
import threading

import uvicorn

logger = logging.getLogger(__name__)


class ServerManager:
    """Manages FastAPI server lifecycle in background thread.

    Handles server startup, shutdown, and port management for the desktop app.

    Attributes:
        host: Server host address (default: 127.0.0.1)
        port: Server port (0 for auto-detect)
        auto_detect: Enable auto port detection if specified port unavailable
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8000, auto_detect: bool = True) -> None:
        """Initialize ServerManager.

        Args:
            host: Server host address
            port: Server port (0 for auto-detect)
            auto_detect: Try finding free port if specified port unavailable
        """
        self.host = host
        self.port = port
        self.auto_detect = auto_detect
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def is_running(self) -> bool:
        """Check if server is currently running.

        Returns:
            True if server is running, False otherwise
        """
        return self._running and self._thread is not None and self._thread.is_alive()

    def get_url(self) -> str:
        """Get the server URL.

        Returns:
            Server URL as string (e.g., "http://127.0.0.1:8000")
        """
        return f"http://{self.host}:{self.port}"

    async def start(self, timeout: int = 10) -> None:
        """Start FastAPI server in background thread.

        Args:
            timeout: Maximum seconds to wait for server readiness

        Raises:
            RuntimeError: If server is already running or fails to start
        """
        if self.is_running():
            raise RuntimeError("Server is already running")

        # Find available port
        if self.port == 0 or (self.auto_detect and not self._is_port_available(self.port)):
            self.port = self._find_free_port()
            logger.info(f"Using auto-detected port: {self.port}")

        # Import main app
        from main import app

        # Configure uvicorn
        config = uvicorn.Config(
            app, host=self.host, port=self.port, log_level="warning", access_log=False
        )
        self._server = uvicorn.Server(config)

        # Start server in background thread
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._running = True
        self._thread.start()

        # Wait for server to be ready
        ready = await self._wait_for_ready(timeout)
        if not ready:
            self._running = False
            raise TimeoutError("Server failed to start within timeout")

        logger.warning(f"FastAPI server started at {self.get_url()}")

    async def stop(self) -> None:
        """Stop FastAPI server gracefully."""
        if not self.is_running():
            return

        self._running = False

        # Signal uvicorn server to exit
        if self._server:
            self._server.should_exit = True

        # Wait for thread to finish
        if self._thread:
            self._thread.join(timeout=5)

        logger.warning("FastAPI server stopped")

    def _run_server(self) -> None:
        """Run uvicorn server (executed in background thread)."""
        if self._server:
            asyncio.run(self._server.serve())

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available.

        Args:
            port: Port number to check

        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, port))
                return True
        except OSError:
            return False

    def _find_free_port(self, start: int = 8000, end: int = 8100) -> int:
        """Find a free port in the specified range.

        Args:
            start: Start of port range
            end: End of port range

        Returns:
            Available port number

        Raises:
            RuntimeError: If no free port found in range
        """
        for port in range(start, end + 1):
            if self._is_port_available(port):
                return port

        raise RuntimeError(f"No free port found in range {start}-{end}")

    async def _wait_for_ready(self, timeout: int) -> bool:
        """Wait for server to be ready to accept connections.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if server became ready, False if timeout
        """
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # Try to connect to the server port
                socket.create_connection((self.host, self.port), timeout=1.0)
                return True
            except (ConnectionRefusedError, OSError):
                await asyncio.sleep(0.1)

        return False
