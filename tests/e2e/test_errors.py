"""E2E: Error handling and queue busy flows."""

import json

from tests.e2e.page_objects import AudioFetchPage


def _error_route(message: str, status: int = 400):
    def handler(route):
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps({"detail": message}),
        )

    return handler


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


def test_invalid_url_shows_error_section(page, live_server):
    """Server 400 on video-info → error-section with message appears."""
    page.route("**/api/video-info", _error_route("Video unavailable"))

    ap = AudioFetchPage(page, live_server)
    ap.navigate()
    ap.enter_url("https://youtube.com/watch?v=invalid")
    ap.click_fetch()

    ap.wait_for_error(timeout=6000)
    assert "Video unavailable" in ap.get_error_message()


def test_retry_returns_to_input_section(page, live_server):
    """'Retry' button returns to input-section (URL field may be cleared)."""
    page.route("**/api/video-info", _error_route("Some error"))

    ap = AudioFetchPage(page, live_server)
    ap.navigate()
    ap.enter_url("https://youtube.com/watch?v=test")
    ap.click_fetch()

    ap.wait_for_error(timeout=6000)
    ap.click_retry()

    # Must return to input-section; error section must disappear
    ap.wait_for_input()
    assert not page.locator("#error-section").is_visible()


def test_new_url_clears_input(page, live_server):
    """'New URL' button from info-section clears the input field."""
    mock_info = {
        "title": "T",
        "uploader": "U",
        "duration": 60,
        "thumbnail_url": "https://example.com/t.jpg",
        "formats": ["mp3"],
        "qualities": {"0": "Best"},
    }
    page.route(
        "**/api/video-info",
        lambda r: r.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(mock_info),
        ),
    )

    ap = AudioFetchPage(page, live_server)
    ap.navigate()
    ap.enter_url("https://youtube.com/watch?v=abc")
    ap.click_fetch()
    ap.wait_for_video_info(timeout=6000)

    ap.click_new_url()
    ap.wait_for_input()
    assert ap.get_url_input_value() == ""


# ---------------------------------------------------------------------------
# Queue busy test
# ---------------------------------------------------------------------------


def test_queue_busy_shows_error_on_download(page, live_server):
    """503 from /api/download → error-section with 'in progress' message."""
    mock_info = {
        "title": "T",
        "uploader": "U",
        "duration": 60,
        "thumbnail_url": "https://example.com/t.jpg",
        "formats": ["mp3"],
        "qualities": {"0": "Best"},
    }
    page.route(
        "**/api/video-info",
        lambda r: r.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(mock_info),
        ),
    )
    page.route(
        "**/api/download",
        _error_route("Another download is in progress. Please wait.", status=503),
    )

    ap = AudioFetchPage(page, live_server)
    ap.navigate()
    ap.enter_url("https://youtube.com/watch?v=test")
    ap.click_fetch()
    ap.wait_for_video_info(timeout=6000)
    ap.click_download()

    ap.wait_for_error(timeout=6000)
    assert "in progress" in ap.get_error_message().lower()
