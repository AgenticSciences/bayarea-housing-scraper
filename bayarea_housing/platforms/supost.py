"""SUPost (Stanford community marketplace) scraper."""

from __future__ import annotations

import re
import time
import logging

from bayarea_housing.platforms.base import BaseScraper, Listing

logger = logging.getLogger(__name__)

# Keywords that indicate a housing listing (vs. "looking for" or non-housing posts)
HOUSING_KEYWORDS = [
    "room", "rent", "housing", "sublet", "bedroom", "apartment",
    "bath", "studio", "lease", "housemate", "furnished",
    "b1b", "b2b", "br", "1b", "2b", "3b",
]


class SUPostScraper(BaseScraper):
    """Scrape housing listings from SUPost (supost.com).

    SUPost is Stanford University's community marketplace. Posts are verified
    with @stanford.edu email addresses, making it a relatively trustworthy
    source for housing near Stanford / Palo Alto / Menlo Park area.
    """

    BASE_URL = "https://www.supost.com"

    def scrape(
        self,
        query: str = "housing rent",
        category: str = "housing",
    ) -> list[Listing]:
        """
        Scrape SUPost housing listings.

        Args:
            query: Search query string.
            category: SUPost category filter.

        Returns:
            List of Listing dicts.
        """
        url = f"{self.BASE_URL}/search?query={query.replace(' ', '+')}&category={category}"
        logger.info("Scraping SUPost: %s", url)

        page = self.context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(3)

            raw = page.evaluate("""(keywords) => {
                const results = [];
                document.querySelectorAll('a[href*="/post/index/"]').forEach(a => {
                    const text = a.innerText.trim();
                    const isHousing = keywords.some(kw =>
                        text.toLowerCase().includes(kw.toLowerCase())
                    );
                    if (isHousing && text.length > 5) {
                        const priceMatch = text.match(/\\$([0-9,]+)/);
                        results.push({
                            title: text.replace(/\\s*-\\s*\\$[0-9,]+$/, '').trim().substring(0, 150),
                            price_raw: priceMatch ? '$' + priceMatch[1] : '',
                            url: a.getAttribute('href'),
                        });
                    }
                });
                return results;
            }""", HOUSING_KEYWORDS)

            listings: list[Listing] = []
            for item in raw:
                href = item.get("url", "")
                if not href.startswith("http"):
                    href = self.BASE_URL + href

                price = self._parse_price(item.get("price_raw", ""))
                listings.append({
                    "source": "supost",
                    "title": item.get("title", ""),
                    "price": price,
                    "price_raw": item.get("price_raw", ""),
                    "location": "",  # SUPost doesn't show location in search
                    "url": href,
                    "area": "peninsula",
                    "category": "housing",
                })

            logger.info("SUPost: found %d listings", len(listings))
            return listings
        finally:
            page.close()

    @staticmethod
    def _parse_price(text: str) -> int | None:
        m = re.search(r"\$([0-9,]+)", text)
        if m:
            return int(m.group(1).replace(",", ""))
        return None
