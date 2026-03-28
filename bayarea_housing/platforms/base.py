"""Base scraper class with shared browser management."""

from __future__ import annotations

import random
import time
from typing import Any, TypedDict

from patchright.sync_api import sync_playwright, BrowserContext, Playwright


class Listing(TypedDict, total=False):
    """Standardized listing dict."""
    source: str
    title: str
    price: int | None
    price_raw: str
    location: str
    url: str
    area: str
    category: str
    author: str
    date: str


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]


class BaseScraper:
    """Base class providing browser context and rate limiting."""

    def __init__(
        self,
        context: BrowserContext | None = None,
        rate_limit: float = 1.5,
    ):
        self._owns_browser = context is None
        self._pw: Playwright | None = None
        self._browser = None
        self.rate_limit_sec = rate_limit

        if context is not None:
            self.context = context
        else:
            # Create our own browser
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=True)
            self.context = self._browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1440, "height": 900},
                locale="en-US",
            )

    def close(self):
        """Clean up browser resources."""
        if self._owns_browser:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()

    def _rate_limit(self):
        """Sleep between requests to be respectful."""
        jitter = random.uniform(0.5, self.rate_limit_sec)
        time.sleep(jitter)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
