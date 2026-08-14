"""Tests to verify download_audio_with_tiers signature has no cookies parameter."""

import inspect

from services.downloader import download_audio_with_tiers


def test_download_audio_with_tiers_signature_no_cookies():
    """Verify download_audio_with_tiers function signature has no cookies parameter."""
    sig = inspect.signature(download_audio_with_tiers)
    params = list(sig.parameters.keys())

    # Should not have 'cookies' parameter
    assert "cookies" not in params, (
        "cookies parameter should be removed from download_audio_with_tiers"
    )

    # Should have these parameters
    expected_params = ["url", "quality", "format_name", "output_dir", "strategy"]
    assert params == expected_params, f"Expected {expected_params}, got {params}"
