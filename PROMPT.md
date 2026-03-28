# Task: Build a Bay Area Housing Scraper open-source repo

Create a clean, well-documented open source Python project that scrapes Bay Area housing listings from 3 platforms:
1. **Craigslist** (sfbay.craigslist.org) — apartments and rooms
2. **SUPost** (supost.com) — Stanford community marketplace  
3. **Bay123** (bay123.com) — Chinese community forum (Discuz-based)

## Architecture

The scraper uses **Patchright** (Playwright fork with stealth) because all 3 sites need JavaScript rendering. 

### Key Design from our working implementation:

**Craigslist:**
- Search URLs: `sfbay.craigslist.org/search/{area}/{category}` where area = sfc/pen/sby, category = apa/roo/sub
- Supports filters: `max_price`, `min_price`, `is_furnished`, `availabilityMode`
- Parse listings from search results page via JS evaluation
- Detail pages: parse title, price, address, body text, image count from HTML

**SUPost:**
- Search: `supost.com/search?query=...&category=housing`
- Links follow pattern: `/post/index/{id}`
- Filter for housing keywords (room, rent, bedroom, apartment, etc.)

**Bay123:**
- Forum pages: `bay123.com/forum-{id}-{page}.html` (40=主版, 158=整租, 165=短租)
- Thread pages: `bay123.com/thread-{tid}-1-1.html`
- Parse via `a.s.xst` CSS selector for thread titles
- Extract price from title text via regex `\$(\d[\d,]*)`

### Features to implement:
1. `scraper.py` — Main scraper with classes for each platform
2. `filter.py` — Filter results by: area, price range, furnished, short-term
3. `safety.py` — Neighborhood safety scoring for SF neighborhoods
4. CLI interface with argparse
5. JSON output with deduplication
6. Rate limiting and error handling
7. Good README with usage examples

### SF Neighborhood Safety Data (hardcoded):
```
5/5: Sunset, Noe Valley, Bernal Heights, Marina, Pacific Heights, Presidio, West Portal, Forest Hill
4/5: Richmond, Upper Haight, Alamo Square, Daly City, Castro, Nob Hill (upper), Ingleside
3/5: SOMA, Mission (Valencia corridor), North Beach, Portola, Excelsior
2/5: Tenderloin adjacent areas
1/5: Tenderloin core, 6th Street corridor
```

### File structure:
```
bayarea-housing-scraper/
├── README.md
├── LICENSE (MIT)
├── setup.py or pyproject.toml
├── requirements.txt
├── bayarea_housing/
│   ├── __init__.py
│   ├── scraper.py      # Main scraper classes
│   ├── platforms/
│   │   ├── __init__.py
│   │   ├── craigslist.py
│   │   ├── supost.py
│   │   └── bay123.py
│   ├── filter.py       # Filtering logic
│   ├── safety.py       # Neighborhood safety ratings
│   └── cli.py          # CLI entry point
├── examples/
│   └── basic_search.py
└── .gitignore
```

### IMPORTANT:
- NO server names, IP addresses, SSH keys, passwords, or personal info
- NO references to "research3", "Tencent Cloud", "Cornell", or any specific infrastructure
- The tool should work for anyone with patchright installed
- Use English for code/docs, but mention Chinese community platforms in README
- Add user-agent rotation
- Add respectful rate limiting (1-2 sec between requests)
- Make it pip-installable

### README should cover:
- What it does (3 platforms, why patchright)
- Installation
- Quick start CLI examples
- Python API examples
- Platform-specific notes (CL filters, Bay123 forum IDs, SUPost)
- Safety scoring explanation
- Contributing guide
- Disclaimer about scraping ethics/ToS

Write all files now. Make it production quality.
