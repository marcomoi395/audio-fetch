"""E2E: Happy path — full user journey URL → info → download."""

import json

import pytest

from tests.e2e.page_objects import AudioFetchPage

MOCK_INFO = {
    "title": "Test Song",
    "uploader": "Test Channel",
    "duration": 180,
    "thumbnail_url": "https://example.com/thumb.jpg",
    "formats": ["mp3", "m4a", "opus", "wav", "best"],
    "qualities": {
        "0": "Cao nhất (320kbps)",
        "5": "Trung bình (192kbps)",
        "9": "Thấp (128kbps)",
    },
}


def _intercept_video_info(route):
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(MOCK_INFO),
    )


def _intercept_download(route):
    route.fulfill(
        status=200,
        content_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="Test Song.mp3"'},
        body=b"\x00" * 16,
    )


@pytest.mark.e2e
def test_happy_path_full_flow(page, live_server):
    """URL input → fetch info → video info displayed → download triggered."""
    # Intercept API calls so no real YouTube network needed
    page.route("**/api/video-info", _intercept_video_info)
    page.route("**/api/download", _intercept_download)

    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Add cookies to enable buttons (required since Task 5)
    ap.add_mock_cookies()

    # Initial state: only input-section visible
    ap.wait_for_input()

    # Enter URL and fetch info
    ap.enter_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    ap.click_fetch()

    # Video info section appears
    ap.wait_for_video_info(timeout=8000)

    assert ap.get_video_title() == "Test Song"
    assert ap.get_video_uploader() == "Test Channel"

    # Select format and quality
    ap.select_format("mp3")
    ap.select_quality("0")

    # Click download — expect browser download event
    download = ap.click_download_and_wait()
    assert download.suggested_filename == "Test Song.mp3"


@pytest.mark.e2e
def test_initial_state_only_input_visible(page, live_server):
    """On load only input-section is visible; others are hidden."""
    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    assert page.locator("#input-section").is_visible()
    assert not page.locator("#loading-section").is_visible()
    assert not page.locator("#error-section").is_visible()
    assert not page.locator("#info-section").is_visible()
