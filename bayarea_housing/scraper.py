"""Main scraper — orchestrates all platforms."""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime
from pathlib import Path

from patchright.sync_api import sync_playwright

from bayarea_housing.platforms.base import Listing, USER_AGENTS
from bayarea_housing.platforms.craigslist import CraigslistScraper
from bayarea_housing.platforms.supost import SUPostScraper
from bayarea_housing.platforms.bay123 import Bay123Scraper

logger = logging.getLogger(__name__)


class HousingScraper:
    """Orchestrates scraping across all platforms.

    Usage:
        with HousingScraper() as scraper:
            listings = scraper.scrape_all()
            scraper.save(listings, "output.json")
    """

    def __init__(self, headless: bool = True, rate_limit: float = 1.5):
        self.headless = headless
        self.rate_limit = rate_limit
        self._pw = None
        self._browser = None
        self._context = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        return self

    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def scrape_all(
        self,
        platforms: list[str] | None = None,
        **kwargs,
    ) -> list[Listing]:
        """
        Scrape all (or selected) platforms.

        Args:
            platforms: List of platform names to scrape.
                       Options: "craigslist", "supost", "bay123".
                       Defaults to all.
            **kwargs: Passed through to individual scrapers.

        Returns:
            Deduplicated list of listings.
        """
        platforms = platforms or ["craigslist", "supost", "bay123"]
        all_listings: list[Listing] = []

        if "craigslist" in platforms:
            logger.info("─── Craigslist ───")
            cl = CraigslistScraper(context=self._context, rate_limit=self.rate_limit)
            listings = cl.scrape(
                areas=kwargs.get("areas"),
                categories=kwargs.get("categories"),
                min_price=kwargs.get("min_price"),
                max_price=kwargs.get("max_price"),
                furnished=kwargs.get("furnished", False),
                query=kwargs.get("query"),
            )
            all_listings.extend(listings)
            logger.info("Craigslist: %d listings", len(listings))

        if "supost" in platforms:
            logger.info("─── SUPost ───")
            sp = SUPostScraper(context=self._context, rate_limit=self.rate_limit)
            listings = sp.scrape(
                query=kwargs.get("supost_query", "housing rent"),
            )
            all_listings.extend(listings)
            logger.info("SUPost: %d listings", len(listings))

        if "bay123" in platforms:
            logger.info("─── Bay123 ───")
            b123 = Bay123Scraper(context=self._context, rate_limit=self.rate_limit)
            listings = b123.scrape(
                forums=kwargs.get("forums"),
                pages=kwargs.get("bay123_pages", 2),
            )
            all_listings.extend(listings)
            logger.info("Bay123: %d listings", len(listings))

        deduped = self._deduplicate(all_listings)
        logger.info("Total: %d listings (%d after dedup)", len(all_listings), len(deduped))
        return deduped

    @staticmethod
    def _deduplicate(listings: list[Listing]) -> list[Listing]:
        """Remove duplicate listings by URL."""
        seen: set[str] = set()
        unique: list[Listing] = []
        for listing in listings:
            key = listing.get("url", listing.get("title", ""))
            if key and key not in seen:
                seen.add(key)
                unique.append(listing)
        return unique

    @staticmethod
    def save(listings: list[Listing], path: str | Path) -> Path:
        """Save listings to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": len(listings),
            "listings": listings,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d listings to %s", len(listings), path)
        return path
