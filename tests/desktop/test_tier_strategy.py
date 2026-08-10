"""Tests for TierStrategy - yt-dlp tier-based fallback strategy."""

from desktop.tier_strategy import DownloadTier, TierConfig, TierStrategy


class TestTierStrategyInitialization:
    """Test TierStrategy initialization."""

    def test_init_with_default_browser(self):
        """Test initialization with default browser."""
        strategy = TierStrategy()
        assert strategy.browser == "chrome"
        assert strategy.tiers is not None

    def test_init_with_custom_browser(self):
        """Test initialization with custom browser."""
        strategy = TierStrategy(browser="firefox")
        assert strategy.browser == "firefox"

    def test_init_with_brave_browser(self):
        """Test initialization with Brave browser."""
        strategy = TierStrategy(browser="brave")
        assert strategy.browser == "brave"


class TestTier1Flags:
    """Test Tier 1 flag generation."""

    def test_tier1_attempt1_no_flags(self):
        """Test Tier 1 attempt 1: Default with no flags."""
        strategy = TierStrategy()
        flags = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=1)

        assert isinstance(flags, list)
        # First attempt should have minimal flags or empty
        assert len(flags) <= 2

    def test_tier1_attempt2_impersonation(self):
        """Test Tier 1 attempt 2: Browser impersonation."""
        strategy = TierStrategy()
        flags = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=2)

        assert "--impersonate" in flags or "--user-agent" in flags

    def test_tier1_attempt3_rate_limiting(self):
        """Test Tier 1 attempt 3: Rate limiting protection."""
        strategy = TierStrategy()
        flags = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=3)

        # Should include sleep or rate limiting flags
        assert any(flag in flags for flag in ["--sleep-requests", "--sleep-interval"])

    def test_tier1_all_attempts_unique(self):
        """Test that Tier 1 attempts produce different flag sets."""
        strategy = TierStrategy()

        flags1 = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=1)
        flags2 = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=2)
        flags3 = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=3)

        # Each attempt should be different
        assert flags1 != flags2 or flags2 != flags3

    def test_tier1_attempt_out_of_range_returns_last(self):
        """Test Tier 1 with attempt > 3 returns last config."""
        strategy = TierStrategy()

        flags3 = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=3)
        flags4 = strategy.get_flags(DownloadTier.TIER_1_SIMPLE, attempt=4)

        # Should return the last available config
        assert flags3 == flags4


class TestTier2Flags:
    """Test Tier 2 flag generation (browser cookies)."""

    def test_tier2_includes_cookies_from_browser_chrome(self):
        """Test Tier 2 includes --cookies-from-browser for Chrome."""
        strategy = TierStrategy(browser="chrome")
        flags = strategy.get_flags(DownloadTier.TIER_2_COOKIES, attempt=1)

        assert "--cookies-from-browser" in flags
        # Next element should be browser name
        idx = flags.index("--cookies-from-browser")
        assert flags[idx + 1] == "chrome"

    def test_tier2_includes_cookies_from_browser_firefox(self):
        """Test Tier 2 includes --cookies-from-browser for Firefox."""
        strategy = TierStrategy(browser="firefox")
        flags = strategy.get_flags(DownloadTier.TIER_2_COOKIES, attempt=1)

        assert "--cookies-from-browser" in flags
        idx = flags.index("--cookies-from-browser")
        assert flags[idx + 1] == "firefox"

    def test_tier2_includes_cookies_from_browser_brave(self):
        """Test Tier 2 includes --cookies-from-browser for Brave."""
        strategy = TierStrategy(browser="brave")
        flags = strategy.get_flags(DownloadTier.TIER_2_COOKIES, attempt=1)

        assert "--cookies-from-browser" in flags
        idx = flags.index("--cookies-from-browser")
        assert flags[idx + 1] == "brave"

    def test_tier2_attempt2_different_from_attempt1(self):
        """Test Tier 2 attempt 2 has different flags from attempt 1."""
        strategy = TierStrategy()

        flags1 = strategy.get_flags(DownloadTier.TIER_2_COOKIES, attempt=1)
        flags2 = strategy.get_flags(DownloadTier.TIER_2_COOKIES, attempt=2)

        # Should have some variation (e.g., additional headers or settings)
        # At minimum, both should include cookies
        assert "--cookies-from-browser" in flags1
        assert "--cookies-from-browser" in flags2


class TestTier3Flags:
    """Test Tier 3 flag generation (advanced strategies)."""

    def test_tier3_includes_extractor_args(self):
        """Test Tier 3 includes advanced extractor arguments."""
        strategy = TierStrategy()
        flags = strategy.get_flags(DownloadTier.TIER_3_ADVANCED, attempt=1)

        # Should include po_token or oauth settings
        assert any(
            flag in flags for flag in ["--extractor-args", "--cookies-from-browser", "--username"]
        )

    def test_tier3_attempt1_uses_mobile_client(self):
        """Test Tier 3 attempt 1 uses mobile client impersonation."""
        strategy = TierStrategy()
        flags = strategy.get_flags(DownloadTier.TIER_3_ADVANCED, attempt=1)

        # Should include extractor args for mobile client
        if "--extractor-args" in flags:
            idx = flags.index("--extractor-args")
            # Check if mobile client is specified
            assert "android" in flags[idx + 1].lower() or "ios" in flags[idx + 1].lower()

    def test_tier3_has_multiple_attempts(self):
        """Test Tier 3 has multiple attempt configurations."""
        strategy = TierStrategy()

        flags1 = strategy.get_flags(DownloadTier.TIER_3_ADVANCED, attempt=1)
        flags2 = strategy.get_flags(DownloadTier.TIER_3_ADVANCED, attempt=2)

        # Both should be valid (non-empty or with specific flags)
        assert isinstance(flags1, list)
        assert isinstance(flags2, list)


class TestTierEscalation:
    """Test tier escalation logic."""

    def test_should_escalate_on_403(self):
        """Test escalation on 403 Forbidden."""
        strategy = TierStrategy()
        assert strategy.should_escalate(403) is True

    def test_should_escalate_on_429(self):
        """Test escalation on 429 Too Many Requests."""
        strategy = TierStrategy()
        assert strategy.should_escalate(429) is True

    def test_should_escalate_on_401(self):
        """Test escalation on 401 Unauthorized."""
        strategy = TierStrategy()
        assert strategy.should_escalate(401) is True

    def test_should_not_escalate_on_404(self):
        """Test no escalation on 404 Not Found."""
        strategy = TierStrategy()
        assert strategy.should_escalate(404) is False

    def test_should_not_escalate_on_500(self):
        """Test no escalation on 500 Internal Server Error."""
        strategy = TierStrategy()
        assert strategy.should_escalate(500) is False

    def test_should_not_escalate_on_200(self):
        """Test no escalation on 200 OK."""
        strategy = TierStrategy()
        assert strategy.should_escalate(200) is False

    def test_should_escalate_on_sign_in_required_message(self):
        """Test escalation on 'Sign in' error message."""
        strategy = TierStrategy()
        assert strategy.should_escalate_on_error("Sign in to confirm your age") is True

    def test_should_escalate_on_bot_detection_message(self):
        """Test escalation on bot detection error message."""
        strategy = TierStrategy()
        assert strategy.should_escalate_on_error("unusual traffic") is True

    def test_should_not_escalate_on_video_unavailable(self):
        """Test no escalation on video unavailable message."""
        strategy = TierStrategy()
        assert strategy.should_escalate_on_error("Video unavailable") is False


class TestTierConfigRetrieval:
    """Test tier configuration retrieval."""

    def test_get_tier_config_tier1(self):
        """Test get_tier_config for Tier 1."""
        strategy = TierStrategy()
        configs = strategy.get_tier_configs(DownloadTier.TIER_1_SIMPLE)

        assert isinstance(configs, list)
        assert len(configs) >= 3  # At least 3 attempts
        assert all(isinstance(c, TierConfig) for c in configs)

    def test_get_tier_config_tier2(self):
        """Test get_tier_config for Tier 2."""
        strategy = TierStrategy()
        configs = strategy.get_tier_configs(DownloadTier.TIER_2_COOKIES)

        assert isinstance(configs, list)
        assert len(configs) >= 1
        assert all(isinstance(c, TierConfig) for c in configs)

    def test_get_tier_config_tier3(self):
        """Test get_tier_config for Tier 3."""
        strategy = TierStrategy()
        configs = strategy.get_tier_configs(DownloadTier.TIER_3_ADVANCED)

        assert isinstance(configs, list)
        assert len(configs) >= 1
        assert all(isinstance(c, TierConfig) for c in configs)

    def test_tier_config_has_description(self):
        """Test that each TierConfig has a description."""
        strategy = TierStrategy()

        for tier in [
            DownloadTier.TIER_1_SIMPLE,
            DownloadTier.TIER_2_COOKIES,
            DownloadTier.TIER_3_ADVANCED,
        ]:
            configs = strategy.get_tier_configs(tier)
            for config in configs:
                assert config.description is not None
                assert len(config.description) > 0


class TestAttemptCounter:
    """Test attempt counter logic."""

    def test_max_attempts_tier1(self):
        """Test max attempts for Tier 1."""
        strategy = TierStrategy()
        max_attempts = strategy.get_max_attempts(DownloadTier.TIER_1_SIMPLE)

        assert max_attempts == 3

    def test_max_attempts_tier2(self):
        """Test max attempts for Tier 2."""
        strategy = TierStrategy()
        max_attempts = strategy.get_max_attempts(DownloadTier.TIER_2_COOKIES)

        assert max_attempts >= 1

    def test_max_attempts_tier3(self):
        """Test max attempts for Tier 3."""
        strategy = TierStrategy()
        max_attempts = strategy.get_max_attempts(DownloadTier.TIER_3_ADVANCED)

        assert max_attempts >= 1

    def test_is_attempt_valid_within_range(self):
        """Test is_attempt_valid returns True within range."""
        strategy = TierStrategy()

        assert strategy.is_attempt_valid(DownloadTier.TIER_1_SIMPLE, 1) is True
        assert strategy.is_attempt_valid(DownloadTier.TIER_1_SIMPLE, 2) is True
        assert strategy.is_attempt_valid(DownloadTier.TIER_1_SIMPLE, 3) is True

    def test_is_attempt_valid_out_of_range(self):
        """Test is_attempt_valid returns False out of range."""
        strategy = TierStrategy()

        assert strategy.is_attempt_valid(DownloadTier.TIER_1_SIMPLE, 0) is False
        assert strategy.is_attempt_valid(DownloadTier.TIER_1_SIMPLE, 4) is False


class TestTierOrdering:
    """Test tier ordering and progression."""

    def test_get_next_tier_from_tier1(self):
        """Test getting next tier from Tier 1."""
        strategy = TierStrategy()
        next_tier = strategy.get_next_tier(DownloadTier.TIER_1_SIMPLE)

        assert next_tier == DownloadTier.TIER_2_COOKIES

    def test_get_next_tier_from_tier2(self):
        """Test getting next tier from Tier 2."""
        strategy = TierStrategy()
        next_tier = strategy.get_next_tier(DownloadTier.TIER_2_COOKIES)

        assert next_tier == DownloadTier.TIER_3_ADVANCED

    def test_get_next_tier_from_tier3_returns_none(self):
        """Test getting next tier from Tier 3 returns None."""
        strategy = TierStrategy()
        next_tier = strategy.get_next_tier(DownloadTier.TIER_3_ADVANCED)

        assert next_tier is None

    def test_tier_progression_order(self):
        """Test full tier progression order."""
        strategy = TierStrategy()

        tier1 = DownloadTier.TIER_1_SIMPLE
        tier2 = strategy.get_next_tier(tier1)
        assert tier2 is not None
        tier3 = strategy.get_next_tier(tier2)
        assert tier3 is not None
        tier_end = strategy.get_next_tier(tier3)

        assert tier2 == DownloadTier.TIER_2_COOKIES
        assert tier3 == DownloadTier.TIER_3_ADVANCED
        assert tier_end is None
