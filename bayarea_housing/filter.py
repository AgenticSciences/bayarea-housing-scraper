"""Filter and sort housing listings."""

from __future__ import annotations

import re
from typing import Any

from bayarea_housing.platforms.base import Listing
from bayarea_housing.safety import SafetyScorer


class ListingFilter:
    """Filter, sort, and rank housing listings.

    Usage:
        f = ListingFilter()
        results = f.filter(listings, min_price=800, max_price=2000, area="sf")
        results = f.sort_by_safety(results)
    """

    def __init__(self):
        self.scorer = SafetyScorer()

    def filter(
        self,
        listings: list[Listing],
        min_price: int | None = None,
        max_price: int | None = None,
        area: str | None = None,
        source: str | None = None,
        furnished: bool = False,
        short_term: bool = False,
        keywords: list[str] | None = None,
        exclude_scams: bool = True,
    ) -> list[Listing]:
        """
        Filter listings by various criteria.

        Args:
            listings: Input listings to filter.
            min_price: Minimum monthly rent.
            max_price: Maximum monthly rent.
            area: Area filter (sf, peninsula, southbay, eastbay).
            source: Platform filter (craigslist, supost, bay123).
            furnished: Only show listings mentioning "furnished".
            short_term: Only show short-term/sublet listings.
            keywords: Additional keyword filters (any match).
            exclude_scams: Remove likely scam listings.

        Returns:
            Filtered list of listings.
        """
        results = listings

        if exclude_scams:
            results = [l for l in results if not self._is_likely_scam(l)]

        if min_price is not None:
            results = [l for l in results if l.get("price") is not None and l["price"] >= min_price]

        if max_price is not None:
            results = [l for l in results if l.get("price") is not None and l["price"] <= max_price]

        if area:
            area_lower = area.lower()
            results = [l for l in results if self._matches_area(l, area_lower)]

        if source:
            results = [l for l in results if l.get("source") == source]

        if furnished:
            results = [l for l in results if self._mentions_furnished(l)]

        if short_term:
            results = [l for l in results if self._is_short_term(l)]

        if keywords:
            results = [l for l in results if self._matches_keywords(l, keywords)]

        return results

    def sort_by_safety(self, listings: list[Listing], descending: bool = True) -> list[Listing]:
        """Sort listings by neighborhood safety score."""
        def safety_key(listing: Listing) -> float:
            score = self.scorer.score(
                listing.get("title", ""),
                listing.get("location", ""),
                listing.get("url", ""),
            )
            return score
        return sorted(listings, key=safety_key, reverse=descending)

    def sort_by_price(self, listings: list[Listing], descending: bool = False) -> list[Listing]:
        """Sort listings by price."""
        def price_key(listing: Listing) -> int:
            return listing.get("price") or 999999
        return sorted(listings, key=price_key, reverse=descending)

    def enrich_with_safety(self, listings: list[Listing]) -> list[Listing]:
        """Add safety_score and neighborhood fields to each listing."""
        for listing in listings:
            text = " ".join([
                listing.get("title", ""),
                listing.get("location", ""),
                listing.get("url", ""),
            ])
            score, neighborhood = self.scorer.score_with_name(text)
            listing["safety_score"] = score
            listing["neighborhood"] = neighborhood or ""
        return listings

    # ── Scam detection ──

    @staticmethod
    def _is_likely_scam(listing: Listing) -> bool:
        """Heuristic scam detection."""
        price = listing.get("price")
        title = (listing.get("title") or "").lower()
        location = (listing.get("location") or "").lower()

        # SF apartment under $700 is almost certainly a scam
        if price is not None and price < 700 and "sf" in str(listing.get("area", "")):
            return True

        # $1 listings
        if price is not None and price <= 5:
            return True

        # Wrong city (e.g., Brooklyn appearing in SF search)
        wrong_cities = ["brooklyn", "new york", "queens", "bronx", "manhattan", "chicago", "miami"]
        if any(city in title or city in location for city in wrong_cities):
            return True

        return False

    @staticmethod
    def _matches_area(listing: Listing, area: str) -> bool:
        searchable = " ".join([
            listing.get("area", ""),
            listing.get("location", ""),
            listing.get("title", ""),
        ]).lower()
        area_aliases = {
            "sf": ["sf", "sfc", "san francisco", "三藩", "旧金山"],
            "peninsula": ["pen", "peninsula", "palo alto", "menlo park", "redwood city", "san mateo", "daly city"],
            "southbay": ["sby", "south bay", "san jose", "sunnyvale", "mountain view", "cupertino", "santa clara"],
            "eastbay": ["eby", "east bay", "oakland", "berkeley", "hayward", "fremont", "alameda"],
        }
        aliases = area_aliases.get(area, [area])
        return any(alias in searchable for alias in aliases)

    @staticmethod
    def _mentions_furnished(listing: Listing) -> bool:
        text = " ".join([
            listing.get("title", ""),
            listing.get("location", ""),
        ]).lower()
        return any(kw in text for kw in ["furnish", "家具", "全配", "拎包"])

    @staticmethod
    def _is_short_term(listing: Listing) -> bool:
        text = " ".join([
            listing.get("title", ""),
            listing.get("category", ""),
        ]).lower()
        return any(kw in text for kw in [
            "short term", "short-term", "sublet", "temporary", "month-to-month",
            "短租", "转租", "sub",
        ])

    @staticmethod
    def _matches_keywords(listing: Listing, keywords: list[str]) -> bool:
        text = " ".join([
            listing.get("title", ""),
            listing.get("location", ""),
        ]).lower()
        return any(kw.lower() in text for kw in keywords)
