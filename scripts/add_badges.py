#!/usr/bin/env python3
"""
Assign visual badges to existing products based on description heuristics.
Run once to add badges to all existing products, then the curation agent
assigns badges manually for new batches.

Usage:
    python3 scripts/add_badges.py
"""
import json, re, sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_DIR / "data" / "sample_products.json"

BADGE_RULES = [
    # (badge_text, keywords_any, min_keyword_matches)
    ("🏆 Award Winner", ["award-winning", "shark tank", "patented", "kickstarter", "award", "best in class"], 1),
    ("🔥 Editor's Pick", ["must-have", "don't miss", "standout", "top pick", "editor's choice", "fan favorite", "customer favorite", "favorite"], 1),
    ("⚡ Great Value", ["budget-friendly", "affordable", "great value", "worth every penny", "under $"], 1),
    ("💡 Unique Find", ["unique", "one-of-a-kind", "unusual", "rare", "like nothing else", "conversation starter", "genius", "clever"], 1),
    ("📦 Compact Design", ["compact", "space-saving", "ultra-portable", "fits in your", "tiny", "slim", "foldable", "collapsible"], 1),
    ("🎁 Perfect Gift", ["perfect gift", "great gift", "makes a great", "gift idea", "ideal for gifting", "everyone will love"], 1),
    ("⭐ Top Rated", ["top-rated", "highly rated", "bestseller", "popular", "best-selling", "most popular", "highly recommended"], 1),
    ("🔧 Premium Build", ["premium", "solid wood", "solid steel", "aircraft-grade", "military-grade", "pro-grade", "professional grade", "handcrafted", "artisan"], 1),
]

def assign_badge(product):
    """Assign a badge based on description text heuristics."""
    desc = (product.get("description", "") + " " + product.get("blurb", "")).lower()
    title = product.get("title", "").lower()
    text = desc + " " + title
    
    for badge_text, keywords, min_matches in BADGE_RULES:
        matches = sum(1 for kw in keywords if kw in text)
        if matches >= min_matches:
            return badge_text
    
    return None

def main():
    with open(DATA_FILE) as f:
        products = json.load(f)
    
    assigned = 0
    for p in products:
        badge = assign_badge(p)
        if badge:
            p["badge"] = badge
            assigned += 1
        else:
            p["badge"] = None  # explicitly set to None so it's a known field
    
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Assigned badges to {assigned}/{len(products)} products")
    print(f"   Products without badges: {len(products) - assigned}")

if __name__ == "__main__":
    main()