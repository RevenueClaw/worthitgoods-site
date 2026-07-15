#!/usr/bin/env python3
"""
Comparison Scout — scans the WorthItGoods catalog for new products,
identifies good "our pick vs competitor" matchups, and outputs a report.

Usage:
    python3 scripts/scout_comparisons.py            # Full scan, output report
    python3 scripts/scout_comparisons.py --quick    # Skip products already compared
    python3 scripts/scout_comparisons.py --report   # Just show existing report

Output: scripts/comparison_candidates.json (last run results)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPARISONS_DIR = os.path.join(REPO_DIR, "comparisons")
CANDIDATES_FILE = os.path.join(os.path.dirname(__file__), "comparison_candidates.json")

# Products already featured in comparison articles
USED_ASINS = {
    # From comparisons on disk
    "B00NCRE4GO",  # TENS 7000 (TENS vs Muscle Roller, TENS vs AUVON)
    "B0CB1D82NB",  # INIU 100W GaN Charger (vs 30W)
    "B0BZHZ56M9",  # UGREEN 30W Charger (vs 100W)
    "B07H7ZDBV4",  # Splatypus Jar Spatula (kitchen roundup)
    "B09P6HFCSP",  # Magnetic Measuring Spoons (kitchen roundup)
    "B0738C7RXF",  # Deiss PRO Zester (kitchen roundup)
    "B07VLBVQBP",  # Red the Crab (kitchen roundup)
    "B0B3CNJ3SQ",  # Swiss Army Knife (vs survival kit)
    "B0000CCY1Y",  # OXO Measuring Cups (kitchen roundup)
    "B004GF1OVY",  # Chemical Guys Clay Bar (vs Mothers)
    "B06XFY5NZW",  # Carhartt Lunchbox
    "B0DT41BHVF",  # Marble Salt Cellar
    "B0000CCY1Y",  # OXO Measuring Cups
    "B07RB2ZYMS",  # Meguiar's Wash and Wax
    "B07SHJVK4G",  # CERAKOTE Trim Coat
}

# Known competitor products with verified prices (from past API calls)
KNOWN_COMPETITORS = {
    "B085TL8TPJ": {"name": "AUVON Rechargeable TENS Unit", "price": 32.99, "type": "TENS unit", "category": "health"},
    "B07D58V8LD": {"name": "AUVON Dual Channel TENS", "price": 32.99, "type": "TENS unit", "category": "health"},
    "B0002U2V1Y": {"name": "Mothers California Gold Clay Bar Kit", "price": 22.55, "type": "clay bar", "category": "car care"},
    "B0CZ6LXL8R": {"name": "Anker Prime 100W GaN Charger", "price": 59.99, "type": "charger", "category": "electronics"},
}


def extract_asin(url):
    """Extract ASIN from an Amazon URL."""
    if not url:
        return None
    # /dp/ASIN format
    m = re.search(r'/dp/([A-Z0-9]{10})', url)
    if m:
        return m.group(1)
    # ASIN in other formats
    m = re.search(r'[A-Z0-9]{10}', url)
    if m and len(m.group(0)) == 10:
        return m.group(0)
    return None


def load_products():
    """Load products from the catalog."""
    products_path = os.path.join(REPO_DIR, "worthitgoods_products.json")
    sample_path = os.path.join(REPO_DIR, "data", "sample_products.json")
    
    products = []
    for path in [products_path, sample_path]:
        if os.path.exists(path):
            with open(path) as f:
                products.extend(json.load(f))
    
    return products


def get_existing_comparisons():
    """Get list of comparison filenames already on disk."""
    if not os.path.exists(COMPARISONS_DIR):
        return []
    return [f for f in os.listdir(COMPARISONS_DIR) if f.endswith('.html')]


def get_category_from_title(title):
    """Guess product category from title."""
    title_lower = title.lower()
    categories = {
        "kitchen": ["measuring", "spatula", "zester", "grater", "spoon", "utensil", 
                     "kitchen", "cooking", "baking", "cheese", "cutting", "knife",
                     "marble", "salt", "cellar", "splap", "splatypus"],
        "car care": ["chemical guys", "meguiar", "cerakote", "clay bar", "car care",
                      "automotive", "car wash", "wax", "detailing", "trim coat"],
        "electronics": ["charger", "gan", "usb c", "power", "battery", "cable",
                         "laptop", "phone", "tablet", "ipad", "projector"],
        "outdoor": ["camping", "lantern", "tent", "flashlight", "spotlight", "neck light",
                     "cooler", "lunchbox", "lunch", "carhartt", "survival", "tactical"],
        "health": ["tens", "muscle", "pain relief", "massage", "stimulator", "back pain"],
        "tools": ["laser", "level", "screwdriver", "tool", "pouch", "organizer"],
        "fitness": ["gym", "exercise", "workout", "resistance", "yoga", "fitness"],
        "home": ["lamp", "light", "decor", "clock", "organizer", "shelf", "storage"],
    }
    
    for category, keywords in categories.items():
        for kw in keywords:
            if kw in title_lower:
                return category
    return "other"


def find_competitors_for_product(asin, title, category):
    """Find known competitors for a product by matching category."""
    competitors = []
    
    # Check known competitors — match by category, not by 'against' field
    our_cat = category
    for comp_asin, comp_data in KNOWN_COMPETITORS.items():
        comp_cat = comp_data.get("category", "other")
        # Same category and not our own product
        if comp_cat == our_cat and comp_asin != asin:
            competitors.append({
                "asin": comp_asin,
                "name": comp_data["name"],
                "price": comp_data["price"],
                "price_verified": True,
                "type": comp_data["type"],
                "source": "known"
            })
    
    return competitors


def main():
    quick_mode = "--quick" in sys.argv
    report_only = "--report" in sys.argv
    
    products = load_products()
    existing = get_existing_comparisons()
    
    if report_only and os.path.exists(CANDIDATES_FILE):
        with open(CANDIDATES_FILE) as f:
            print(json.dumps(json.load(f), indent=2))
        return
    
    # Track which ASINs we've already used
    used_asins = set(USED_ASINS)
    
    # Process products
    candidates = []
    processed = 0
    
    for product in products:
        title = product.get("title") or product.get("name", "")
        url = product.get("url", "")
        asin = extract_asin(url)
        price = product.get("price")
        
        if not asin:
            continue
        
        if asin in used_asins and quick_mode:
            continue
        
        processed += 1
        category = get_category_from_title(title)
        
        competitors = find_competitors_for_product(asin, title, category)
        
        if competitors:
            candidates.append({
                "asin": asin,
                "title": title[:80],
                "price": price,
                "category": category,
                "competitors": competitors,
                "priority": "high" if competitors else "low",
                "url": url,
            })
    
    # Sort: high priority first, then by category
    candidates.sort(key=lambda c: (0 if c["priority"] == "high" else 1, c["category"]))
    
    # Build report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_products_scanned": len(products),
        "products_with_asins": processed,
        "products_already_compared": len(used_asins),
        "comparison_candidates": candidates,
        "existing_articles_on_disk": len(existing),
        "comparison_files": existing,
        "summary": {
            "top_candidates": [
                {
                    "product": c["title"][:60],
                    "category": c["category"],
                    "competitors": [comp["name"] for comp in c["competitors"]],
                    "total_competitors": len(c["competitors"]),
                }
                for c in candidates[:5]
            ]
        }
    }
    
    # Save
    with open(CANDIDATES_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"COMPARISON SCOUT REPORT")
    print(f"{'='*60}")
    print(f"Scanned:     {len(products)} products")
    print(f"With ASINs:  {processed}")
    print(f"Used:        {len(used_asins)} already compared")
    print(f"Candidates:  {len(candidates)} potential matchups")
    print(f"Articles:    {len(existing)} on disk")
    print(f"\nTop candidates:")
    for c in candidates[:5]:
        comp_names = ", ".join(comp["name"][:40] for comp in c["competitors"])
        print(f"  [{c['category']:12s}] {c['title'][:55]}")
        print(f"       → vs {comp_names}")
    print(f"\nFull report: {CANDIDATES_FILE}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()