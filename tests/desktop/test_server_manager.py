"""Tests for ServerManager - FastAPI server lifecycle management."""

import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from desktop.server_manager import ServerManager


class TestServerManagerInitialization:
    """Test ServerManager initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        manager = ServerManager()
        assert manager.host == "127.0.0.1"
        assert manager.port == 8000
        assert manager.auto_detect is True
        assert manager.is_running() is False

    def test_init_with_custom_port(self):
        """Test initialization with custom port."""
        manager = ServerManager(port=9000)
        assert manager.port == 9000
        assert manager.host == "127.0.0.1"

    def test_init_with_custom_host(self):
        """Test initialization with custom host."""
        manager = ServerManager(host="0.0.0.0")
        assert manager.host == "0.0.0.0"

    def test_init_auto_detect_disabled(self):
        """Test initialization with auto-detect disabled."""
        manager = ServerManager(auto_detect=False)
        assert manager.auto_detect is False


class TestServerManagerURL:
    """Test ServerManager URL generation."""

    def test_get_url_default_port(self):
        """Test get_url with default port."""
        manager = ServerManager()
        assert manager.get_url() == "http://127.0.0.1:8000"

    def test_get_url_custom_port(self):
        """Test get_url with custom port."""
        manager = ServerManager(port=9000)
        assert manager.get_url() == "http://127.0.0.1:9000"

    def test_get_url_custom_host(self):
        """Test get_url with custom host."""
        manager = ServerManager(host="0.0.0.0", port=8080)
        assert manager.get_url() == "http://0.0.0.0:8080"


class TestServerManagerPortDetection:
    """Test port availability detection."""

    def test_is_port_available_free_port(self):
        """Test port availability check with free port."""
        manager = ServerManager()
        # Find an actually free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            free_port = s.getsockname()[1]

        assert manager._is_port_available(free_port) is True

    def test_is_port_available_occupied_port(self):
        """Test port availability check with occupied port."""
        manager = ServerManager()

        # Occupy a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            occupied_port = s.getsockname()[1]

            # Port should be unavailable while socket is bound
            assert manager._is_port_available(occupied_port) is False

    def test_find_free_port_in_range(self):
        """Test finding free port in specified range."""
        manager = ServerManager()
        free_port = manager._find_free_port(start=9000, end=9100)

        assert 9000 <= free_port <= 9100
        assert manager._is_port_available(free_port) is True

    def test_find_free_port_no_ports_available(self):
        """Test finding free port when all ports occupied."""
        manager = ServerManager()

        # This test is hard to implement without actually occupying all ports
        # We'll mock _is_port_available to always return False
        with patch.object(manager, "_is_port_available", return_value=False):
            with pytest.raises(RuntimeError, match="No free port found"):
                manager._find_free_port(start=9000, end=9010)


class TestServerManagerLifecycle:
    """Test server start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_server_specified_port(self):
        """Test starting server on specified port."""
        manager = ServerManager(port=8001, auto_detect=False)

        # Mock uvicorn.Server
        mock_server = AsyncMock()
        mock_server.serve = AsyncMock()

        with patch("desktop.server_manager.uvicorn.Server", return_value=mock_server):
            with patch.object(manager, "_wait_for_ready", return_value=True):
                await manager.start(timeout=5)

                assert manager.is_running() is True
                assert manager._thread is not None
                assert manager._thread.is_alive()

        # Cleanup
        await manager.stop()

    @pytest.mark.asyncio
    async def test_start_server_auto_detect_port(self):
        """Test starting server with auto port detection."""
        manager = ServerManager(port=8000, auto_detect=True)

        # Mock port availability check - simulate port 8000 is occupied
        original_is_available = manager._is_port_available

        def mock_is_available(port):
            if port == 8000:
                return False
            return original_is_available(port)

        with patch.object(manager, "_is_port_available", side_effect=mock_is_available):
            with patch.object(manager, "_find_free_port", return_value=8001):
                mock_server = AsyncMock()
                mock_server.serve = AsyncMock()

                with patch("desktop.server_manager.uvicorn.Server", return_value=mock_server):
                    with patch.object(manager, "_wait_for_ready", return_value=True):
                        await manager.start(timeout=5)

                        # Port should have been changed to 8001
                        assert manager.port == 8001
                        assert manager.is_running() is True

        # Cleanup
        await manager.stop()

    @pytest.mark.asyncio
    async def test_start_server_double_start_raises_error(self):
        """Test that starting server twice raises RuntimeError."""
        manager = ServerManager(port=8002, auto_detect=False)

        mock_server = AsyncMock()
        mock_server.serve = AsyncMock()

        with patch("desktop.server_manager.uvicorn.Server", return_value=mock_server):
            with patch.object(manager, "_wait_for_ready", return_value=True):
                await manager.start(timeout=5)

                # Try to start again - should raise error
                with pytest.raises(RuntimeError, match="Server is already running"):
                    await manager.start(timeout=5)

        # Cleanup
        await manager.stop()

    @pytest.mark.asyncio
    async def test_start_server_timeout(self):
        """Test server start timeout handling."""
        manager = ServerManager(port=8003, auto_detect=False)

        mock_server = AsyncMock()
        mock_server.serve = AsyncMock()

        with patch("desktop.server_manager.uvicorn.Server", return_value=mock_server):
            # Mock _wait_for_ready to return False (timeout)
            with patch.object(manager, "_wait_for_ready", return_value=False):
                with pytest.raises(TimeoutError, match="Server failed to start"):
                    await manager.start(timeout=1)

                # Server should not be marked as running
                assert manager.is_running() is False

    @pytest.mark.asyncio
    async def test_stop_server_cleanly(self):
        """Test stopping server gracefully."""
        manager = ServerManager(port=8004, auto_detect=False)

        mock_server = AsyncMock()
        mock_server.serve = AsyncMock()
        mock_server.should_exit = False

        with patch("desktop.server_manager.uvicorn.Server", return_value=mock_server):
            with patch.object(manager, "_wait_for_ready", return_value=True):
                await manager.start(timeout=5)

                assert manager.is_running() is True

                # Stop the server
                await manager.stop()

                # Should set should_exit flag
                assert mock_server.should_exit is True

                # Should no longer be running
                assert manager.is_running() is False

    @pytest.mark.asyncio
    async def test_stop_server_not_running(self):
        """Test stopping server when not running does nothing."""
        manager = ServerManager()

        # Should not raise error
        await manager.stop()

        assert manager.is_running() is False

    @pytest.mark.asyncio
    async def test_is_running_false_before_start(self):
        """Test is_running returns False before start."""
        manager = ServerManager()
        assert manager.is_running() is False

    @pytest.mark.asyncio
    async def test_is_running_true_after_start(self):
        """Test is_running returns True after successful start."""
        manager = ServerManager(port=8005, auto_detect=False)

        mock_server = AsyncMock()
        mock_server.serve = AsyncMock()

        with patch("desktop.server_manager.uvicorn.Server", return_value=mock_server):
            with patch.object(manager, "_wait_for_ready", return_value=True):
                await manager.start(timeout=5)
                assert manager.is_running() is True

        # Cleanup
        await manager.stop()


class TestServerManagerWaitForReady:
    """Test server readiness checking."""

    @pytest.mark.asyncio
    async def test_wait_for_ready_success(self):
        """Test waiting for server to be ready - success case."""
        manager = ServerManager(port=8006)

        # Mock socket connection to succeed
        with patch("socket.create_connection", return_value=MagicMock()):
            result = await manager._wait_for_ready(timeout=5)
            assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_ready_timeout(self):
        """Test waiting for server to be ready - timeout case."""
        manager = ServerManager(port=8007)

        # Mock socket connection to always fail
        with patch("socket.create_connection", side_effect=ConnectionRefusedError):
            result = await manager._wait_for_ready(timeout=1)
            assert result is False

    @pytest.mark.asyncio
    async def test_wait_for_ready_eventual_success(self):
        """Test waiting for server - succeeds after retries."""
        manager = ServerManager(port=8008)

        # Mock connection to fail first 2 times, then succeed
        call_count = 0

        def mock_connection(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionRefusedError
            return MagicMock()

        with patch("socket.create_connection", side_effect=mock_connection):
            result = await manager._wait_for_ready(timeout=5)
            assert result is True
            assert call_count >= 3
