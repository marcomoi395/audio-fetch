"""Desktop application window using PySide6 QWebEngineView."""


from PySide6.QtCore import QUrl, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow


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
        """Handle window close event.

        Args:
            event: QCloseEvent
        """
        self.window_closed.emit()
        event.accept()
