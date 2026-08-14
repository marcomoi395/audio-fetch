"""Tests to verify download_audio signature has no cookies parameter."""

import inspect

from services.downloader import download_audio


def test_download_audio_signature_no_cookies():
    """Verify download_audio function signature has no cookies parameter."""
    sig = inspect.signature(download_audio)
    params = list(sig.parameters.keys())

    # Should not have 'cookies' parameter
    assert "cookies" not in params, "cookies parameter should be removed from download_audio"

    # Should have these parameters
    expected_params = [
        "url",
        "audio_format",
        "quality",
        "output_dir",
        "cookies_from_browser",
        "player_client",
    ]
    assert params == expected_params, f"Expected {expected_params}, got {params}"
