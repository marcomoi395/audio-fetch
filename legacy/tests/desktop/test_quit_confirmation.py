"""Tests for AudioFetchWindow quit confirmation dialog."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QMessageBox

from desktop.app_window import AudioFetchWindow


@pytest.fixture
def mock_qapp(qapp):
    """Provide Qt application instance for tests."""
    return qapp


@pytest.fixture
def window(mock_qapp):
    """Create AudioFetchWindow instance for testing."""
    return AudioFetchWindow(server_url="http://127.0.0.1:8000")


class TestQuitConfirmation:
    """Test quit confirmation dialog behavior."""

    def test_close_with_no_downloads_in_progress(self, window):
        """Test closing window when no downloads are active."""
        mock_event = MagicMock()

        with patch("desktop.app_window.httpx.get") as mock_get:
            # Mock empty queue response
            mock_response = MagicMock()
            mock_response.json.return_value = {"items": []}
            mock_get.return_value = mock_response

            # Should close immediately without showing dialog
            window.closeEvent(mock_event)

            mock_event.accept.assert_called_once()
            assert mock_get.called

    def test_close_with_downloads_user_confirms(self, window):
        """Test closing window when downloads active and user confirms."""
        mock_event = MagicMock()

        with patch("desktop.app_window.httpx.get") as mock_get:
            with patch("desktop.app_window.QMessageBox.question") as mock_dialog:
                # Mock active downloads in queue
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "items": [{"url": "https://youtube.com/watch?v=test", "status": "downloading"}]
                }
                mock_get.return_value = mock_response

                # User clicks "Yes" to quit
                mock_dialog.return_value = QMessageBox.StandardButton.Yes

                window.closeEvent(mock_event)

                mock_event.accept.assert_called_once()
                mock_dialog.assert_called_once()

    def test_close_with_downloads_user_cancels(self, window):
        """Test closing window when downloads active and user cancels."""
        mock_event = MagicMock()

        with patch("desktop.app_window.httpx.get") as mock_get:
            with patch("desktop.app_window.QMessageBox.question") as mock_dialog:
                # Mock active downloads in queue
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "items": [{"url": "https://youtube.com/watch?v=test", "status": "downloading"}]
                }
                mock_get.return_value = mock_response

                # User clicks "No" to cancel quit
                mock_dialog.return_value = QMessageBox.StandardButton.No

                window.closeEvent(mock_event)

                mock_event.ignore.assert_called_once()
                mock_event.accept.assert_not_called()
                mock_dialog.assert_called_once()

    def test_close_with_queue_check_error(self, window):
        """Test closing when queue check fails (fail-safe behavior)."""
        mock_event = MagicMock()

        with patch("desktop.app_window.httpx.get") as mock_get:
            # Simulate network error
            mock_get.side_effect = Exception("Connection error")

            # Should close anyway (fail-safe)
            window.closeEvent(mock_event)

            mock_event.accept.assert_called_once()

    def test_close_with_pending_downloads(self, window):
        """Test closing with pending (not yet started) downloads."""
        mock_event = MagicMock()

        with patch("desktop.app_window.httpx.get") as mock_get:
            with patch("desktop.app_window.QMessageBox.question") as mock_dialog:
                # Mock pending downloads in queue
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "items": [
                        {"url": "https://youtube.com/watch?v=test1", "status": "pending"},
                        {"url": "https://youtube.com/watch?v=test2", "status": "pending"},
                    ]
                }
                mock_get.return_value = mock_response

                # User confirms quit
                mock_dialog.return_value = QMessageBox.StandardButton.Yes

                window.closeEvent(mock_event)

                mock_event.accept.assert_called_once()
                # Should show dialog for pending downloads too
                mock_dialog.assert_called_once()

    def test_dialog_message_content(self, window):
        """Test that dialog shows appropriate message."""
        mock_event = MagicMock()

        with patch("desktop.app_window.httpx.get") as mock_get:
            with patch("desktop.app_window.QMessageBox.question") as mock_dialog:
                # Mock active downloads
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "items": [{"url": "test", "status": "downloading"}]
                }
                mock_get.return_value = mock_response

                mock_dialog.return_value = QMessageBox.StandardButton.Yes

                window.closeEvent(mock_event)

                # Verify dialog was called with appropriate message
                call_args = mock_dialog.call_args
                assert "download" in call_args[0][2].lower()  # Message text
                assert "progress" in call_args[0][2].lower() or "active" in call_args[0][2].lower()

    def test_window_closed_signal_emitted_on_accept(self, window):
        """Test that window_closed signal is emitted when closing."""
        mock_event = MagicMock()
        signal_emitted = False

        def on_window_closed():
            nonlocal signal_emitted
            signal_emitted = True

        window.window_closed.connect(on_window_closed)

        with patch("desktop.app_window.httpx.get") as mock_get:
            # No downloads
            mock_response = MagicMock()
            mock_response.json.return_value = {"items": []}
            mock_get.return_value = mock_response

            window.closeEvent(mock_event)

            assert signal_emitted is True

    def test_window_closed_signal_not_emitted_on_cancel(self, window):
        """Test that window_closed signal is not emitted when user cancels."""
        mock_event = MagicMock()
        signal_emitted = False

        def on_window_closed():
            nonlocal signal_emitted
            signal_emitted = True

        window.window_closed.connect(on_window_closed)

        with patch("desktop.app_window.httpx.get") as mock_get:
            with patch("desktop.app_window.QMessageBox.question") as mock_dialog:
                # Downloads active
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "items": [{"url": "test", "status": "downloading"}]
                }
                mock_get.return_value = mock_response

                # User cancels
                mock_dialog.return_value = QMessageBox.StandardButton.No

                window.closeEvent(mock_event)

                assert signal_emitted is False
