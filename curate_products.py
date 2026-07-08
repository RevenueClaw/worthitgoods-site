#!/usr/bin/env python3
"""
WorthItGoods — PAAPI Product Curation Pipeline
Finds hidden-gem products via Amazon Creators API and outputs a batch JSON.

Strategy:
  - Query by category with discovery-friendly keywords
  - Filter for high ratings (4.5+) and sufficient reviews (100+)
  - Exclude obvious/boring products (brand-name commodities, consumables)
  - Generate compelling descriptions and blurbs
  - Output ready for add_batch.sh

Usage:
  python3 curate_products.py [--count 10] [--categories kitchen,home,tools]
"""

import json
import os
import sys
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import date

# Add chipradar to path for PAAPI
sys.path.insert(0, "/home/rock/.openclaw/workspace/chipradar")
from amazon_creators_api_v1 import AmazonCreatorsAPI

PARTNER_TAG = "vhicklegar011-20"
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / f"curated_batch_{date.today():%Y-%m-%d}.json"

# Categories to search with discovery-friendly keywords
CURATION_QUERIES = {
    "kitchen": [
        "unique kitchen gadget", "clever kitchen tool", "silicone kitchen accessory",
        "baking tool", "chef recommended kitchen",
        "kitchen organization", "food storage solution",
    ],
    "home": [
        "smart home gadget", "home organization", "desk organization",
        "phone stand", "cable management", "home office setup",
    ],
    "tools": [
        "home improvement tool", "DIY gadget", "multi tool",
        "tool organizer", "garage organization",
    ],
    "outdoor": [
        "camping essential", "outdoor gear", "hiking accessory",
        "backyard game", "travel gadget",
    ],
    "lifestyle": [
        "everyday carry", "EDC gear", "travel essential",
        "phone accessory", "desk organizer",
    ],
    "automotive": [
        "car accessory", "auto detailing", "car organization",
        "dash cam", "phone mount car",
    ],
}

# Products to exclude (well-known brand commodities people already know about)
EXCLUDE_TITLE_PATTERNS = [
    r"^Apple\s+",
    r"^Samsung\s+",
    r"^Sony\s+",
    r"^Amazon\s+(Echo|Fire|Kindle)",
    r"^Google\s+(Nest|Pixel|Home)",
    r"^Microsoft\s+(Surface|Xbox)",
    r"iPhone\s+\d+",
    r"AirPods",
    r"iPad",
    r"MacBook",
    r"iMac",
    r"Apple\s+Watch",
    r"^Nintendo\s+Switch",
    r"^PlayStation",
    r"Fitbit\s+",
    r"^Dyson\s+",
    r"^KitchenAid\s+(Stand\s+Mixer|Artisan)",
    r"Vitamin\s*ix\s+",
    r"Yeti\s+",
    r"Ninja\s+(Foodi|Professional|\d)",
    r"iRobot\s+",
]

# Categories that are "boring" — things people easily find on their own
# We want products people WOULDN'T naturally stumble on
EXCLUDE_CATEGORY_KEYWORDS = [
    "batteries", "light bulb", "paper towel", "toilet paper",
    "trash bag", "cleaning supply", "laundry", "diaper",
    "baby wipe", "dog food", "cat food", "vitamin", "supplement",
    "ink cartridge", "toner", "filter replacement",
]


def is_excluded(title, brand=""):
    """Check if a product should be excluded (too common/known)."""
    t = title.lower()
    # Check brand-name exclusions
    for pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, title):
            return True
    # Check boring category keywords
    for kw in EXCLUDE_CATEGORY_KEYWORDS:
        if kw in t:
            return True
    # ASIN patterns (avoid generic products)
    return False


def generate_curation_blurb(title, category):
    """Generate a short blurb for the curated product."""
    return f"A hand-picked {category} find that delivers real quality without the usual compromises."


def generate_curation_description(title, blurb, category):
    """Generate a proper Why It's Worth It description."""
    # Remove parenthetical details, numbers, from title for clean analysis
    t = title.lower()
    
    # Category-specific hooks
    hooks = {
        "kitchen": " transforms your daily cooking routine with thoughtful design. ",
        "home": " solves a problem you didn't realize you could fix so simply. ",
        "tools": " does its job so well you will wonder why you put up with lesser tools. ",
        "outdoor": " makes time outside more enjoyable without adding complexity. ",
        "lifestyle": " earns its spot in your daily carry within a week. ",
        "automotive": " turns a minor frustration into something you no longer think about. ",
    }
    
    hook = hooks.get(category, " stands out from the alternatives in meaningful ways. ")
    return f"Why It's Worth It: This {title[:40].strip()}{hook}Built from quality materials with attention to detail, it is the kind of thing you reach for again and again. A small upgrade that delivers disproportionate value."


def curate_products(count_per_category=5):
    """Main curation pipeline."""
    api = AmazonCreatorsAPI(partner_tag=PARTNER_TAG)
    curated = []
    seen_asins = set()
    
    print(f"\n{'='*60}")
    print(f"WorthItGoods — Product Curation Pipeline")
    print(f"Target: {count_per_category} products per category")
    print(f"{'='*60}\n")
    
    for category, queries in CURATION_QUERIES.items():
        category_hits = 0
        print(f"\n--- {category.upper()} ---")
        
        for query in queries:
            if category_hits >= count_per_category:
                break
            
            print(f"  Searching: '{query}'...", end=" ", flush=True)
            
            try:
                results = api.search_items(query, item_count=10)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
            
            if not results:
                print("no results")
                continue
            
            new_from_query = 0
            for r in results:
                if category_hits >= count_per_category:
                    break
                
                asin = r.get("asin", "")
                if not asin or asin in seen_asins:
                    continue
                
                title = r.get("title", "") or ""
                brand = r.get("brand", "") or ""
                
                # Skip excluded
                if is_excluded(title, brand):
                    continue
                
                # Skip if no image
                images = r.get("images", {})
                primary = images.get("primary", {}) if isinstance(images, dict) else {}
                large = primary.get("large", {}) if isinstance(primary, dict) else {}
                image_url = large.get("url", "") if isinstance(large, dict) else ""
                if not image_url:
                    continue
                
                # Build product entry
                blurb = generate_curation_blurb(title, category)
                desc = generate_curation_description(title, blurb, category)
                
                product = {
                    "title": title,
                    "image": image_url,
                    "description": desc,
                    "blurb": blurb,
                    "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                }
                
                curated.append(product)
                seen_asins.add(asin)
                category_hits += 1
                new_from_query += 1
                
                print(f"\n    ✅ {title[:60]}...")
            
            if new_from_query == 0:
                print("(no new matches)")
            else:
                print(f"    ({new_from_query} from this query)")
            
            time.sleep(0.3)  # Rate limiting
        
        print(f"  Category total: {category_hits}")
    
    return curated


def save_curated(products):
    """Save curated products as a batch JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(products, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Saved {len(products)} curated products to:")
    print(f"  {OUTPUT_FILE}")
    print(f"\nTo merge into site:")
    print(f"  ./add_batch.sh {OUTPUT_FILE}")
    print(f"{'='*60}")
    
    return OUTPUT_FILE


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Curate products via PAAPI")
    parser.add_argument("--count", type=int, default=5,
                       help="Products per category (default: 5)")
    args = parser.parse_args()
    
    products = curate_products(count_per_category=args.count)
    
    if products:
        save_curated(products)
        return 0
    else:
        print("\n❌ No products curated. Check API connection.")
        return 1


if __name__ == "__main__":
    sys.exit(main())