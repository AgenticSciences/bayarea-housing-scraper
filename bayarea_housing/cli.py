"""CLI entry point for bayarea-housing scraper."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from bayarea_housing.scraper import HousingScraper
from bayarea_housing.filter import ListingFilter


def main():
    parser = argparse.ArgumentParser(
        prog="bayarea-housing",
        description="Scrape Bay Area housing listings from multiple platforms",
    )

    # Platform selection
    parser.add_argument(
        "--platforms", "-p",
        nargs="+",
        choices=["craigslist", "supost", "bay123"],
        default=["craigslist", "supost", "bay123"],
        help="Platforms to scrape (default: all)",
    )

    # Area filters
    parser.add_argument(
        "--areas", "-a",
        nargs="+",
        choices=["sf", "peninsula", "southbay", "eastbay", "northbay"],
        help="Craigslist areas to search (default: all)",
    )

    # Price range
    parser.add_argument("--min-price", type=int, help="Minimum monthly rent")
    parser.add_argument("--max-price", type=int, help="Maximum monthly rent")

    # Filters
    parser.add_argument("--furnished", action="store_true", help="Only furnished listings")
    parser.add_argument("--short-term", action="store_true", help="Only short-term/sublet listings")
    parser.add_argument("--query", "-q", help="Free-text search query (Craigslist)")
    parser.add_argument("--keywords", "-k", nargs="+", help="Filter by keywords")

    # Safety
    parser.add_argument("--min-safety", type=int, choices=[1, 2, 3, 4, 5],
                        help="Minimum safety score (1-5)")
    parser.add_argument("--sort-safety", action="store_true",
                        help="Sort results by safety score (safest first)")

    # Output
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--format", choices=["json", "text"], default="text",
                        help="Output format (default: text)")

    # Options
    parser.add_argument("--no-scam-filter", action="store_true",
                        help="Disable scam detection filter")
    parser.add_argument("--rate-limit", type=float, default=1.5,
                        help="Seconds between requests (default: 1.5)")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browser headless (default: true)")
    parser.add_argument("--no-headless", action="store_true",
                        help="Show browser window (for debugging)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")

    # Bay123 options
    parser.add_argument("--bay123-pages", type=int, default=2,
                        help="Pages to scrape per Bay123 forum (default: 2)")
    parser.add_argument("--bay123-forums", nargs="+",
                        choices=["main", "whole", "short"],
                        help="Bay123 forum sections (default: all)")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    headless = not args.no_headless

    # Scrape
    print(f"🏠 Bay Area Housing Scraper")
    print(f"   Platforms: {', '.join(args.platforms)}")
    if args.min_price or args.max_price:
        print(f"   Price: ${args.min_price or '?'} - ${args.max_price or '?'}")
    print()

    with HousingScraper(headless=headless, rate_limit=args.rate_limit) as scraper:
        listings = scraper.scrape_all(
            platforms=args.platforms,
            areas=args.areas,
            min_price=args.min_price,
            max_price=args.max_price,
            furnished=args.furnished,
            query=args.query,
            forums=args.bay123_forums,
            bay123_pages=args.bay123_pages,
        )

    # Filter
    f = ListingFilter()
    listings = f.filter(
        listings,
        min_price=args.min_price,
        max_price=args.max_price,
        furnished=args.furnished,
        short_term=args.short_term,
        keywords=args.keywords,
        exclude_scams=not args.no_scam_filter,
    )

    # Safety enrichment
    listings = f.enrich_with_safety(listings)

    # Safety filter
    if args.min_safety:
        listings = [l for l in listings if l.get("safety_score", 0) >= args.min_safety]

    # Sort
    if args.sort_safety:
        listings = f.sort_by_safety(listings)
    else:
        listings = f.sort_by_price(listings)

    # Output
    if args.output:
        HousingScraper.save(listings, args.output)
        print(f"\n💾 Saved {len(listings)} listings to {args.output}")

    if args.format == "json":
        print(json.dumps(listings, ensure_ascii=False, indent=2))
    else:
        _print_text(listings)


def _print_text(listings: list):
    """Pretty-print listings to terminal."""
    safety_emoji = {5: "🟢", 4: "🔵", 3: "🟡", 2: "🟠", 1: "🔴", 0: "⚪"}

    print(f"Found {len(listings)} listings\n")
    print("=" * 80)

    for i, l in enumerate(listings, 1):
        score = l.get("safety_score", 0)
        emoji = safety_emoji.get(score, "⚪")
        price_str = f"${l['price']:,}" if l.get("price") else "N/A"
        hood = l.get("neighborhood", "")

        print(f"\n{i}. [{l.get('source', '?')}] {price_str} — {l.get('title', '')[:80]}")
        if l.get("location"):
            print(f"   📍 {l['location']}")
        if hood:
            print(f"   {emoji} Safety: {score}/5 ({hood})")
        if l.get("url"):
            print(f"   🔗 {l['url']}")

    print("\n" + "=" * 80)
    print(f"\nTotal: {len(listings)} listings")


if __name__ == "__main__":
    main()
