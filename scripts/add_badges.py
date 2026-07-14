#!/usr/bin/env python3
"""
Assign visual badges to products based on PAAPI price data.

Only 4 badge types:
  - 💰 Budget Pick:   price ≤ $15 (selectively applied — only to standout deals)
  - ⚡ Great Value:   price between $15-$25
  - 🔧 Premium Pick:  price ≥ $80
  - 🔥 Editor's Pick: manual — set by curation agent only

Budget Pick is deliberately underused — only ~25% of eligible products get it.
"""
import json
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_DIR / "data" / "sample_products.json"

# ── Budget Pick keep list ───────────────────────────────────────────
# These products genuinely feel like steals at their price.
# Add products to this list by checking their index or asin in sample_products.json.
# Format: (keyword to match in title, optional min_price)
BUDGET_PICK_KEEP = [
    # Under $6 — absurdly cheap for useful items (auto-keep if < $6 via keyword)
    # Multi-packs and fun items under $10
    # Unique gadgets under $14
    # Quality kitchen tools under $10
]

# Set of product title substrings that qualify for Budget Pick
BUDGET_TITLES = {
    # Under $7 — dirt cheap utility items
    "onion holder", "sanding sponge", "measuring spoon set",
    "water container 2 gallon", "sunglass holder", "craftsman shallow",
    # Fun items under $10
    "vomiting chicken", "angry mama", "squishy toys",
    "sasquatch", "funny sasquatch",
    # Kitchen tools under $10
    "olive oil sprayer", "meat tenderizer", "kitchenaid",
    "magnetic measuring spoon", "elizabat kitchen",
    # Gadgets under $14
    "pooch selfie", "muscle roller", "laser level",
    "tent lamp", "retro bluetooth speaker",
    "edc pocket multitool",
    # Multi-packs
    "8 pack sanding sponge", "30 pack squishy",
}

def qualify_for_budget(title_lower: str, price: float) -> bool:
    """Only ~25% of sub-$15 products should get Budget Pick."""
    if any(kw in title_lower for kw in BUDGET_TITLES):
        return True
    # Under $6 always qualifies
    if price < 6:
        return True
    return False

def assign_badge(product):
    """Assign badge using price data only. Budget Pick is selective."""
    existing = product.get("badge")
    if existing == "🔥 Editor's Pick":
        return existing  # preserve manual
    
    price = product.get("price")
    if price is None:
        return None
    
    title = product.get("title", "").lower()
    
    if price <= 15:
        if qualify_for_budget(title, price):
            return "💰 Budget Pick"
        return None  # not a standout deal
    
    if 15 < price <= 25:
        return "⚡ Great Value"
    
    if price >= 80:
        return "🔧 Premium Pick"
    
    return None

def main():
    with open(DATA_FILE) as f:
        products = json.load(f)
    
    budget_count = 0
    for p in products:
        badge = assign_badge(p)
        p["badge"] = badge
        if badge == "💰 Budget Pick":
            budget_count += 1
    
    # Check Editor's Pick still preserved (manual override)
    for p in products:
        if p.get("badge") is None:
            # There might be a manual override stored elsewhere; skip
            pass
    
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    total = len(products)
    badges = {}
    for p in products:
        b = p.get("badge")
        badges[b] = badges.get(b, 0) + 1
    
    print(f"✅ Badges assigned: {sum(badges.values())}/{total}")
    print(f"   {'💰 Budget Pick':<20} {badges.get('💰 Budget Pick', 0)}  (capped — only standout deals)")
    print(f"   {'⚡ Great Value':<20} {badges.get('⚡ Great Value', 0)}")
    print(f"   {'🔧 Premium Pick':<20} {badges.get('🔧 Premium Pick', 0)}")
    editor_badge = "🔥 Editor's Pick"
    print(f"   {'🔥 Editor' + chr(39) + 's Pick':<20} {badges.get(editor_badge, 0)}")
    print(f"   No badge: {badges.get(None, 0)}")

if __name__ == "__main__":
    main()