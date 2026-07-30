"""E2E: Cookie validation before API calls."""

import pytest

from tests.e2e.page_objects import AudioFetchPage


@pytest.mark.e2e
def test_fetch_without_cookies_shows_error(page, live_server):
    """Fetch button without cookies shows error message (programmatic validation)."""
    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Clear any stored cookies
    page.evaluate("localStorage.clear(); sessionStorage.clear();")

    # Call handleFetchInfo directly to test programmatic validation
    ap.enter_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    page.evaluate("handleFetchInfo()")

    # Should show error immediately (no API call)
    ap.wait_for_error(timeout=2000)
    error_msg = ap.get_error_message()
    assert "cookies required" in error_msg.lower()
    assert "please add cookies" in error_msg.lower()


@pytest.mark.e2e
def test_download_without_cookies_shows_error(page, live_server):
    """Download button without cookies shows error message (programmatic validation)."""

    # Mock successful video-info response
    def mock_video_info(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"title": "Test Video", "uploader": "Test Channel", '
            '"duration": 180, "thumbnail_url": "/static/placeholder.png"}',
        )

    page.route("**/api/video-info", mock_video_info)

    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Add mock cookies for initial fetch and enable buttons
    page.evaluate(
        'sessionStorage.setItem("youtube_cookies", "# Netscape HTTP Cookie File\\n.youtube.com\\tTRUE\\t/\\tTRUE\\t0\\ttest\\tvalue"); updateButtonStates();'
    )

    ap.enter_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    page.click("#fetch-btn", force=True)
    ap.wait_for_video_info(timeout=3000)

    # Clear cookies
    page.evaluate("localStorage.clear(); sessionStorage.clear();")

    # Try to download without cookies (force click to bypass disabled state)
    page.click("#download-btn", force=True)

    # Should show error immediately (no API call)
    ap.wait_for_error(timeout=2000)
    error_msg = ap.get_error_message()
    assert "cookies required" in error_msg.lower()
    assert "please add cookies" in error_msg.lower()


@pytest.mark.e2e
def test_fetch_with_cookies_proceeds(page, live_server):
    """Fetch with cookies calls the API."""

    # Mock successful video-info response
    def mock_video_info(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"title": "Test Video", "uploader": "Test Channel", '
            '"duration": 180, "thumbnail_url": "/static/placeholder.png"}',
        )

    page.route("**/api/video-info", mock_video_info)

    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Add cookies and enable buttons
    page.evaluate(
        'sessionStorage.setItem("youtube_cookies", "# Netscape HTTP Cookie File\\n.youtube.com\\tTRUE\\t/\\tTRUE\\t0\\ttest\\tvalue"); updateButtonStates();'
    )

    ap.enter_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    ap.click_fetch()

    # Should show video info (API call succeeded)
    ap.wait_for_video_info(timeout=3000)
    assert "Test Video" in ap.get_video_title()
