"""3-tier yt-dlp fallback strategy for robust YouTube downloads.

Implements progressive enhancement strategy:
- Tier 1: Simple requests with basic spoofing (3 attempts)
- Tier 2: Browser cookie authentication
- Tier 3: Advanced strategies (mobile clients, oauth2, po_token)
"""

from dataclasses import dataclass
from enum import Enum


class DownloadTier(Enum):
    """Download strategy tiers in escalation order."""

    TIER_1_SIMPLE = "tier1"
    TIER_2_COOKIES = "tier2"
    TIER_3_ADVANCED = "tier3"


@dataclass
class TierConfig:
    """Configuration for a specific download attempt.

    Attributes:
        tier: The tier this config belongs to
        flags: yt-dlp command-line flags for this attempt
        description: Human-readable description of the strategy
    """

    tier: DownloadTier
    flags: list[str]
    description: str


class TierStrategy:
    """Manages 3-tier fallback strategy for yt-dlp downloads.

    Progressively escalates from simple requests to authenticated requests
    when encountering bot detection or access restrictions.
    """

    def __init__(self, browser: str = "chrome") -> None:
        """Initialize tier strategy.

        Args:
            browser: Browser to extract cookies from (chrome, firefox, edge, brave)
        """
        self.browser = browser
        self.tiers: dict[DownloadTier, list[TierConfig]] = {}
        self._define_tiers()

    def _define_tiers(self) -> None:
        """Define tier configurations for all three tiers."""
        # Tier 1: Simple requests with progressive enhancements
        self.tiers[DownloadTier.TIER_1_SIMPLE] = [
            TierConfig(
                tier=DownloadTier.TIER_1_SIMPLE,
                flags=[],
                description="Default (no special flags)",
            ),
            TierConfig(
                tier=DownloadTier.TIER_1_SIMPLE,
                flags=[
                    "--user-agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ],
                description="Browser user agent spoofing",
            ),
            TierConfig(
                tier=DownloadTier.TIER_1_SIMPLE,
                flags=[
                    "--user-agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "--sleep-requests",
                    "1",
                ],
                description="User agent + rate limiting",
            ),
        ]

        # Tier 2: Browser cookie authentication
        self.tiers[DownloadTier.TIER_2_COOKIES] = [
            TierConfig(
                tier=DownloadTier.TIER_2_COOKIES,
                flags=["--cookies-from-browser", self.browser],
                description=f"Browser cookies from {self.browser}",
            ),
            TierConfig(
                tier=DownloadTier.TIER_2_COOKIES,
                flags=[
                    "--cookies-from-browser",
                    self.browser,
                    "--user-agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ],
                description=f"Browser cookies + user agent from {self.browser}",
            ),
        ]

        # Tier 3: Advanced strategies (mobile clients, extractor args)
        self.tiers[DownloadTier.TIER_3_ADVANCED] = [
            TierConfig(
                tier=DownloadTier.TIER_3_ADVANCED,
                flags=[
                    "--extractor-args",
                    "youtube:player_client=android",
                    "--cookies-from-browser",
                    self.browser,
                ],
                description="Android client with browser cookies",
            ),
            TierConfig(
                tier=DownloadTier.TIER_3_ADVANCED,
                flags=[
                    "--extractor-args",
                    "youtube:player_client=ios",
                    "--cookies-from-browser",
                    self.browser,
                ],
                description="iOS client with browser cookies",
            ),
        ]

    def get_flags(self, tier: DownloadTier, attempt: int) -> list[str]:
        """Get yt-dlp flags for a specific tier and attempt.

        Args:
            tier: The download tier to use
            attempt: Attempt number (1-indexed)

        Returns:
            List of yt-dlp command-line flags
        """
        configs = self.tiers.get(tier, [])
        if not configs:
            return []

        # Clamp attempt to valid range (1 to len(configs))
        attempt_idx = max(0, min(attempt - 1, len(configs) - 1))
        return configs[attempt_idx].flags.copy()

    def should_escalate(self, error_code: int) -> bool:
        """Determine if we should escalate to next tier based on HTTP error code.

        Args:
            error_code: HTTP status code from failed request

        Returns:
            True if should escalate to next tier, False otherwise
        """
        # Escalate on auth/permission errors
        escalation_codes = {401, 403, 429}
        return error_code in escalation_codes

    def should_escalate_on_error(self, error_message: str) -> bool:
        """Determine if we should escalate based on error message.

        Args:
            error_message: Error message from yt-dlp

        Returns:
            True if should escalate to next tier, False otherwise
        """
        # Bot detection and auth-related error messages
        escalation_keywords = [
            "sign in",
            "unusual traffic",
            "bot",
            "captcha",
            "verify",
            "confirm your age",
        ]

        message_lower = error_message.lower()
        return any(keyword in message_lower for keyword in escalation_keywords)

    def get_tier_configs(self, tier: DownloadTier) -> list[TierConfig]:
        """Get all configurations for a specific tier.

        Args:
            tier: The download tier

        Returns:
            List of TierConfig objects for the tier
        """
        return self.tiers.get(tier, []).copy()

    def get_max_attempts(self, tier: DownloadTier) -> int:
        """Get maximum number of attempts for a tier.

        Args:
            tier: The download tier

        Returns:
            Maximum attempt count for the tier
        """
        return len(self.tiers.get(tier, []))

    def is_attempt_valid(self, tier: DownloadTier, attempt: int) -> bool:
        """Check if an attempt number is valid for a tier.

        Args:
            tier: The download tier
            attempt: Attempt number (1-indexed)

        Returns:
            True if attempt is valid (within range), False otherwise
        """
        max_attempts = self.get_max_attempts(tier)
        return 1 <= attempt <= max_attempts

    def get_next_tier(self, current_tier: DownloadTier) -> DownloadTier | None:
        """Get the next tier in escalation order.

        Args:
            current_tier: The current tier

        Returns:
            Next tier in sequence, or None if at highest tier
        """
        tier_order = [
            DownloadTier.TIER_1_SIMPLE,
            DownloadTier.TIER_2_COOKIES,
            DownloadTier.TIER_3_ADVANCED,
        ]

        try:
            current_idx = tier_order.index(current_tier)
            next_idx = current_idx + 1
            if next_idx < len(tier_order):
                return tier_order[next_idx]
        except ValueError:
            pass

        return None
