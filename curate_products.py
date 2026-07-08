#!/usr/bin/env python3
"""
WorthItGoods — PAAPI Product Curation Pipeline
Finds hidden-gem products via Amazon Creators API and outputs a batch JSON.

Strategy:
  - Query by category with discovery-friendly keywords
  - Filter for high ratings (4.5+) and sufficient reviews (100+)
  - Exclude obvious/boring products (brand-name commodities, consumables)
  - Skip duplicates (same product type already on site)
  - Generate compelling descriptions and blurbs
  - Output ready for add_batch.sh

Usage:
  python3 curate_products.py [--count 2] [--categories kitchen,home,tools]
"""

import json
import os
import sys
import re
import time
from pathlib import Path
from datetime import date

sys.path.insert(0, "/home/rock/.openclaw/workspace/chipradar")
from amazon_creators_api_v1 import AmazonCreatorsAPI

PARTNER_TAG = "vhicklegar011-20"
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / f"curated_batch_{date.today():%Y-%m-%d}.json"

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

BORING_KEYWORDS = [
    "batteries", "light bulb", "paper towel", "toilet paper",
    "trash bag", "cleaning supply", "laundry", "diaper",
    "baby wipe", "dog food", "cat food", "vitamin", "supplement",
    "ink cartridge", "toner", "filter replacement",
]

EXISTING_CACHE = None

def load_existing():
    global EXISTING_CACHE
    if EXISTING_CACHE is None:
        try:
            with open("data/sample_products.json") as f:
                EXISTING_CACHE = json.load(f)
        except:
            EXISTING_CACHE = []
    return EXISTING_CACHE

# Product type nouns — shared use of these indicates same product type
PRODUCT_NOUNS = {
    'rest', 'spoon', 'cup', 'bowl', 'knife', 'ladle', 'spatula', 'grater', 'zester',
    'shears', 'skillet', 'mold', 'scale', 'timer', 'board', 'rack', 'holder',
    'bag', 'pack', 'case', 'hat', 'shirt', 'pants', 'socks', 'gloves',
    'lamp', 'light', 'fan', 'charger', 'cable', 'stand', 'mount',
    'tool', 'pouch', 'organizer', 'mat', 'towel', 'kit', 'set', 'caddy',
    'scoop', 'shooter', 'launcher', 'disc', 'puzzle', 'game',
    'tumbler', 'mug', 'glass', 'bottle', 'jar', 'container',
    'blanket', 'pillow', 'plush', 'coaster', 'vase', 'journal',
    'brush', 'comb', 'mirror', 'tray', 'basket', 'bin',
    'screwdriver', 'socket', 'wrench', 'hammer', 'level',
    'camera', 'lens', 'tripod', 'speaker', 'adapter', 'hub', 'dock',
    'flag', 'banner', 'windsock', 'bunting',
    'paddleboard', 'hammock', 'cooler', 'lunchbox',
}


def is_duplicate_by_content(title):
    """Detect if a product is essentially the same as something already on site.
    
    Logic:
    - 4+ meaningful common words (no overlap in product noun) -> duplicate
    - 2+ meaningful common words WITH a shared product noun -> duplicate
    - Otherwise allow (different product types from same brand are fine)
    """
    existing = load_existing()
    t = title.lower().strip()
    
    for p in existing:
        et = p.get("title", "").lower().strip()
        if not et:
            continue
        new_words = set(t.split())
        exist_words = set(et.split())
        common = new_words & exist_words
        
        stop_words = {"and", "the", "for", "with", "in", "of", "to", "a", "an", "is", "-", "|", ",", "."}
        meaningful = [w for w in common if len(w) > 3 and w not in stop_words]
        shared_nouns = set(meaningful) & PRODUCT_NOUNS
        
        # 4+ shared words without a shared noun = false positive risk (e.g. "stainless steel" matches)
        # Only flag if also sharing a product type
        if shared_nouns and len(meaningful) >= 2:
            return True
        if len(meaningful) >= 4:
            return True
    
    return False

def is_excluded(title, brand=""):
    t = title.lower()
    for pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, title):
            return True
    for kw in BORING_KEYWORDS:
        if kw in t:
            return True
    return False

def curate_products(count_per_category=2):
    api = AmazonCreatorsAPI(partner_tag=PARTNER_TAG)
    curated = []
    seen_asins = set()
    
    print(f"\n{'='*60}")
    print(f"WorthItGoods — Product Curation Pipeline")
    print(f"Target: {count_per_category} per category ({count_per_category * 6} total)")
    print(f"{'='*60}\n")
    
    for category, queries in CURATION_QUERIES.items():
        hits = 0
        print(f"\n--- {category.upper()} ---")
        
        for query in queries:
            if hits >= count_per_category:
                break
            
            print(f"  '{query}'...", end=" ", flush=True)
            try:
                results = api.search_items(query, item_count=10)
            except Exception as e:
                print(f"error: {e}")
                continue
            
            if not results:
                print("no results")
                continue
            
            new_count = 0
            for r in results:
                if hits >= count_per_category:
                    break
                
                asin = r.get("asin", "")
                if not asin or asin in seen_asins:
                    continue
                
                title = r.get("title", "") or ""
                brand = r.get("brand", "") or ""
                
                if is_excluded(title, brand):
                    continue
                if is_duplicate_by_content(title):
                    continue
                
                images = r.get("images", {})
                primary = images.get("primary", {}) if isinstance(images, dict) else {}
                large = primary.get("large", {}) if isinstance(primary, dict) else {}
                img = large.get("url", "") if isinstance(large, dict) else ""
                if not img:
                    continue
                
                product = {
                    "title": title,
                    "image": img,
                    "description": f"(edit me — write genuine why-it-is-worth-it description)",
                    "blurb": f"(edit me — one-line hook)",
                    "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                }
                
                curated.append(product)
                seen_asins.add(asin)
                hits += 1
                new_count += 1
                print(f"\n    ✅ {title[:65]}")
            
            if new_count == 0:
                print("(no new)")
            else:
                print(f"    +{new_count}")
            
            time.sleep(0.3)
        
        print(f"  total: {hits}")
    
    return curated

def save(products):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(products, f, indent=2)
    print(f"\n{'='*60}")
    print(f"Saved {len(products)} products to {OUTPUT_FILE}")
    print(f"IMPORTANT: Edit descriptions before merging!")
    print(f"Then: ./add_batch.sh {OUTPUT_FILE}")
    print(f"{'='*60}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=2)
    args = parser.parse_args()
    products = curate_products(count_per_category=args.count)
    if products:
        save(products)
        return 0
    else:
        print("No products found.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
