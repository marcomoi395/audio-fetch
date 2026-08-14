"""Tests for CookieExtractor - browser cookie path detection and validation."""

from pathlib import Path
from unittest.mock import patch

import pytest

from desktop.cookie_extractor import BrowserType, CookieExtractor


class TestCookieExtractorInitialization:
    """Test CookieExtractor initialization."""

    def test_init_default(self):
        """Test initialization with defaults."""
        extractor = CookieExtractor()
        assert extractor.platform_system is not None
        assert extractor.home_dir is not None

    def test_init_detects_platform(self):
        """Test platform detection on initialization."""
        extractor = CookieExtractor()
        detected = extractor.platform_system
        assert detected in ["Linux", "Windows", "Darwin"]


class TestChromeCookiePathsLinux:
    """Test Chrome cookie path detection on Linux."""

    @patch("platform.system", return_value="Linux")
    @patch("pathlib.Path.home")
    def test_chrome_linux_default_path(self, mock_home, mock_platform):
        """Test Chrome default path on Linux."""
        mock_home.return_value = Path("/home/testuser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.CHROME)
        expected = Path("/home/testuser/.config/google-chrome/Default/Cookies")
        assert path == expected

    @patch("platform.system", return_value="Linux")
    @patch("pathlib.Path.home")
    def test_chrome_linux_profile_paths(self, mock_home, mock_platform):
        """Test Chrome profile-specific paths on Linux."""
        mock_home.return_value = Path("/home/testuser")
        extractor = CookieExtractor()

        paths = extractor.get_all_cookie_paths(BrowserType.CHROME)
        assert any("Default" in str(p) for p in paths)
        assert all("google-chrome" in str(p) for p in paths)


class TestChromeCookiePathsWindows:
    """Test Chrome cookie path detection on Windows."""

    @patch("platform.system", return_value="Windows")
    @patch("pathlib.Path.home")
    def test_chrome_windows_default_path(self, mock_home, mock_platform):
        """Test Chrome default path on Windows."""
        mock_home.return_value = Path("C:/Users/TestUser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.CHROME)
        expected = Path(
            "C:/Users/TestUser/AppData/Local/Google/Chrome/User Data/Default/Network/Cookies"
        )
        assert path == expected

    @patch("platform.system", return_value="Windows")
    @patch("pathlib.Path.home")
    def test_chrome_windows_profile_paths(self, mock_home, mock_platform):
        """Test Chrome profile-specific paths on Windows."""
        mock_home.return_value = Path("C:/Users/TestUser")
        extractor = CookieExtractor()

        paths = extractor.get_all_cookie_paths(BrowserType.CHROME)
        assert any("Default" in str(p) for p in paths)
        assert all("Chrome" in str(p) for p in paths)


class TestFirefoxCookiePaths:
    """Test Firefox cookie path detection."""

    @patch("platform.system", return_value="Linux")
    @patch("pathlib.Path.home")
    def test_firefox_linux_path(self, mock_home, mock_platform):
        """Test Firefox path on Linux."""
        mock_home.return_value = Path("/home/testuser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.FIREFOX)
        assert ".mozilla/firefox" in str(path)
        assert "cookies.sqlite" in str(path)

    @patch("platform.system", return_value="Windows")
    @patch("pathlib.Path.home")
    def test_firefox_windows_path(self, mock_home, mock_platform):
        """Test Firefox path on Windows."""
        mock_home.return_value = Path("C:/Users/TestUser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.FIREFOX)
        assert "Firefox" in str(path)
        assert "cookies.sqlite" in str(path)


class TestBraveCookiePaths:
    """Test Brave browser cookie path detection."""

    @patch("platform.system", return_value="Linux")
    @patch("pathlib.Path.home")
    def test_brave_linux_path(self, mock_home, mock_platform):
        """Test Brave path on Linux."""
        mock_home.return_value = Path("/home/testuser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.BRAVE)
        assert "BraveSoftware/Brave-Browser" in str(path)
        assert "Cookies" in str(path)

    @patch("platform.system", return_value="Windows")
    @patch("pathlib.Path.home")
    def test_brave_windows_path(self, mock_home, mock_platform):
        """Test Brave path on Windows."""
        mock_home.return_value = Path("C:/Users/TestUser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.BRAVE)
        assert "BraveSoftware" in str(path)
        assert "Cookies" in str(path)


class TestEdgeCookiePaths:
    """Test Edge browser cookie path detection."""

    @patch("platform.system", return_value="Linux")
    @patch("pathlib.Path.home")
    def test_edge_linux_path(self, mock_home, mock_platform):
        """Test Edge path on Linux."""
        mock_home.return_value = Path("/home/testuser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.EDGE)
        assert "microsoft-edge" in str(path)
        assert "Cookies" in str(path)

    @patch("platform.system", return_value="Windows")
    @patch("pathlib.Path.home")
    def test_edge_windows_path(self, mock_home, mock_platform):
        """Test Edge path on Windows."""
        mock_home.return_value = Path("C:/Users/TestUser")
        extractor = CookieExtractor()

        path = extractor.get_cookie_db_path(BrowserType.EDGE)
        assert "Microsoft/Edge" in str(path)
        assert "Cookies" in str(path)


class TestBrowserDetection:
    """Test browser installation detection."""

    def test_detect_browser_not_installed(self):
        """Test detection when browser is not installed."""
        extractor = CookieExtractor()

        # Use a non-existent path
        with patch.object(extractor, "get_cookie_db_path", return_value=Path("/nonexistent/path")):
            assert extractor.is_browser_installed(BrowserType.CHROME) is False

    def test_detect_browser_installed(self, tmp_path):
        """Test detection when browser is installed."""
        extractor = CookieExtractor()

        # Create a mock cookie file
        mock_cookie_file = tmp_path / "Cookies"
        mock_cookie_file.touch()

        with patch.object(extractor, "get_cookie_db_path", return_value=mock_cookie_file):
            assert extractor.is_browser_installed(BrowserType.CHROME) is True

    def test_find_installed_browsers(self, tmp_path):
        """Test finding all installed browsers."""
        extractor = CookieExtractor()

        # Mock Chrome installed, Firefox not
        def mock_installed(browser_type):
            return browser_type == BrowserType.CHROME

        with patch.object(extractor, "is_browser_installed", side_effect=mock_installed):
            browsers = extractor.find_installed_browsers()
            assert BrowserType.CHROME in browsers
            assert BrowserType.FIREFOX not in browsers


class TestBrowserFallback:
    """Test browser fallback logic."""

    def test_get_fallback_order_chrome_primary(self):
        """Test fallback order with Chrome as primary."""
        extractor = CookieExtractor()
        order = extractor.get_fallback_order(BrowserType.CHROME)

        assert order[0] == BrowserType.CHROME
        assert BrowserType.FIREFOX in order
        assert BrowserType.BRAVE in order
        assert BrowserType.EDGE in order

    def test_get_fallback_order_firefox_primary(self):
        """Test fallback order with Firefox as primary."""
        extractor = CookieExtractor()
        order = extractor.get_fallback_order(BrowserType.FIREFOX)

        assert order[0] == BrowserType.FIREFOX
        assert BrowserType.CHROME in order

    def test_get_best_available_browser(self, tmp_path):
        """Test getting best available browser."""
        extractor = CookieExtractor()

        # Mock only Firefox installed
        def mock_installed(browser_type):
            return browser_type == BrowserType.FIREFOX

        with patch.object(extractor, "is_browser_installed", side_effect=mock_installed):
            best = extractor.get_best_available_browser(BrowserType.CHROME)
            assert best == BrowserType.FIREFOX

    def test_get_best_available_browser_none_installed(self):
        """Test when no browsers are installed."""
        extractor = CookieExtractor()

        with patch.object(extractor, "is_browser_installed", return_value=False):
            best = extractor.get_best_available_browser(BrowserType.CHROME)
            assert best is None


class TestBrowserStringConversion:
    """Test browser type string conversion."""

    def test_from_string_chrome(self):
        """Test converting 'chrome' string to BrowserType."""
        extractor = CookieExtractor()
        browser = extractor.browser_from_string("chrome")
        assert browser == BrowserType.CHROME

    def test_from_string_firefox(self):
        """Test converting 'firefox' string to BrowserType."""
        extractor = CookieExtractor()
        browser = extractor.browser_from_string("firefox")
        assert browser == BrowserType.FIREFOX

    def test_from_string_case_insensitive(self):
        """Test case-insensitive conversion."""
        extractor = CookieExtractor()
        assert extractor.browser_from_string("CHROME") == BrowserType.CHROME
        assert extractor.browser_from_string("Chrome") == BrowserType.CHROME

    def test_from_string_invalid(self):
        """Test invalid browser string."""
        extractor = CookieExtractor()
        with pytest.raises(ValueError):
            extractor.browser_from_string("invalid")

    def test_to_string_chrome(self):
        """Test converting BrowserType to string."""
        extractor = CookieExtractor()
        name = extractor.browser_to_string(BrowserType.CHROME)
        assert name == "chrome"
