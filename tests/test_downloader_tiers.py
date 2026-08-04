"""Tests for downloader tier strategy integration."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from desktop.tier_strategy import DownloadTier, TierStrategy
from services.downloader import download_audio_with_tiers


class TestDownloadWithTiers:
    """Test download_audio_with_tiers with tier fallback."""

    @pytest.mark.asyncio
    async def test_tier1_success_first_attempt(self, tmp_path):
        """Test successful download on first Tier 1 attempt."""
        strategy = TierStrategy(tier2_enabled=True, tier3_enabled=False)

        with patch("services.downloader._download_sync") as mock_download:
            mock_download.return_value = str(tmp_path / "audio.m4a")

            result = await download_audio_with_tiers(
                url="https://youtube.com/watch?v=test",
                quality="5",
                format_name="m4a",
                output_dir=str(tmp_path),
                cookies="",
                strategy=strategy,
            )

            assert result["success"] is True
            assert result["tier_used"] == DownloadTier.TIER_1_SIMPLE
            assert result["attempts"] == 1
            assert mock_download.call_count == 1

    @pytest.mark.asyncio
    async def test_tier1_escalates_on_403(self, tmp_path):
        """Test Tier 1 escalation on 403 error."""
        strategy = TierStrategy(tier2_enabled=True, tier3_enabled=False)

        with patch("services.downloader._download_sync") as mock_download:
            # First two attempts fail with 403
            mock_download.side_effect = [
                Exception("HTTP Error 403: Forbidden"),
                Exception("HTTP Error 403: Forbidden"),
                str(tmp_path / "audio.m4a"),  # Third succeeds
            ]

            result = await download_audio_with_tiers(
                url="https://youtube.com/watch?v=test",
                quality="5",
                format_name="m4a",
                output_dir=str(tmp_path),
                cookies="",
                strategy=strategy,
            )

            assert result["success"] is True
            assert result["tier_used"] == DownloadTier.TIER_1_SIMPLE
            assert result["attempts"] == 3
            assert mock_download.call_count == 3

    @pytest.mark.asyncio
    async def test_tier1_all_fail_escalates_to_tier2(self, tmp_path, caplog):
        """Test escalation to Tier 2 after all Tier 1 attempts fail."""
        strategy = TierStrategy(tier2_enabled=True, tier3_enabled=False)

        with patch("services.downloader._download_sync") as mock_download:
            with patch("services.downloader.CookieExtractor") as mock_extractor:
                # Configure mock extractor
                mock_instance = mock_extractor.return_value
                mock_instance.find_installed_browsers.return_value = [MagicMock(value="chrome")]
                mock_instance.browser_to_string.return_value = "chrome"

                # Tier 1: all 3 attempts fail with 403
                # Tier 2: chrome attempt succeeds
                mock_download.side_effect = [
                    Exception("HTTP Error 403: Forbidden"),
                    Exception("HTTP Error 403: Forbidden"),
                    Exception("HTTP Error 403: Forbidden"),
                    str(tmp_path / "audio.m4a"),  # Tier 2 Chrome succeeds
                ]

                with caplog.at_level(logging.WARNING):
                    result = await download_audio_with_tiers(
                        url="https://youtube.com/watch?v=test",
                        quality="5",
                        format_name="m4a",
                        output_dir=str(tmp_path),
                        cookies="",
                        strategy=strategy,
                    )

                assert result["success"] is True
                assert result["tier_used"] == DownloadTier.TIER_2_COOKIES
                assert "Escalating to Tier 2" in caplog.text
                assert mock_download.call_count == 4

    @pytest.mark.asyncio
    async def test_tier2_tries_multiple_browsers(self, tmp_path):
        """Test Tier 2 tries multiple browsers on failure."""
        strategy = TierStrategy(tier2_enabled=True, tier3_enabled=False)

        with patch("services.downloader._download_sync") as mock_download:
            with patch("services.downloader.CookieExtractor") as mock_extractor:
                # Configure mock to return multiple browsers
                mock_instance = mock_extractor.return_value
                mock_instance.find_installed_browsers.return_value = [
                    MagicMock(value="chrome"),
                    MagicMock(value="firefox"),
                ]
                mock_instance.browser_to_string.side_effect = ["chrome", "firefox"]

                # Tier 1: all fail
                # Tier 2: chrome fails, firefox succeeds
                mock_download.side_effect = [
                    Exception("HTTP Error 403"),
                    Exception("HTTP Error 403"),
                    Exception("HTTP Error 403"),
                    Exception("HTTP Error 403"),  # Chrome fails
                    str(tmp_path / "audio.m4a"),  # Firefox succeeds
                ]

                result = await download_audio_with_tiers(
                    url="https://youtube.com/watch?v=test",
                    quality="5",
                    format_name="m4a",
                    output_dir=str(tmp_path),
                    cookies="",
                    strategy=strategy,
                )

                assert result["success"] is True
                assert result["tier_used"] == DownloadTier.TIER_2_COOKIES
                assert result["browser_used"] == "firefox"

    @pytest.mark.asyncio
    async def test_tier2_disabled_skips_to_tier3(self, tmp_path, caplog):
        """Test skipping Tier 2 when disabled."""
        strategy = TierStrategy(tier2_enabled=False, tier3_enabled=True)

        with patch("services.downloader._download_sync") as mock_download:
            # Tier 1: all fail
            # Tier 3: succeeds
            mock_download.side_effect = [
                Exception("HTTP Error 403"),
                Exception("HTTP Error 403"),
                Exception("HTTP Error 403"),
                str(tmp_path / "audio.m4a"),  # Tier 3 succeeds
            ]

            with caplog.at_level(logging.WARNING):
                result = await download_audio_with_tiers(
                    url="https://youtube.com/watch?v=test",
                    quality="5",
                    format_name="m4a",
                    output_dir=str(tmp_path),
                    cookies="",
                    strategy=strategy,
                )

            assert result["success"] is True
            assert result["tier_used"] == DownloadTier.TIER_3_ADVANCED
            assert "Tier 2 disabled, escalating to Tier 3" in caplog.text

    @pytest.mark.asyncio
    async def test_all_tiers_fail_returns_error(self, tmp_path):
        """Test all tiers failing returns error result."""
        strategy = TierStrategy(tier2_enabled=True, tier3_enabled=True)

        with patch("services.downloader._download_sync") as mock_download:
            with patch("services.downloader.CookieExtractor") as mock_extractor:
                mock_instance = mock_extractor.return_value
                mock_instance.find_installed_browsers.return_value = [MagicMock(value="chrome")]
                mock_instance.browser_to_string.return_value = "chrome"

                # All attempts fail
                mock_download.side_effect = Exception("HTTP Error 403")

                result = await download_audio_with_tiers(
                    url="https://youtube.com/watch?v=test",
                    quality="5",
                    format_name="m4a",
                    output_dir=str(tmp_path),
                    cookies="",
                    strategy=strategy,
                )

                assert result["success"] is False
                assert "error" in result
                assert result["tier_used"] is None

    @pytest.mark.asyncio
    async def test_tier1_bot_detection_escalates(self, tmp_path):
        """Test escalation on bot detection error."""
        strategy = TierStrategy(tier2_enabled=True, tier3_enabled=False)

        with patch("services.downloader._download_sync") as mock_download:
            with patch("services.downloader.CookieExtractor") as mock_extractor:
                mock_instance = mock_extractor.return_value
                mock_instance.find_installed_browsers.return_value = [MagicMock(value="chrome")]
                mock_instance.browser_to_string.return_value = "chrome"

                # Tier 1: bot detection error
                # Tier 2: succeeds
                mock_download.side_effect = [
                    Exception("Sign in to confirm you're not a bot"),
                    str(tmp_path / "audio.m4a"),
                ]

                result = await download_audio_with_tiers(
                    url="https://youtube.com/watch?v=test",
                    quality="5",
                    format_name="m4a",
                    output_dir=str(tmp_path),
                    cookies="",
                    strategy=strategy,
                )

                assert result["success"] is True
                assert result["tier_used"] == DownloadTier.TIER_2_COOKIES

    @pytest.mark.asyncio
    async def test_tier2_no_browsers_skips_to_tier3(self, tmp_path, caplog):
        """Test Tier 2 skipped when no browsers installed."""
        strategy = TierStrategy(tier2_enabled=True, tier3_enabled=True)

        with patch("services.downloader._download_sync") as mock_download:
            with patch("services.downloader.CookieExtractor") as mock_extractor:
                mock_instance = mock_extractor.return_value
                mock_instance.find_installed_browsers.return_value = []

                # Tier 1: fails
                # Tier 3: succeeds (Tier 2 skipped due to no browsers)
                mock_download.side_effect = [
                    Exception("HTTP Error 403"),
                    Exception("HTTP Error 403"),
                    Exception("HTTP Error 403"),
                    str(tmp_path / "audio.m4a"),
                ]

                with caplog.at_level(logging.WARNING):
                    result = await download_audio_with_tiers(
                        url="https://youtube.com/watch?v=test",
                        quality="5",
                        format_name="m4a",
                        output_dir=str(tmp_path),
                        cookies="",
                        strategy=strategy,
                    )

                assert result["success"] is True
                assert result["tier_used"] == DownloadTier.TIER_3_ADVANCED
                assert "No browsers found" in caplog.text
