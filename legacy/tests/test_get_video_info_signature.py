"""Tests to verify get_video_info signature has no cookies parameter."""

import inspect

from services.downloader import get_video_info


def test_get_video_info_signature_no_cookies():
    """Verify get_video_info function signature has no cookies parameter."""
    sig = inspect.signature(get_video_info)
    params = list(sig.parameters.keys())

    # Should only have 'url' parameter
    assert params == ["url"], f"Expected ['url'], got {params}"
    assert "cookies" not in params, "cookies parameter should be removed from get_video_info"
