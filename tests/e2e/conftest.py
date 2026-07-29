"""Playwright-specific fixtures for E2E tests."""
import threading
import pytest
import uvicorn

from main import app

class _Server(threading.Thread):
    """Runs uvicorn on a dynamic port in a daemon thread."""

    def __init__(self):
        super().__init__(daemon=True)
        self.port = 0
        self._started = threading.Event()
        self._config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="info")
        self._server = uvicorn.Server(self._config)

        # Patch startup to capture the actual port assigned by OS
        original_startup = self._server.startup

        async def _startup(sockets=None):
            await original_startup(sockets)
            if self._server.servers:
                sock = self._server.servers[0].sockets[0]
                self.port = sock.getsockname()[1]
            self._started.set()

        self._server.startup = _startup

    def run(self):
        import asyncio
        asyncio.run(self._server.serve())

    def stop(self):
        self._server.should_exit = True


@pytest.fixture(scope="session")
def live_server():
    """Start FastAPI on a dynamic port; yield base URL; stop after session."""
    import time
    import socket

    server = _Server()
    server.start()

    if not server._started.wait(timeout=10):
        server.stop()
        raise RuntimeError("Live server failed to start within 10 seconds")

    # Extra wait just to ensure the port binds completely
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", server.port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
            
    yield f"http://127.0.0.1:{server.port}"
    server.stop()
    server.join(timeout=5)


@pytest.fixture(autouse=True)
def block_external_requests(page):
    """Block external CSS/Fonts requests to prevent test timeouts in Playwright."""
    def intercept_route(route):
        if "unpkg.com" in route.request.url or "googleapis.com" in route.request.url or "gstatic.com" in route.request.url:
            route.abort()
        else:
            route.continue_()
            
    page.route("**/*", intercept_route)
    yield
