#!/usr/bin/env python3
"""
Comparison Scout v2 — scans the WorthItGoods catalog for products
that haven't been used in comparison articles yet.

Output: sorted list of potential candidates for the cron agent
to research, write, and schedule.

Usage:
    python3 scripts/scout_comparisons.py              # Full scan
    python3 scripts/scout_comparisons.py --report     # Show last results
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPARISONS_DIR = os.path.join(REPO_DIR, "comparisons")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATES_FILE = os.path.join(SCRIPTS_DIR, "comparison_candidates.json")

# Products already used in comparisons — ASINs extracted from articles + catalog
USED_ASINS = {
    "B00NCRE4GO",  # TENS 7000 (vs Muscle Roller, vs AUVON)
    "B0B3CNJ3SQ",  # Swiss Army Knife (vs Survival Kit)
    "B0CB1D82NB",  # INIU 100W GaN Charger (vs 30W)
    "B0BZHZ56M9",  # UGREEN 30W Charger (vs 100W)
    "B07H7ZDBV4",  # Splatypus Jar Spatula
    "B09P6HFCSP",  # Magnetic Measuring Spoons
    "B0738C7RXF",  # Deiss PRO Zester
    "B07VLBVQBP",  # Red the Crab Utensil Rest
    "B0000CCY1Y",  # OXO Measuring Cups
    "B004GF1OVY",  # Chemical Guys Clay Bar
    "B09M68SFL9",  # FLY2SKY Tent Lamp
    "B07WNRN9WQ",  # 80hr Neck Light
    "B0CL465G9L",  # Rechargeable Spotlight
}

# Keywords to skip — gag gifts, party supplies, seasonal items
SKIP_WORDS = [
    "dad", "fathers", "mothers", "birthday", "4th of july", "patriotic",
    "american flag", "funny ", "gag gift", "novelty", "t-shirt", "coasters",
    "coffee mug", "cat socks", "dog bandana", "squishy", "bubble bottle",
    "dinosaur", "costume", "windsock", "jigsaw puzzle", "porch goose",
    "crocs", "burrito blanket", "car registration", "license plate",
    "beef tallow", "soap bar", "sanding sponge", "dryer vent",
    "trunk organizer", "dog camera", "selfie", "dog toy",
]

CATEGORIES = {
    "kitchen": ["kitchen", "measur", "spatula", "zester", "grater",
                "spoon", "utensil", "cutting", "knife", "cheese",
                "olive oil", "egg separator", "onion", "salt cellar",
                "cookie", "bowl", "tenderizer", "freezer mold",
                "cooking", "baking", "grill", "bbq"],
    "car care": ["clay bar", "car care", "automotive", "car wash", "wax",
                 "detailing", "trim coat", "jump", "car emergency",
                 "ceramic coating", "microfiber"],
    "electronics": ["charger", "usb c", "gan", "bluetooth", "projector",
                    "keyboard", "raspberry pi", "smart plug", "lamp",
                    "apple watch", "garmin", "power bank", "cable",
                    "phone", "tablet", "speaker", "earbuds"],
    "outdoor": ["lantern", "flashlight", "camping", "tent", "cooler",
                "lunch", "water jug", "hammock", "spotlight", "neck light",
                "survival", "paddle board", "backpack"],
    "health": ["tens", "pain relief", "massager", "muscle", "back pain",
               "first aid", "insect repellent", "mosquito"],
    "tools": ["laser level", "screwdriver", "tool", "multitool",
              "measuring tape", "caulking", "borescope", "charger"],
    "home": ["air purifier", "smart plug", "shelf", "organizer",
             "docking station", "clock", "vase", "blanket", "table lamp"],
}


def extract_asin(url):
    if not url:
        return None
    m = re.search(r'/dp/([A-Z0-9]{10})', url)
    if m:
        return m.group(1)
    m = re.search(r'[A-Z0-9]{10}', url)
    if m and len(m.group(0)) == 10:
        return m.group(0)
    return None


def load_products():
    products = []
    for path in [
        os.path.join(REPO_DIR, "worthitgoods_products.json"),
        os.path.join(REPO_DIR, "data", "sample_products.json"),
    ]:
        if os.path.exists(path):
            with open(path) as f:
                products.extend(json.load(f))
    return products


def get_category(title):
    t = (title or "").lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in t:
                return cat
    return None  # No matching category


def should_skip(title):
    t = (title or "").lower()
    for word in SKIP_WORDS:
        if word in t:
            return True
    return False


def main():
    products = load_products()
    seen_asins = set()
    
    candidates_by_category = {}
    
    for product in products:
        title = product.get("title") or product.get("name", "")
        if not title:
            continue
        
        url = product.get("url", "")
        asin = extract_asin(url)
        
        if not asin or asin in seen_asins or asin in USED_ASINS:
            continue
        
        if should_skip(title):
            continue
        
        seen_asins.add(asin)
        category = get_category(title)
        
        if not category:
            continue  # Only include categorized products
        
        candidate = {
            "asin": asin,
            "title": title.strip()[:120],
            "price": product.get("price"),
            "category": category,
            "url": url if url else f"https://www.amazon.com/dp/{asin}?tag=worthitgoods-20",
        }
        
        candidates_by_category.setdefault(category, []).append(candidate)
    
    # Build flat list sorted by category
    ordered_cats = ["kitchen", "car care", "electronics", "outdoor", "health", "tools", "home"]
    flat_candidates = []
    for cat in ordered_cats:
        for c in candidates_by_category.get(cat, []):
            flat_candidates.append(c)
    
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report": {
            "total_products": len(products),
            "unique_asins_found": len(seen_asins) + len(USED_ASINS),
            "already_compared": len(USED_ASINS),
            "remaining_candidates": len(flat_candidates),
            "by_category": {cat: len(candidates_by_category.get(cat, [])) for cat in ordered_cats},
        },
        "candidates": flat_candidates,
    }
    
    with open(CANDIDATES_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nComparison Scout v2")
    print(f"{'='*50}")
    print(f"Already compared:  {len(USED_ASINS)} products")
    print(f"Available:         {len(flat_candidates)} candidates by category:")
    for cat in ordered_cats:
        count = len(candidates_by_category.get(cat, []))
        if count > 0:
            print(f"  {cat:15s}: {count}")
    print(f"\nAgent will: pick one → search web for competitors")
    print(f"→ verify via Amazon API → write article → schedule publish")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
