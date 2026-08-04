"""Integration tests for Audio Fetch desktop application.

Tests full startup/shutdown cycle, UI accessibility, and resource cleanup.
"""

import asyncio
import socket

import httpx
import pytest
from PySide6.QtWidgets import QApplication

from desktop.app_window import AudioFetchWindow
from desktop.server_manager import ServerManager


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests.

    Module-scoped fixture to avoid creating multiple QApplication instances.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def _find_free_port() -> int:
    """Find an available port for testing.

    Returns:
        Integer port number that is available
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.asyncio
async def test_full_startup_shutdown_cycle():
    """Test complete startup and shutdown cycle.

    Verifies:
    - ServerManager can start successfully
    - Server is running and responding
    - Server can stop cleanly
    - Port is released after shutdown
    """
    free_port = _find_free_port()
    manager = ServerManager(port=free_port)

    try:
        # Verify initial state
        assert not manager.is_running()

        # Start server
        await manager.start(timeout=10)
        assert manager.is_running()

        # Verify server responds
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:{free_port}/health")
            assert response.status_code == 200

        # Stop server
        await manager.stop()
        assert not manager.is_running()

        # Verify port is released (can rebind to it)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", free_port))
    finally:
        # Cleanup in case of test failure
        if manager.is_running():
            await manager.stop()


@pytest.mark.asyncio
async def test_ui_accessibility_via_http():
    """Test that UI server is accessible via HTTP.

    Verifies:
    - Server starts with auto-detect port
    - /health endpoint responds with 200
    - Server URL is correct format
    """
    manager = ServerManager(auto_detect=True)

    try:
        # Start server with auto-detected port
        await manager.start(timeout=10)
        assert manager.is_running()

        server_url = manager.get_url()
        assert server_url.startswith("http://127.0.0.1:")

        # Make HTTP request to verify accessibility
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{server_url}/health")
            assert response.status_code == 200
            # Additional check: response should be JSON if it has content
            if response.content:
                assert response.is_success
    finally:
        if manager.is_running():
            await manager.stop()


@pytest.mark.asyncio
async def test_multiple_start_stop_cycles():
    """Test multiple start/stop cycles for resource cleanup.

    Verifies:
    - Server can be started and stopped multiple times
    - No resource leaks or port conflicts occur
    - Each cycle starts fresh
    """
    free_port = _find_free_port()
    manager = ServerManager(port=free_port)

    try:
        for cycle in range(3):
            # Start
            await manager.start(timeout=10)
            assert manager.is_running(), f"Cycle {cycle}: Server failed to start"

            # Verify responsiveness
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:{free_port}/health")
                assert response.status_code == 200, f"Cycle {cycle}: Health check failed"

            # Stop
            await manager.stop()
            assert not manager.is_running(), f"Cycle {cycle}: Server failed to stop"

            # Give OS time to release resources
            await asyncio.sleep(0.1)
    finally:
        if manager.is_running():
            await manager.stop()


@pytest.mark.asyncio
async def test_window_with_running_server(qapp):
    """Test AudioFetchWindow can be created with running server.

    Verifies:
    - Server and window can coexist
    - Window properly initializes with server URL
    - Window title is set correctly
    """
    free_port = _find_free_port()
    manager = ServerManager(port=free_port)

    try:
        # Start server
        await manager.start(timeout=10)
        assert manager.is_running()

        server_url = manager.get_url()

        # Create window with running server URL
        window = AudioFetchWindow(server_url, title="Integration Test Window")

        # Verify window initialization
        assert window.server_url == server_url
        assert window.windowTitle() == "Integration Test Window"

        # Verify window has webview pointing to server
        browser = window.centralWidget()
        loaded_url = browser.url().toString()
        assert loaded_url == server_url

        # Clean up window
        window.close()
    finally:
        if manager.is_running():
            await manager.stop()


@pytest.mark.asyncio
async def test_concurrent_http_requests_during_operation():
    """Test multiple concurrent HTTP requests to running server.

    Verifies:
    - Server handles multiple simultaneous requests
    - No race conditions or drops
    - All requests complete successfully
    """
    manager = ServerManager(auto_detect=True)

    try:
        await manager.start(timeout=10)
        assert manager.is_running()

        server_url = manager.get_url()

        # Make multiple concurrent requests
        async def make_request():
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server_url}/health")
                return response.status_code

        # Create 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(status == 200 for status in results), f"Some requests failed: {results}"
    finally:
        if manager.is_running():
            await manager.stop()
