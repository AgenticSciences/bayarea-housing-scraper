#!/usr/bin/env python3
"""Basic usage example for Bay Area Housing Scraper."""

from bayarea_housing import HousingScraper, ListingFilter

def main():
    # Create scraper (uses Patchright browser)
    with HousingScraper() as scraper:
        print("🏠 Scraping Bay Area housing listings...")
        print()
        
        # Scrape all platforms with filters
        listings = scraper.scrape_all(
            platforms=["craigslist", "supost", "bay123"],
            areas=["sf", "peninsula"],  # SF + Peninsula only
            min_price=1000,
            max_price=2500,
            furnished=True,  # Craigslist furnished filter
        )
        
        print(f"\n✅ Found {len(listings)} raw listings")
    
    # Create filter
    f = ListingFilter()
    
    # Apply additional filters
    listings = f.filter(
        listings,
        area="sf",  # SF only (filter Peninsula out)
        min_price=1500,
        max_price=2000,
        furnished=True,
        short_term=False,
        exclude_scams=True,  # Remove obvious scams
    )
    
    print(f"📋 After filtering: {len(listings)} listings")
    
    # Enrich with safety scores
    listings = f.enrich_with_safety(listings)
    
    # Sort by safety (safest first)
    listings = f.sort_by_safety(listings, descending=True)
    
    # Print top 10 safest listings
    print("\n🏆 Top 10 Safest Listings:\n")
    print("=" * 80)
    
    safety_emoji = {5: "🟢", 4: "🔵", 3: "🟡", 2: "🟠", 1: "🔴", 0: "⚪"}
    
    for i, listing in enumerate(listings[:10], 1):
        score = listing.get("safety_score", 0)
        emoji = safety_emoji.get(score, "⚪")
        hood = listing.get("neighborhood", "Unknown")
        price = listing.get("price")
        price_str = f"${price:,}" if price else "N/A"
        
        print(f"\n{i}. {emoji} {score}/5 — {hood}")
        print(f"   💰 {price_str}/month")
        print(f"   📝 {listing['title'][:70]}")
        print(f"   🏢 Source: {listing['source']}")
        if listing.get("location"):
            print(f"   📍 {listing['location']}")
        print(f"   🔗 {listing['url']}")
    
    print("\n" + "=" * 80)
    print(f"\nTotal: {len(listings)} SF listings in $1500-$2000 range")
    print("\n💡 Tip: Visit neighborhoods in person before signing a lease!")

if __name__ == "__main__":
    main()
