"""Tests for ServerManager (FastAPI lifecycle management)."""

import socket

import httpx
import pytest

from desktop.server_manager import ServerManager


class TestServerManager:
    """Test suite for ServerManager class."""

    def test_init_with_default_port(self):
        """Test initialization with default port."""
        manager = ServerManager()
        assert manager.host == "127.0.0.1"
        assert manager.port == 8000
        assert not manager.is_running()

    def test_init_with_custom_port(self):
        """Test initialization with custom port."""
        manager = ServerManager(host="localhost", port=8080)
        assert manager.host == "localhost"
        assert manager.port == 8080

    @pytest.mark.asyncio
    async def test_start_server_on_specified_port(self):
        """Test starting server on specified port."""
        # Find a free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]

        manager = ServerManager(port=free_port)

        try:
            await manager.start()
            assert manager.is_running()
            assert manager.port == free_port

            # Verify server responds
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://127.0.0.1:{free_port}/health")
                assert response.status_code == 200
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_start_server_auto_detect_port(self):
        """Test starting server with auto port detection."""
        manager = ServerManager(port=0)  # 0 means auto-detect

        try:
            await manager.start()
            assert manager.is_running()
            assert manager.port > 0
            assert manager.port != 0
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_stop_server(self):
        """Test stopping server cleanly."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]

        manager = ServerManager(port=free_port)

        await manager.start()
        assert manager.is_running()

        await manager.stop()
        assert not manager.is_running()

        # Verify port is released
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", free_port))  # Should not raise

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test stopping server when it's not running."""
        manager = ServerManager()
        await manager.stop()  # Should not raise
        assert not manager.is_running()

    def test_get_url(self):
        """Test getting server URL."""
        manager = ServerManager(host="127.0.0.1", port=8000)
        assert manager.get_url() == "http://127.0.0.1:8000"

        manager2 = ServerManager(host="localhost", port=9000)
        assert manager2.get_url() == "http://localhost:9000"

    @pytest.mark.asyncio
    async def test_find_free_port_in_range(self):
        """Test finding free port in range 8000-8100."""
        # Occupy port 8000
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", 8000))
        blocker.listen(1)

        try:
            manager = ServerManager(port=8000, auto_detect=True)
            await manager.start()

            # Should have found a different port
            assert manager.is_running()
            assert manager.port != 8000
            assert 8001 <= manager.port <= 8100
        finally:
            await manager.stop()
            blocker.close()

    @pytest.mark.asyncio
    async def test_double_start_raises_error(self):
        """Test that starting an already running server raises error."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]

        manager = ServerManager(port=free_port)

        try:
            await manager.start()

            with pytest.raises(RuntimeError, match="Server is already running"):
                await manager.start()
        finally:
            await manager.stop()
