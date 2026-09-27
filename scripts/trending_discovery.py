#!/usr/bin/env python3
"""
Trending Topic Discovery — feeds real-world trends into the curation pipeline.

Fetches trending gadget/product ideas from web sources and outputs
a JSON file of PAAPI search queries for the week's curation run.

Sources:
  - web_search for "best gadgets 2026" style articles
  - Product Hunt's current featured products
  - Pre-defined seasonal/timely angles (fall, holiday, etc.)

Output: data/trending_queries_YYYY-MM-DD.json
  Format: { "category_name": ["search query", ...], ... }

This gets consumed by curate_products.py Phase 0 (LLM query generation)
or merged directly into the FUN_QUERIES pool.

Usage:
    python3 scripts/trending_discovery.py           # fetch + generate queries
    python3 scripts/trending_discovery.py --dry-run # show what it'd do
    python3 scripts/trending_discovery.py --cron    # quiet, auto-save
"""

import json, os, sys, urllib.request, urllib.error, re, time
from pathlib import Path
from datetime import date

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR.parent / 'data'

# Seasonal themes with relevant search queries
SEASONAL_THEMES = {
    "spring": {
        "months": [3, 4, 5],
        "queries": ["gardening gadget unique", "spring cleaning tool clever",
                     "outdoor entertaining gadget", "patio accessory cool"]
    },
    "summer": {
        "months": [6, 7, 8],
        "queries": ["summer travel gadget", "camping essential unique",
                     "BBQ grilling tool", "beach accessory clever", "outdoor game fun"]
    },
    "fall": {
        "months": [9, 10, 11],
        "queries": ["fall home decor unique", "cozy gadget gift",
                     "halloween decor creative", "indoor hobby gadget"]
    },
    "winter": {
        "months": [12, 1, 2],
        "queries": ["winter travel gadget", "indoor activity kit",
                     "holiday gift unique", "cold weather essential creative"]
    },
}

# Pre-defined trending queries that rotate by week number
WEEKLY_ANGLES = [
    "desk organization clever", "home office gadget mini",
    "cable management solution", "phone stand wireless charger",
    "keychain tool useful", "pocket gadget premium",
    "travel adapter compact", "packing cube set",
    "bathroom storage clever", "shower speaker waterproof",
    "coffee gadget unique", "tea lover accessory",
    "phone camera lens kit", "mini tripod phone",
    "notebook premium leather", "pen set gift unique",
    "stress relief gadget desk", "fidget toy adult",
    "plant pot self watering", "succulent terrarium kit",
    "pet travel accessory", "dog treat dispenser",
    "car phone mount magnetic", "car trash can",
    "home safe lock box", "security camera indoor mini",
    "snow removal tool", "winter car emergency kit",
    "home gym small gadget", "resistance band set door",
    "baby gadget useful", "kid travel activity",
]


def get_seasonal_queries():
    """Return seasonal queries based on current month."""
    now = date.today()
    month = now.month
    for season, info in SEASONAL_THEMES.items():
        if month in info["months"]:
            print(f"  Seasonal ({season}): {len(info['queries'])} queries")
            return info["queries"]
    return []


def get_weekly_queries():
    """Return a rotating subset of weekly queries based on week number."""
    week = date.today().isocalendar()[1]
    # Pick 5 queries based on week number (changes weekly)
    idx = (week * 3) % len(WEEKLY_ANGLES)
    selected = WEEKLY_ANGLES[idx:idx+5]
    if len(selected) < 5:
        selected += WEEKLY_ANGLES[:5-len(selected)]
    print(f"  Weekly rotation (week {week}): {len(selected)} queries")
    return selected


def fetch_product_hunt_trending():
    """Fetch trending products from Product Hunt's public page.
    
    This is a lightweight HTML scrape of their front page.
    Falls back gracefully if Product Hunt is unreachable.
    Returns list of product names for use as search seeds.
    """
    url = "https://api.producthunt.com/v1/posts?sort_by=votes_count&order=desc&per_page=5"
    # Note: Product Hunt v1 API is public-read; no key needed for basic listing
    products = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        for post in data.get("posts", []):
            name = post.get("name", "")
            tagline = post.get("tagline", "")
            if name:
                products.append(name)
                # Generate Amazon-friendly search query from product name
                print(f"  🌐 Product Hunt: {name} — {tagline[:60]}")
        return products
    except urllib.error.URLError:
        print(f"  🌐 Product Hunt: unreachable (using static queries)")
        return []
    except json.JSONDecodeError:
        print(f"  🌐 Product Hunt: bad response (using static queries)")
        return []
    except Exception as e:
        print(f"  🌐 Product Hunt: {type(e).__name__}: {e}")
        return []


def generate_query_from_product_name(name):
    """Turn a Product Hunt product name into an Amazon-friendly search query."""
    # Clean the name: lowercase, remove special chars
    name = name.strip()
    # Remove common prefixes/suffixes
    name = re.sub(r'^\d+\s*\.?\s*', '', name)
    name = re.sub(r'\s*[-–—|]\s*.*$', '', name)
    # Keep it short (3-5 words max)
    words = name.split()[:4]
    if len(words) <= 2:
        return f"{' '.join(words)} gadget"
    return ' '.join(words)


def save_output(all_queries):
    """Save discovered queries to a dated file for the curation pipeline."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "date": date.today().isoformat(),
        "seasonal": get_seasonal_queries(),
        "weekly": get_weekly_queries(),
        "product_hunt": [],
    }
    output.update(all_queries)
    
    path = OUTPUT_DIR / f"trending_queries_{date.today()}.json"
    with open(path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved to {path}")
    return path


def main():
    dry_run = '--dry-run' in sys.argv
    quiet = '--cron' in sys.argv or dry_run
    
    print(f"\n{'='*45}")
    print(f" Trending Topic Discovery — {date.today()}")
    print(f"{'='*45}")
    
    all_queries = {}
    total = 0
    
    # 1. Seasonal queries
    seasonal = get_seasonal_queries()
    if seasonal:
        all_queries["seasonal"] = seasonal
        total += len(seasonal)
    
    # 2. Weekly rotation
    weekly = get_weekly_queries()
    if weekly:
        all_queries["weekly_angles"] = weekly
        total += len(weekly)
    
    # 3. Product Hunt trending
    ph_products = fetch_product_hunt_trending() if not dry_run else []
    if ph_products:
        ph_queries = [generate_query_from_product_name(name) for name in ph_products]
        all_queries["product_hunt"] = ph_queries
        total += len(ph_queries)
        
        if not quiet:
            print(f"\n  Generated Amazon queries:")
            for q in ph_queries:
                print(f"    🔍 {q}")
    
    print(f"\n  Total: {total} trending queries across {len(all_queries)} sources")
    
    if dry_run:
        print(f"  (dry run — use --cron to save)")
        return 0
    
    path = save_output(all_queries)
    print(f"  ✅ Trending topics ready for tonight's curation run")
    return 0


if __name__ == '__main__':
    sys.exit(main())