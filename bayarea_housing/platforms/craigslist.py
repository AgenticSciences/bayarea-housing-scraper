"""Craigslist SF Bay Area scraper."""

from __future__ import annotations

import re
import time
import logging
from typing import Any

from bayarea_housing.platforms.base import BaseScraper, Listing

logger = logging.getLogger(__name__)

# Area codes for SF Bay Area sub-regions
AREAS = {
    "sf": "sfc",       # San Francisco
    "peninsula": "pen", # Peninsula (Palo Alto, RWC, etc.)
    "southbay": "sby",  # South Bay (San Jose, Sunnyvale, etc.)
    "eastbay": "eby",   # East Bay (Oakland, Berkeley, etc.)
    "northbay": "nby",  # North Bay (Marin, etc.)
}

# Listing categories
CATEGORIES = {
    "apartments": "apa",   # Apartments / housing for rent
    "rooms": "roo",        # Rooms / shared
    "sublets": "sub",      # Sublets / temporary
}


class CraigslistScraper(BaseScraper):
    """Scrape housing listings from Craigslist SF Bay Area."""

    BASE_URL = "https://sfbay.craigslist.org"

    def scrape(
        self,
        areas: list[str] | None = None,
        categories: list[str] | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        furnished: bool = False,
        query: str | None = None,
    ) -> list[Listing]:
        """
        Scrape Craigslist listings.

        Args:
            areas: List of area keys (sf, peninsula, southbay, eastbay, northbay).
                   Defaults to all areas.
            categories: List of category keys (apartments, rooms, sublets).
                        Defaults to ["apartments", "rooms"].
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            furnished: Only show furnished listings.
            query: Free-text search query.

        Returns:
            List of Listing dicts.
        """
        areas = areas or list(AREAS.keys())
        categories = categories or ["apartments", "rooms"]
        all_listings: list[Listing] = []

        for area_key in areas:
            area_code = AREAS.get(area_key, area_key)
            for cat_key in categories:
                cat_code = CATEGORIES.get(cat_key, cat_key)
                url = self._build_url(area_code, cat_code, min_price, max_price, furnished, query)
                logger.info("Scraping CL: %s/%s → %s", area_key, cat_key, url)
                try:
                    listings = self._scrape_search_page(url, area_key, cat_key)
                    all_listings.extend(listings)
                except Exception as e:
                    logger.error("Error scraping %s: %s", url, e)
                self._rate_limit()

        return all_listings

    def fetch_detail(self, url: str) -> dict[str, Any]:
        """Fetch details from a single Craigslist listing page."""
        page = self.context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1)
            detail = page.evaluate("""() => {
                const title = document.querySelector('#titletextonly');
                const price = document.querySelector('.price');
                const body = document.querySelector('#postingbody');
                const addr = document.querySelector('.mapaddress');
                const imgs = document.querySelectorAll('img[id$="_image"]');
                const bodyText = body ? body.innerText.replace(/QR Code Link.*/, '').trim() : '';
                return {
                    title: title ? title.innerText.trim() : '',
                    price: price ? price.innerText.trim() : '',
                    address: addr ? addr.innerText.trim() : '',
                    body: bodyText.substring(0, 2000),
                    image_count: imgs.length,
                };
            }""")
            detail["url"] = url
            return detail
        finally:
            page.close()

    # ── internal ──

    def _build_url(
        self, area: str, category: str,
        min_price: int | None, max_price: int | None,
        furnished: bool, query: str | None,
    ) -> str:
        url = f"{self.BASE_URL}/search/{area}/{category}?"
        params: list[str] = []
        if min_price:
            params.append(f"min_price={min_price}")
        if max_price:
            params.append(f"max_price={max_price}")
        if furnished:
            params.append("is_furnished=1")
        if query:
            params.append(f"query={query.replace(' ', '+')}")
        params.append("availabilityMode=0")
        return url + "&".join(params)

    def _scrape_search_page(self, url: str, area: str, category: str) -> list[Listing]:
        page = self.context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(3)

            # Try structured selectors first, fall back to text parsing
            raw = page.evaluate("""() => {
                // Method 1: structured elements
                const structured = [];
                document.querySelectorAll('.cl-search-result, li.cl-static-search-result').forEach(el => {
                    const a = el.querySelector('a');
                    const price = el.querySelector('.priceinfo, .price, [class*="price"]');
                    const loc = el.querySelector('.label-text, .meta, .location, [class*="location"]');
                    if (a) {
                        structured.push({
                            title: a.innerText.trim().substring(0, 150),
                            url: a.href,
                            price: price ? price.innerText.trim() : '',
                            location: loc ? loc.innerText.trim() : '',
                        });
                    }
                });
                if (structured.length > 0) return structured;

                // Method 2: text-based fallback
                const results = [];
                const links = Array.from(document.querySelectorAll('a[href*="/d/"]'));
                const lines = document.body.innerText.split('\\n').filter(l => l.trim());
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].trim().startsWith('$')) {
                        const price = lines[i].trim();
                        const title = (i > 0) ? lines[i-1].trim() : '';
                        const location = (i < lines.length - 1) ? lines[i+1].trim() : '';
                        if (title.length > 5) {
                            results.push({title, price, location, url: ''});
                        }
                    }
                }
                // Try to match URLs
                for (let i = 0; i < Math.min(results.length, links.length); i++) {
                    results[i].url = links[i].href;
                }
                return results.slice(0, 40);
            }""")

            listings: list[Listing] = []
            for item in raw:
                price = self._parse_price(item.get("price", ""))
                listings.append({
                    "source": "craigslist",
                    "title": item.get("title", ""),
                    "price": price,
                    "price_raw": item.get("price", ""),
                    "location": item.get("location", ""),
                    "url": item.get("url", ""),
                    "area": area,
                    "category": category,
                })
            return listings
        finally:
            page.close()

    @staticmethod
    def _parse_price(text: str) -> int | None:
        m = re.search(r"\$([0-9,]+)", text)
        if m:
            return int(m.group(1).replace(",", ""))
        return None
