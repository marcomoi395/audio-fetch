"""Tests for AudioFetchWindow (PySide6 main window)."""

import pytest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from desktop.app_window import AudioFetchWindow


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestAudioFetchWindow:
    """Test suite for AudioFetchWindow class."""

    def test_init_with_server_url(self, qapp):
        """Test window initialization with server URL."""
        server_url = "http://127.0.0.1:8000"
        window = AudioFetchWindow(server_url)

        assert window.server_url == server_url
        assert window.windowTitle() == "Audio Fetch"
        assert window.width() == 1200
        assert window.height() == 800

    def test_window_has_webview(self, qapp):
        """Test that window contains QWebEngineView."""
        window = AudioFetchWindow("http://127.0.0.1:8000")

        central_widget = window.centralWidget()
        assert isinstance(central_widget, QWebEngineView)

    def test_webview_loads_correct_url(self, qapp):
        """Test that QWebEngineView loads the server URL."""
        server_url = "http://127.0.0.1:8000"
        window = AudioFetchWindow(server_url)

        browser = window.centralWidget()
        loaded_url = browser.url().toString()
        assert loaded_url == server_url

    def test_custom_window_size(self, qapp):
        """Test window with custom size."""
        window = AudioFetchWindow("http://localhost:9000", width=1024, height=768)

        assert window.width() == 1024
        assert window.height() == 768

    def test_window_closed_signal_emitted(self, qapp):
        """Test that window_closed signal is emitted on close."""
        window = AudioFetchWindow("http://127.0.0.1:8000")

        signal_emitted = False

        def on_window_closed():
            nonlocal signal_emitted
            signal_emitted = True

        window.window_closed.connect(on_window_closed)

        # Simulate close event
        window.close()

        assert signal_emitted

    def test_window_title_customizable(self, qapp):
        """Test that window title can be customized."""
        window = AudioFetchWindow("http://127.0.0.1:8000", title="Custom Audio Fetch")

        assert window.windowTitle() == "Custom Audio Fetch"

    def test_browser_accessible(self, qapp):
        """Test that browser property provides access to QWebEngineView."""
        window = AudioFetchWindow("http://127.0.0.1:8000")

        assert hasattr(window, "browser")
        assert isinstance(window.browser, QWebEngineView)
