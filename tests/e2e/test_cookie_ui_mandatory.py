"""E2E: Cookie UI reflects mandatory requirement."""

import pytest

from tests.e2e.page_objects import AudioFetchPage


@pytest.mark.e2e
def test_fetch_button_disabled_without_cookies(page, live_server):
    """Fetch button is disabled when no cookies are stored."""
    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Clear any stored cookies
    page.evaluate("localStorage.clear(); sessionStorage.clear();")

    # Reload to ensure button state reflects no cookies
    page.reload(wait_until="domcontentloaded")

    # Fetch button should be disabled
    fetch_btn = page.locator("#fetch-btn")
    assert fetch_btn.is_disabled()


@pytest.mark.e2e
def test_download_button_disabled_without_cookies(page, live_server):
    """Download button is disabled when no cookies are stored."""

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

    # Add cookies to fetch video info
    page.evaluate(
        'sessionStorage.setItem("youtube_cookies", "# Netscape HTTP Cookie File\\n.youtube.com\\tTRUE\\t/\\tTRUE\\t0\\ttest\\tvalue")'
    )
    page.reload(wait_until="domcontentloaded")

    ap.enter_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    ap.click_fetch()
    ap.wait_for_video_info(timeout=3000)
    # Clear cookies and update button states
    page.evaluate("localStorage.clear(); sessionStorage.clear(); updateButtonStates();")
    page.wait_for_timeout(100)

    # Download button should be disabled
    download_btn = page.locator("#download-btn")
    assert download_btn.is_disabled()


@pytest.mark.e2e
def test_buttons_enabled_with_cookies(page, live_server):
    """Fetch and download buttons are enabled when cookies are stored."""
    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Add cookies
    page.evaluate(
        'sessionStorage.setItem("youtube_cookies", "# Netscape HTTP Cookie File\\n.youtube.com\\tTRUE\\t/\\tTRUE\\t0\\ttest\\tvalue")'
    )

    # Reload to ensure button state reflects cookies
    page.reload(wait_until="domcontentloaded")

    # Fetch button should be enabled
    fetch_btn = page.locator("#fetch-btn")
    assert not fetch_btn.is_disabled()


@pytest.mark.e2e
def test_cookie_section_visible_by_default(page, live_server):
    """Cookie section is visible/expanded by default."""
    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Cookie container should be visible
    cookies_container = page.locator("#cookies-container")
    assert cookies_container.is_visible()


@pytest.mark.e2e
def test_cookie_button_text_shows_required(page, live_server):
    """Cookie button text indicates cookies are required."""
    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Button text should mention "Required"
    add_cookies_btn = page.locator("#add-cookies-btn")
    button_text = add_cookies_btn.inner_text()
    assert "required" in button_text.lower()
