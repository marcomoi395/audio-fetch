"""Browser cookie path detection and extraction for desktop application.

Handles platform-specific cookie database locations for Chrome, Firefox, Edge,
and Brave browsers on Linux and Windows.
"""

import platform
from enum import Enum
from pathlib import Path


class BrowserType(Enum):
    """Supported browser types for cookie extraction."""

    CHROME = "chrome"
    FIREFOX = "firefox"
    BRAVE = "brave"
    EDGE = "edge"


class CookieExtractor:
    """Detects and extracts browser cookie database paths.

    Handles platform-specific paths for Chrome, Firefox, Edge, and Brave.
    Supports fallback browser detection when preferred browser is not installed.
    """

    def __init__(self) -> None:
        """Initialize cookie extractor with platform detection."""
        self.platform_system = platform.system()
        self.home_dir = Path.home()

    def get_cookie_db_path(self, browser_type: BrowserType) -> Path:
        """Get default cookie database path for a browser.

        Args:
            browser_type: The browser to get cookie path for

        Returns:
            Path to the default cookie database file
        """
        if self.platform_system == "Linux":
            return self._get_linux_path(browser_type)
        elif self.platform_system == "Windows":
            return self._get_windows_path(browser_type)
        elif self.platform_system == "Darwin":
            return self._get_macos_path(browser_type)
        else:
            raise RuntimeError(f"Unsupported platform: {self.platform_system}")

    def _get_linux_path(self, browser_type: BrowserType) -> Path:
        """Get cookie path for Linux.

        Args:
            browser_type: The browser type

        Returns:
            Path to cookie database on Linux
        """
        if browser_type == BrowserType.CHROME:
            return self.home_dir / ".config/google-chrome/Default/Cookies"
        elif browser_type == BrowserType.FIREFOX:
            # Firefox uses profile directories with random names
            firefox_dir = self.home_dir / ".mozilla/firefox"
            return firefox_dir / "*.default-release/cookies.sqlite"
        elif browser_type == BrowserType.BRAVE:
            return self.home_dir / ".config/BraveSoftware/Brave-Browser/Default/Cookies"
        elif browser_type == BrowserType.EDGE:
            return self.home_dir / ".config/microsoft-edge/Default/Cookies"
        else:
            raise ValueError(f"Unknown browser type: {browser_type}")

    def _get_windows_path(self, browser_type: BrowserType) -> Path:
        """Get cookie path for Windows.

        Args:
            browser_type: The browser type

        Returns:
            Path to cookie database on Windows
        """
        if browser_type == BrowserType.CHROME:
            return self.home_dir / "AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
        elif browser_type == BrowserType.FIREFOX:
            firefox_dir = self.home_dir / "AppData/Roaming/Mozilla/Firefox/Profiles"
            return firefox_dir / "*.default-release/cookies.sqlite"
        elif browser_type == BrowserType.BRAVE:
            return (
                self.home_dir
                / "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Network/Cookies"
            )
        elif browser_type == BrowserType.EDGE:
            return self.home_dir / "AppData/Local/Microsoft/Edge/User Data/Default/Network/Cookies"
        else:
            raise ValueError(f"Unknown browser type: {browser_type}")

    def _get_macos_path(self, browser_type: BrowserType) -> Path:
        """Get cookie path for macOS.

        Args:
            browser_type: The browser type

        Returns:
            Path to cookie database on macOS
        """
        if browser_type == BrowserType.CHROME:
            return self.home_dir / "Library/Application Support/Google/Chrome/Default/Cookies"
        elif browser_type == BrowserType.FIREFOX:
            firefox_dir = self.home_dir / "Library/Application Support/Firefox/Profiles"
            return firefox_dir / "*.default-release/cookies.sqlite"
        elif browser_type == BrowserType.BRAVE:
            return (
                self.home_dir
                / "Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies"
            )
        elif browser_type == BrowserType.EDGE:
            return self.home_dir / "Library/Application Support/Microsoft Edge/Default/Cookies"
        else:
            raise ValueError(f"Unknown browser type: {browser_type}")

    def get_all_cookie_paths(self, browser_type: BrowserType) -> list[Path]:
        """Get all potential cookie paths including profiles.

        Args:
            browser_type: The browser type

        Returns:
            List of potential cookie database paths
        """
        paths = []
        base_path = self.get_cookie_db_path(browser_type)

        # For Firefox, expand wildcard profiles
        if "*" in str(base_path):
            parent = base_path.parent.parent
            if parent.exists():
                for profile_dir in parent.glob("*.default*"):
                    cookie_path = profile_dir / "cookies.sqlite"
                    if cookie_path.exists():
                        paths.append(cookie_path)
        else:
            paths.append(base_path)

        # Add common profile variations for Chromium-based browsers
        if browser_type in [BrowserType.CHROME, BrowserType.BRAVE, BrowserType.EDGE]:
            # Also check Profile 1, Profile 2, etc.
            parent = base_path.parent.parent
            if parent.exists():
                for profile_dir in parent.glob("Profile *"):
                    if self.platform_system == "Windows":
                        cookie_path = profile_dir / "Network/Cookies"
                    else:
                        cookie_path = profile_dir / "Cookies"
                    if cookie_path.exists():
                        paths.append(cookie_path)

        return paths

    def is_browser_installed(self, browser_type: BrowserType) -> bool:
        """Check if a browser is installed by checking for cookie database.

        Args:
            browser_type: The browser type to check

        Returns:
            True if browser appears to be installed, False otherwise
        """
        path = self.get_cookie_db_path(browser_type)

        # Handle wildcard paths (Firefox)
        if "*" in str(path):
            parent = path.parent.parent
            if not parent.exists():
                return False
            # Check if any profile directory exists
            return any(parent.glob("*.default*"))

        # For regular paths, check if file exists
        return path.exists()

    def find_installed_browsers(self) -> list[BrowserType]:
        """Find all installed browsers on the system.

        Returns:
            List of installed browser types
        """
        installed = []
        for browser_type in BrowserType:
            if self.is_browser_installed(browser_type):
                installed.append(browser_type)
        return installed

    def get_fallback_order(self, preferred: BrowserType) -> list[BrowserType]:
        """Get browser fallback order starting with preferred.

        Args:
            preferred: Preferred browser to try first

        Returns:
            List of browsers in fallback order
        """
        # Start with preferred
        order = [preferred]

        # Add others in common priority
        fallbacks = [
            BrowserType.CHROME,
            BrowserType.FIREFOX,
            BrowserType.BRAVE,
            BrowserType.EDGE,
        ]

        for browser in fallbacks:
            if browser not in order:
                order.append(browser)

        return order

    def get_best_available_browser(self, preferred: BrowserType) -> BrowserType | None:
        """Get the best available installed browser.

        Args:
            preferred: Preferred browser to try first

        Returns:
            Best available browser type, or None if none installed
        """
        fallback_order = self.get_fallback_order(preferred)

        for browser in fallback_order:
            if self.is_browser_installed(browser):
                return browser

        return None

    def browser_from_string(self, name: str) -> BrowserType:
        """Convert browser name string to BrowserType.

        Args:
            name: Browser name (case-insensitive)

        Returns:
            BrowserType enum value

        Raises:
            ValueError: If browser name is invalid
        """
        name_lower = name.lower()
        for browser_type in BrowserType:
            if browser_type.value == name_lower:
                return browser_type

        raise ValueError(f"Unknown browser: {name}")

    def browser_to_string(self, browser_type: BrowserType) -> str:
        """Convert BrowserType to string name.

        Args:
            browser_type: Browser type enum

        Returns:
            Browser name string
        """
        return browser_type.value
