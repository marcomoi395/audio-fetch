"""Desktop application window using PySide6 QWebEngineView."""

import httpx
from PySide6.QtCore import QUrl, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QMessageBox


class AudioFetchWindow(QMainWindow):
    """Main desktop application window.

    Embeds the FastAPI web UI in QWebEngineView without modifications.
    Communicates with backend via localhost HTTP.

    Attributes:
        server_url: Local FastAPI server URL (e.g., "http://127.0.0.1:8000")
        browser: QWebEngineView instance rendering the UI
    """

    window_closed = Signal()  # Emitted when user closes window

    def __init__(
        self,
        server_url: str,
        width: int = 1200,
        height: int = 800,
        title: str = "Audio Fetch",
        parent: QMainWindow | None = None,
    ) -> None:
        """Initialize main window.

        Args:
            server_url: URL of local FastAPI server
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.server_url = server_url
        self._init_ui(width, height, title)

    def _init_ui(self, width: int, height: int, title: str) -> None:
        """Initialize UI components.

        Args:
            width: Window width
            height: Window height
            title: Window title
        """
        self.setWindowTitle(title)
        self.resize(width, height)

        # Embed web UI
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(self.server_url))
        self.setCentralWidget(self.browser)

    def closeEvent(self, event) -> None:
        """Handle window close event with quit confirmation.

        Checks for active downloads and prompts user to confirm
        if downloads are in progress.

        Args:
            event: QCloseEvent
        """
        # Check if downloads are in progress
        if self._has_active_downloads():
            reply = QMessageBox.question(
                self,
                "Quit Audio Fetch",
                "Downloads are in progress. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # User confirmed or no downloads active
        self.window_closed.emit()
        event.accept()

    def _has_active_downloads(self) -> bool:
        """Check if there are active or pending downloads.

        Returns:
            True if downloads are in progress or pending, False otherwise
        """
        try:
            response = httpx.get(f"{self.server_url}/api/queue", timeout=1.0)
            queue_data = response.json()
            items = queue_data.get("items", [])

            # Check for any non-completed downloads
            for item in items:
                status = item.get("status", "")
                if status in ["pending", "downloading"]:
                    return True

            return False
        except Exception:
            # Fail-safe: if we can't check queue, allow quit
            return False
