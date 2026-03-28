"""Bay123 (Chinese community forum) scraper."""

from __future__ import annotations

import re
import time
import logging

from bayarea_housing.platforms.base import BaseScraper, Listing

logger = logging.getLogger(__name__)

# Forum section IDs on Bay123 (Discuz! based)
FORUMS = {
    "main": 40,        # 租房主版 (main rental board)
    "whole": 158,       # 房屋整租 (whole unit rentals)
    "short": 165,       # 短租房 (short-term rentals)
}


class Bay123Scraper(BaseScraper):
    """Scrape housing listings from Bay123 (bay123.com).

    Bay123 is a Chinese community forum for the San Francisco Bay Area.
    It runs on Discuz! and has dedicated housing rental sections.
    Listings are predominantly in Chinese (Simplified + Traditional).
    """

    BASE_URL = "http://www.bay123.com"

    def scrape(
        self,
        forums: list[str] | None = None,
        pages: int = 2,
    ) -> list[Listing]:
        """
        Scrape Bay123 forum listings.

        Args:
            forums: List of forum keys (main, whole, short).
                    Defaults to all.
            pages: Number of pages to scrape per forum section.

        Returns:
            List of Listing dicts.
        """
        forums = forums or list(FORUMS.keys())
        all_listings: list[Listing] = []

        for forum_key in forums:
            forum_id = FORUMS.get(forum_key, forum_key)
            for pg in range(1, pages + 1):
                url = f"{self.BASE_URL}/forum-{forum_id}-{pg}.html"
                logger.info("Scraping Bay123: %s page %d → %s", forum_key, pg, url)
                try:
                    listings = self._scrape_forum_page(url, forum_key)
                    all_listings.extend(listings)
                except Exception as e:
                    logger.error("Error scraping %s: %s", url, e)
                self._rate_limit()

        return all_listings

    def fetch_detail(self, url: str) -> dict:
        """Fetch details from a Bay123 thread page."""
        page = self.context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            detail = page.evaluate("""() => {
                const title = document.querySelector('#thread_subject');
                const post = document.querySelector('td[id^="postmessage_"]');
                const author = document.querySelector('.authi a');
                const date = document.querySelector('.authi em');
                const bodyText = post ? post.innerText.trim() : '';
                return {
                    title: title ? title.innerText.trim() : '',
                    body: bodyText.substring(0, 3000),
                    author: author ? author.innerText.trim() : '',
                    date: date ? date.innerText.trim() : '',
                };
            }""")
            detail["url"] = url
            return detail
        finally:
            page.close()

    # ── internal ──

    def _scrape_forum_page(self, url: str, forum_key: str) -> list[Listing]:
        page = self.context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(4)

            raw = page.evaluate("""() => {
                const results = [];
                const rows = document.querySelectorAll('tbody[id^="normalthread_"], tr');
                rows.forEach(row => {
                    const a = row.querySelector('a.s.xst') || row.querySelector('th a[href*="thread-"]');
                    if (a) {
                        const title = a.innerText.trim();
                        const href = a.href;
                        const author = row.querySelector('td.by cite a, .by cite a');
                        const date = row.querySelector('td.by em, .by em');
                        results.push({
                            title: title.substring(0, 150),
                            url: href,
                            author: author ? author.innerText.trim() : '',
                            date: date ? date.innerText.trim() : '',
                        });
                    }
                });
                return results;
            }""")

            listings: list[Listing] = []
            for item in raw:
                price = self._parse_price(item.get("title", ""))
                listings.append({
                    "source": "bay123",
                    "title": item.get("title", ""),
                    "price": price,
                    "price_raw": f"${price}" if price else "",
                    "location": "",
                    "url": item.get("url", ""),
                    "area": "",
                    "category": forum_key,
                    "author": item.get("author", ""),
                    "date": item.get("date", ""),
                })

            return listings
        finally:
            page.close()

    @staticmethod
    def _parse_price(text: str) -> int | None:
        m = re.search(r"\$(\d[\d,]*)", text)
        if m:
            return int(m.group(1).replace(",", ""))
        return None
