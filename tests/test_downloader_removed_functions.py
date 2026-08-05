"""Tests to verify cookie-related helper functions are removed."""


def test_clean_cookie_content_function_removed():
    """Verify _clean_cookie_content function no longer exists."""
    from services import downloader

    assert not hasattr(downloader, "_clean_cookie_content"), (
        "_clean_cookie_content function should be removed"
    )


def test_youtube_cookies_context_function_removed():
    """Verify youtube_cookies_context function no longer exists."""
    from services import downloader

    assert not hasattr(downloader, "youtube_cookies_context"), (
        "youtube_cookies_context function should be removed"
    )
