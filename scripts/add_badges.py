#!/usr/bin/env python3
"""
Assign visual badges to products based on PAAPI data only.
NO text/keyword heuristics — those were wrong half the time.

Data-driven rules (checked first):
  - 💰 Budget Pick:   price ≤ $15
  - ⚡ Great Value:   price ≤ $25
  - 🔧 Premium Pick:  price ≥ $80
  - 🔥 Editor's Pick: manual — only set by curation agent in the JSON

Products without any qualifying badge get no badge.
"""
import json
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_DIR / "data" / "sample_products.json"

# Data-driven rules ONLY — no text scraping
DATA_RULES = [
    ("💰 Budget Pick", lambda p: p.get("price") is not None and p.get("price") <= 15),
    ("⚡ Great Value", lambda p: p.get("price") is not None and 15 < p.get("price") <= 25),
    ("🔧 Premium Pick", lambda p: p.get("price") is not None and p.get("price") >= 80),
]

# Editor's Pick is manual-only — set by curation agent, never auto-assigned
MANUAL_BADGES = {"🔥 Editor's Pick"}

def assign_badge(product):
    """Assign a badge using price data only."""
    existing = product.get("badge")
    if existing in MANUAL_BADGES:
        return existing  # preserve manual assignments
    
    for badge_text, check_fn in DATA_RULES:
        if check_fn(product):
            return badge_text
    
    return None

def main():
    with open(DATA_FILE) as f:
        products = json.load(f)
    
    assigned = 0
    data_based = 0
    manual_kept = 0
    for p in products:
        old_badge = p.get("badge")
        badge = assign_badge(p)
        if badge:
            p["badge"] = badge
            assigned += 1
            if badge in MANUAL_BADGES:
                manual_kept += 1
            else:
                data_based += 1
        else:
            p["badge"] = None
    
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Badges assigned: {assigned}/{len(products)}")
    print(f"   Price-based: {data_based}")
    print(f"   Manual (Editor's Pick): {manual_kept}")
    print(f"   No badge: {len(products) - assigned}")

if __name__ == "__main__":
    main()