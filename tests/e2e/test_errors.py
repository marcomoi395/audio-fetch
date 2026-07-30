"""E2E: Error handling and queue busy flows."""

import json

import pytest

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


@pytest.mark.e2e
def test_invalid_url_shows_error_section(page, live_server):
    """Server 400 on video-info → error-section with message appears."""
    page.route("**/api/video-info", _error_route("Video unavailable"))

    ap = AudioFetchPage(page, live_server)
    ap.navigate()
    ap.add_mock_cookies()
    ap.enter_url("https://youtube.com/watch?v=invalid")
    ap.click_fetch()

    ap.wait_for_error(timeout=6000)
    assert "Video unavailable" in ap.get_error_message()


@pytest.mark.e2e
def test_retry_returns_to_input_section(page, live_server):
    """'Retry' button returns to input-section (URL field may be cleared)."""
    page.route("**/api/video-info", _error_route("Video unavailable"))

    ap = AudioFetchPage(page, live_server)
    ap.navigate()
    ap.add_mock_cookies()
    ap.enter_url("https://youtube.com/watch?v=invalid")
    ap.click_fetch()

    ap.wait_for_error(timeout=6000)
    ap.click_retry()

    # Returns to input-section
    ap.wait_for_input()
    assert not page.locator("#error-section").is_visible()


@pytest.mark.e2e
def test_new_url_clears_input(page, live_server):
    """'New URL' button from info-section clears the input field."""

    def _intercept_video_info(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "title": "Test Video",
                    "uploader": "Test Channel",
                    "duration": 100,
                    "thumbnail_url": "https://example.com/thumb.jpg",
                    "formats": ["mp3", "m4a"],
                    "qualities": {"0": "High", "5": "Medium"},
                }
            ),
        )

    page.route("**/api/video-info", _intercept_video_info)

    ap = AudioFetchPage(page, live_server)
    ap.navigate()
    ap.add_mock_cookies()
    ap.enter_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    ap.click_fetch()
    ap.wait_for_video_info(timeout=6000)

    ap.click_new_url()
    ap.wait_for_input()
    assert ap.get_url_input_value() == ""


# ---------------------------------------------------------------------------
# Queue busy test
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_queue_busy_shows_error_on_download(page, live_server):
    """503 from /api/download → error-section with 'in progress' message."""

    def _intercept_video_info(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "title": "Test Video",
                    "uploader": "Test Channel",
                    "duration": 100,
                    "thumbnail_url": "https://example.com/thumb.jpg",
                    "formats": ["mp3", "m4a"],
                    "qualities": {"0": "High"},
                }
            ),
        )

    def _download_busy(route):
        route.fulfill(
            status=503,
            content_type="application/json",
            body=json.dumps({"detail": "Download in progress. Please wait."}),
        )

    page.route("**/api/video-info", _intercept_video_info)
    page.route("**/api/download", _download_busy)

    ap = AudioFetchPage(page, live_server)
    ap.navigate()

    # Add cookies to enable buttons (required since Task 5)
    ap.add_mock_cookies()

    ap.enter_url("https://youtube.com/watch?v=test")
    ap.click_fetch()
    ap.wait_for_video_info(timeout=6000)
    ap.select_format("mp3")
    ap.select_quality("0")

    with page.expect_response("**/api/download") as response_info:
        page.locator("#download-btn").click()

    response_info.value.finished()

    ap.wait_for_error(timeout=6000)
    assert "in progress" in ap.get_error_message().lower()
