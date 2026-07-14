#!/usr/bin/env python3
"""
Assign visual badges to products based on PAAPI data (price, features)
and text heuristics. Runs at build time.

Data-driven rules (checked first):
  - ⚡ Great Value:   price <= 25 (available PAAPI data)
  - 💰 Budget Pick:   price <= 15
  - 🔧 Premium Build: price >= 80
  - 📦 Compact Design: features/description contain compact/portable/slim
  - 💡 Unique Find:    features/description contain unique/clever/rare

Text-only fallbacks:
  - 🏆 Award Winner: "award", "patented", "shark tank"
  - 🎁 Perfect Gift:  "gift"
  - ⭐ Top Rated:     "top-rated", "bestseller", etc.

Usage:
    python3 scripts/add_badges.py
"""
import json
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_DIR / "data" / "sample_products.json"

# ── Data-driven rules (checked first, uses actual PAAPI data) ─────────────
DATA_RULES = [
    ("💰 Budget Pick", lambda p, nf: p.get("price") is not None and p.get("price") <= 15),
    ("⚡ Great Value", lambda p, nf: p.get("price") is not None and 15 < p.get("price") <= 25),
    ("🔧 Premium Build", lambda p, nf: p.get("price") is not None and p.get("price") >= 80),
    ("📦 Compact Design", lambda p, nf: nf and any(kw in nf for kw in
        ["compact", "space-saving", "ultra-portable", "fits in", "tiny", "slim", "foldable", "collapsible", "mini", "small"])),
    ("💡 Unique Find", lambda p, nf: nf and any(kw in nf for kw in
        ["unique", "one-of-a-kind", "unusual", "rare", "conversation starter", "genius", "clever", "one of a kind", "creative", "novel"])),
]

# ── Text-only fallbacks (description heuristics, no PAAPI data needed) ─────
TEXT_RULES = [
    ("🏆 Award Winner", ["award-winning", "shark tank", "patented", "kickstarter", "award", "best in class", "winner"]),
    ("🔥 Editor's Pick", ["must-have", "don't miss", "standout", "top pick", "editor's choice", "fan favorite", "customer favorite"]),
    ("🎁 Perfect Gift", ["perfect gift", "great gift", "makes a great", "gift idea", "gift for"]),
    ("⭐ Top Rated", ["top-rated", "highly rated", "bestseller", "best-selling", "most popular"]),
]

def get_normalized_text(product):
    """Combine all text fields into one searchable string."""
    parts = []
    for field in ['title', 'description', 'blurb']:
        val = product.get(field, '')
        if val:
            parts.append(val.lower())
    features = product.get('features', [])
    if features:
        parts.append(' '.join(features).lower())
    return ' '.join(parts)

def assign_badge(product):
    """Assign a badge using price/features data first, then text fallback."""
    # Preserve manually assigned badges from curation agent
    existing = product.get("badge")
    if existing and existing not in (None, ""):
        return existing
    
    text = get_normalized_text(product)
    
    # Step 1: Data-driven rules
    for badge_text, check_fn in DATA_RULES:
        if check_fn(product, text):
            return badge_text
    
    # Step 2: Text-only fallback
    for badge_text, keywords in TEXT_RULES:
        if any(kw in text for kw in keywords):
            return badge_text
    
    return None

def main():
    with open(DATA_FILE) as f:
        products = json.load(f)
    
    assigned = 0
    data_based = 0
    for p in products:
        badge = assign_badge(p)
        if badge:
            p["badge"] = badge
            assigned += 1
            if any(badge == dr[0] for dr in DATA_RULES):
                data_based += 1
        else:
            p["badge"] = None
    
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Assigned badges to {assigned}/{len(products)} products")
    print(f"   Data-driven: {data_based} | Text-based: {assigned - data_based}")
    print(f"   No badge: {len(products) - assigned}")

if __name__ == "__main__":
    main()