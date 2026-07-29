"""Smoke test: verify E2E infrastructure works."""
import pytest


def test_homepage_loads(page, live_server):
    """Homepage must return 200 and render the URL input."""
    page.goto(live_server)
    assert page.locator("#youtube-url").is_visible()
    assert page.locator("#fetch-btn").is_visible()
    assert page.locator("#input-section").is_visible()
    # Other sections hidden by default
    assert not page.locator("#loading-section").is_visible()
    assert not page.locator("#error-section").is_visible()
    assert not page.locator("#info-section").is_visible()
