"""Desktop application window using PySide6 QWebEngineView."""

import httpx
from PySide6.QtCore import QPoint, QStandardPaths, Qt, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox


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
        self._drag_position = QPoint()
        self._force_closing = False  # Flag to skip download check
        self._init_ui(width, height, title)

    def _init_ui(self, width: int, height: int, title: str) -> None:
        """Initialize UI components.

        Args:
            width: Window width
            height: Window height
            title: Window title
        """
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        # Enable frameless window with custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Embed web UI
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(self.server_url))
        self.setCentralWidget(self.browser)

        # Set up download handler
        self.browser.page().profile().downloadRequested.connect(self._handle_download)

        # Enable JavaScript to call window drag
        self.browser.page().runJavaScript("""
            window.startDrag = function(x, y) {
                return JSON.stringify({x: x, y: y});
            };
        """)

    def start_window_drag(self, x: int, y: int) -> None:
        """Start dragging the window from the given position.

        Args:
            x: X coordinate relative to window
            y: Y coordinate relative to window
        """
        self._drag_position = QPoint(x, y)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for window dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def force_close(self) -> None:
        """Force close the window without confirmation (called from title bar button).

        Uses non-blocking approach to avoid 'Not Responding' dialog on Hyprland.
        """
        from PySide6.QtCore import QTimer

        # Set flag to skip download check
        self._force_closing = True

        # Emit signal immediately
        self.window_closed.emit()

        # Defer actual close to event loop (non-blocking)
        QTimer.singleShot(0, self.close)

    def closeEvent(self, event) -> None:
        """Handle window close event with quit confirmation.

        Checks for active downloads and prompts user to confirm
        if downloads are in progress, unless force_closing flag is set.

        Args:
            event: QCloseEvent
        """
        # Skip download check if force closing from title bar button
        if self._force_closing:
            event.accept()
            return

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
            # Use very short timeout to avoid blocking on Hyprland/Wayland
            response = httpx.get(f"{self.server_url}/api/queue", timeout=0.5)
            queue_data = response.json()
            items = queue_data.get("items", [])

            # Check for any non-completed downloads
            for item in items:
                status = item.get("status", "")
                if status in ["pending", "downloading"]:
                    return True

            return False
        except Exception:
            # Fail-safe: if we can't check queue quickly, allow quit
            return False

    def _handle_download(self, download: QWebEngineDownloadRequest) -> None:
        """Handle download requests with file save dialog.

        Args:
            download: QWebEngineDownloadRequest object
        """
        # Get suggested filename from download
        suggested_filename = download.downloadFileName()

        # Clean up the filename - remove extra extensions and sanitize
        import re
        from pathlib import Path

        # Parse filename
        path = Path(suggested_filename)

        # Clean the stem (remove invalid characters for Windows/Linux)
        clean_stem = re.sub(r'[<>:"|?*]', "", path.stem)
        clean_stem = re.sub(r"[\x00-\x1f\x7f]", "", clean_stem)
        clean_stem = clean_stem.strip()

        # Reconstruct filename
        if clean_stem:
            suggested_filename = f"{clean_stem}{path.suffix}"

        # Get default download directory
        default_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        default_path = f"{default_dir}/{suggested_filename}"

        # Show save file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Audio File",
            default_path,
            "Audio Files (*.mp3 *.m4a *.opus *.wav);;All Files (*)",
        )

        # If user selected a path, proceed with download
        if file_path:
            download.setDownloadFileName(file_path)
            download.accept()
        else:
            # User cancelled
            download.cancel()
