# Bay Area Housing Scraper

A multi-platform scraper for Bay Area rental housing listings. Aggregates listings from **Craigslist**, **SUPost** (Stanford community), and **Bay123** (Chinese community forum).

## Why This Tool?

- **Multi-platform aggregation**: See listings from 3 different platforms in one place
- **SF neighborhood safety scoring**: Built-in safety ratings for San Francisco neighborhoods (1-5 scale)
- **Smart filtering**: Price, location, furnished, short-term, and keyword filters
- **Scam detection**: Heuristic filters to remove obvious scam listings
- **Stealth scraping**: Uses [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) (Playwright fork) for JavaScript-rendered sites with anti-bot bypass

## Platforms

| Platform | Coverage | Language | Login Required |
|----------|----------|----------|----------------|
| **Craigslist** | SF Bay Area (SF, Peninsula, South Bay, East Bay) | English | No |
| **SUPost** | Stanford/Palo Alto area | English | No (but requires @stanford.edu to reply) |
| **Bay123** | Bay Area Chinese community | Chinese (Simplified/Traditional) | No |

## Installation

```bash
# Clone the repo
git clone https://github.com/agentic-sciences/bayarea-housing-scraper.git
cd bayarea-housing-scraper

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Quick Start

### CLI

```bash
# Search all platforms, SF + Peninsula, $1500-$2500, furnished
bayarea-housing --areas sf peninsula --min-price 1500 --max-price 2500 --furnished

# Sort by safety (safest neighborhoods first)
bayarea-housing --areas sf --max-price 2000 --sort-safety --min-safety 4

# Save to JSON
bayarea-housing --areas sf --max-price 2000 -o results.json

# Short-term/sublet only
bayarea-housing --areas sf --short-term --max-price 1800

# Search with keywords
bayarea-housing --areas sf --keywords "studio" "sunset" --max-price 1500
```

### Python API

```python
from bayarea_housing import HousingScraper, ListingFilter

# Scrape all platforms
with HousingScraper() as scraper:
    listings = scraper.scrape_all(
        platforms=["craigslist", "supost", "bay123"],
        areas=["sf", "peninsula"],
        min_price=1000,
        max_price=2500,
        furnished=True,
    )

# Filter and sort
f = ListingFilter()
listings = f.filter(listings, area="sf", min_price=1500)
listings = f.enrich_with_safety(listings)
listings = f.sort_by_safety(listings)

# Print top 5 safest
for listing in listings[:5]:
    print(f"{listing['safety_score']}/5 - ${listing['price']} - {listing['title']}")
```

See `examples/basic_search.py` for a complete example.

## Platform-Specific Notes

### Craigslist

**Areas:**
- `sf` — San Francisco
- `peninsula` — Palo Alto, Redwood City, San Mateo, Daly City
- `southbay` — San Jose, Sunnyvale, Mountain View, Cupertino
- `eastbay` — Oakland, Berkeley, Fremont, Hayward
- `northbay` — Marin, Napa, Sonoma

**Categories:**
- `apartments` — Whole unit rentals
- `rooms` — Room shares
- `sublets` — Short-term/sublet

**Search filters:**
- `min_price`, `max_price` — Price range (monthly rent)
- `furnished=True` — Only furnished listings
- `query` — Free-text search

**Detail fetching:**
```python
from bayarea_housing.platforms import CraigslistScraper

with CraigslistScraper() as cl:
    listings = cl.scrape(areas=["sf"], max_price=2000)
    # Fetch full details for first listing
    detail = cl.fetch_detail(listings[0]["url"])
    print(detail["body"])  # Full description
    print(detail["image_count"])  # Number of photos
```

### SUPost

**What is SUPost?**
SUPost is Stanford University's community marketplace. Listings are verified with `@stanford.edu` email addresses, making it a relatively trustworthy source.

**Coverage:**
Primarily Stanford campus, Palo Alto, Menlo Park, and nearby Peninsula areas.

**Limitations:**
- Replying to listings requires a Stanford email address
- Smaller volume than Craigslist
- Search is keyword-based (no structured filters)

**Usage:**
```python
from bayarea_housing.platforms import SUPostScraper

with SUPostScraper() as sp:
    listings = sp.scrape(query="housing rent palo alto")
```

### Bay123

**What is Bay123?**
Bay123 (bay123.com) is a Chinese community forum for the SF Bay Area. It runs on Discuz! and has dedicated housing sections. Listings are predominantly in Chinese (Simplified and Traditional).

**Forum sections:**
- `main` (40) — 租房主版 (main rental board)
- `whole` (158) — 房屋整租 (whole unit rentals)
- `short` (165) — 短租房 (short-term rentals)

**Usage:**
```python
from bayarea_housing.platforms import Bay123Scraper

with Bay123Scraper() as b123:
    listings = b123.scrape(forums=["main", "short"], pages=3)
    
    # Fetch thread details
    detail = b123.fetch_detail(listings[0]["url"])
    print(detail["body"])  # Full post content
    print(detail["author"])  # Poster username
```

**Advantages:**
- Direct contact with Chinese-speaking landlords
- Often includes WeChat IDs for communication
- Prices may be negotiable
- Community trust signals (forum reputation, post history)

**Considerations:**
- Most listings in Chinese (use translation tools if needed)
- Forum etiquette matters (respectful communication expected)
- Some posts are "求租" (seeking housing) rather than "出租" (offering)

## Safety Scoring

The scraper includes **neighborhood safety ratings for San Francisco** based on publicly available crime statistics and community knowledge. These are approximate guides, **not** definitive safety guarantees.

**Scale:** 1-5 (5 = safest)

### Safety Tiers

**⭐⭐⭐⭐⭐ (5/5) — Safest:**
Sunset, Noe Valley, Bernal Heights, Marina, Pacific Heights, Presidio, West Portal, Forest Hill, Glen Park, Twin Peaks

**⭐⭐⭐⭐ (4/5) — Safe:**
Richmond, Upper Haight, Alamo Square, Daly City, Castro, Nob Hill, Russian Hill, Hayes Valley, Potrero Hill

**⭐⭐⭐ (3/5) — Moderate:**
SOMA, Mission (Valencia corridor), North Beach, Portola, Excelsior, Financial District, Chinatown

**⭐⭐ (2/5) — Caution:**
Lower Nob Hill, Civic Center, Mid-Market, Western Addition (south)

**⭐ (1/5) — Avoid:**
Tenderloin, 6th Street corridor

**Usage:**
```python
from bayarea_housing import ListingFilter

f = ListingFilter()
listings = f.enrich_with_safety(listings)  # Adds safety_score and neighborhood fields
listings = f.sort_by_safety(listings)      # Sort by safety (safest first)

# Filter for safe neighborhoods only
safe = [l for l in listings if l.get("safety_score", 0) >= 4]
```

**⚠️ Important:** Always visit neighborhoods in person before signing a lease. Safety conditions can vary block-by-block.

## Scam Detection

The scraper includes heuristic filters to remove obvious scams:

- ❌ SF apartments under $700/month (unrealistic)
- ❌ $1 listings (spam)
- ❌ Wrong city (e.g., Brooklyn appearing in SF search results)
- ❌ Template/copy-paste spam patterns

**Disable scam filtering:**
```bash
bayarea-housing --no-scam-filter
```

**Note:** Scam detection is heuristic and not perfect. Always verify listings independently.

## Rate Limiting

The scraper includes respectful rate limiting (1.5 seconds between requests by default) to avoid overwhelming target sites.

**Adjust rate limit:**
```bash
bayarea-housing --rate-limit 2.5  # Wait 2.5 seconds between requests
```

```python
with HousingScraper(rate_limit=2.0) as scraper:
    listings = scraper.scrape_all()
```

## Advanced Usage

### Fetch Individual Listing Details

```python
from bayarea_housing.platforms import CraigslistScraper, Bay123Scraper

with CraigslistScraper() as cl:
    listings = cl.scrape(areas=["sf"], max_price=2000)
    
    # Fetch full details for listings of interest
    for listing in listings[:5]:
        detail = cl.fetch_detail(listing["url"])
        print(f"\n{listing['title']}")
        print(f"Body: {detail['body'][:200]}...")
        print(f"Photos: {detail['image_count']}")
```

### Custom Filters

```python
from bayarea_housing import ListingFilter

f = ListingFilter()

# Multiple filters
listings = f.filter(
    listings,
    area="sf",
    min_price=1000,
    max_price=2000,
    furnished=True,
    short_term=True,
    keywords=["studio", "sunset"],
    exclude_scams=True,
)

# Sort by price
listings = f.sort_by_price(listings, descending=False)  # Cheapest first
```

### Extend Safety Data

```python
from bayarea_housing.safety import SafetyScorer

# Add custom neighborhoods
custom_hoods = {
    "My Neighborhood": (5, ["my hood", "custom area"]),
}

scorer = SafetyScorer(neighborhoods=custom_hoods)
score = scorer.score("Apartment in My Hood")  # Returns 5
```

## Output Formats

### JSON

```bash
bayarea-housing --areas sf --max-price 2000 -o results.json --format json
```

**JSON structure:**
```json
{
  "timestamp": "2026-03-28T05:30:00",
  "count": 42,
  "listings": [
    {
      "source": "craigslist",
      "title": "Sunny 1BR in Sunset District",
      "price": 1800,
      "price_raw": "$1,800",
      "location": "outer sunset",
      "url": "https://sfbay.craigslist.org/...",
      "area": "sf",
      "category": "apartments",
      "safety_score": 5,
      "neighborhood": "Sunset"
    }
  ]
}
```

### Text (Terminal)

```bash
bayarea-housing --areas sf --max-price 2000
```

Output includes:
- Safety emoji indicators (🟢🔵🟡🟠🔴)
- Price, title, location
- Clickable URLs

## Contributing

Contributions welcome! Areas for improvement:

- **More platforms**: Zillow, Apartments.com, Facebook Marketplace (needs auth), Xiaohongshu (小红书)
- **Better scam detection**: ML-based filtering, price anomaly detection
- **Peninsula/South Bay safety data**: Extend safety scoring beyond SF
- **Email alerts**: Notify when new matching listings appear
- **Photo analysis**: OCR on listing photos, image quality scoring
- **Listing change detection**: Track price changes, availability updates

**To contribute:**
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/new-platform`)
3. Make your changes with tests
4. Submit a pull request

## Disclaimer

**Legal:** This tool is for personal use only. Respect the Terms of Service of each platform. Do not use for commercial scraping or high-volume automated access.

**Safety:** Neighborhood safety ratings are approximate guides based on publicly available data and community knowledge. They are NOT definitive safety guarantees. Crime can happen anywhere. Always:
- Visit neighborhoods in person before signing a lease
- Research recent crime reports
- Talk to current residents
- Trust your instincts

**Scam Warning:** Always verify listings independently. Meet landlords in person. Never wire money or pay deposits without seeing the property. If a deal seems too good to be true, it probably is.

## License

MIT License — see [LICENSE](LICENSE)

## Acknowledgments

- [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) for stealth browser automation
- Craigslist, SUPost, and Bay123 communities for housing platforms
- SF crime data sources (SFPD, community reports)

## Contact

Issues and questions: [GitHub Issues](https://github.com/agentic-sciences/bayarea-housing-scraper/issues)
