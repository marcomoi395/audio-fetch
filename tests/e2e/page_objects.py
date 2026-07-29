"""Page Object for the Audio Fetch single-page app."""
from playwright.sync_api import Download, Page, expect


class AudioFetchPage:
    """Wraps all interactions with index.html."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self):
        self.page.goto(self.base_url, wait_until="domcontentloaded")

    # ------------------------------------------------------------------
    # Input section
    # ------------------------------------------------------------------

    def enter_url(self, url: str):
        self.page.fill("#youtube-url", url)

    def click_fetch(self):
        self.page.click("#fetch-btn")

    # ------------------------------------------------------------------
    # Info section
    # ------------------------------------------------------------------

    def select_format(self, fmt: str):
        """Select a format option by value (mp3, m4a, opus, wav, best)."""
        self.page.select_option("#format-select", value=fmt)

    def select_quality(self, quality: str):
        """Select quality by value (0, 5, 9)."""
        self.page.select_option("#quality-select", value=quality)

    def click_download(self):
        self.page.click("#download-btn")

    def click_new_url(self):
        self.page.click("#new-url-btn")

    # ------------------------------------------------------------------
    # Error section
    # ------------------------------------------------------------------

    def click_retry(self):
        self.page.click("#retry-btn")

    # ------------------------------------------------------------------
    # Visibility helpers
    # ------------------------------------------------------------------

    def wait_for_input(self):
        expect(self.page.locator("#input-section")).to_be_visible()

    def wait_for_loading(self):
        expect(self.page.locator("#loading-section")).to_be_visible()

    def wait_for_video_info(self, timeout: int = 5000):
        expect(self.page.locator("#info-section")).to_be_visible(timeout=timeout)

    def wait_for_error(self, timeout: int = 5000):
        expect(self.page.locator("#error-section")).to_be_visible(timeout=timeout)

    # ------------------------------------------------------------------
    # Data readers
    # ------------------------------------------------------------------

    def get_video_title(self) -> str:
        return self.page.inner_text("#video-title")

    def get_video_uploader(self) -> str:
        return self.page.inner_text("#video-uploader")

    def get_error_message(self) -> str:
        return self.page.inner_text("#error-message")

    def get_url_input_value(self) -> str:
        return self.page.input_value("#youtube-url")

    # ------------------------------------------------------------------
    # Download trigger helper
    # ------------------------------------------------------------------

    def click_download_and_wait(self) -> Download:
        """Click download and return the Download object."""
        with self.page.expect_download() as dl_info:
            self.click_download()
        return dl_info.value
