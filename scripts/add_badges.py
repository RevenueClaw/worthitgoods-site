#!/usr/bin/env python3
"""
add_badges.py — Assign engaging, data-driven badges to existing products.
Replaces monotonous single-badge system with sparse, earned badges.

Badge types (at most one per product, priority order):
  1. "🎯 Hidden Gem"  — fun_score >= 0.70 AND has price (unique, clever products)
  2. "💰 Under $10"   — price <= $10 AND fun_score >= 0.45 (bargains worth noticing)

Only ~15% of products get badges. The rest stay clean — badges feel earned.

Usage:
  python3 scripts/add_badges.py                        # score + badge all products
  python3 scripts/add_badges.py --dry-run              # preview only
  python3 scripts/add_badges.py data/curated_batch_*.json  # badge a specific batch
"""

import json, re, sys, os
from pathlib import Path

# ── fun_score function (mirrors curate_products.py) ──────────────────────────
FUN_KEYWORDS = [
    "innovative","patented","unique","award","genius","clever","ingenious",
    "unusual","creative","one-of-a-kind","conversation","novel","original",
    "multifunctional","2-in-1","3-in-1","multi-functional",
    "titanium","premium","handmade","artisan","compact","portable",
    "transforms","converts","folds","collapsible","solar","rechargeable",
    "bamboo","ceramic","copper","solid wood","leather","magnetic","glass",
    "stainless","retro","vintage","modern","minimalist",
    "DIY","kit","build","assemble","custom","modular","adjustable",
    "universal","compatible","smart","app","bluetooth","LED","sensor",
    "award-winning","as seen on","shark tank","dragon's den","kickstarter","indiegogo",
    "solid wood","walnut","oak","maple","aluminum","brass","copper",
    "silicone","carbon fiber","marble","stone","resin","wool","canvas",
    "patented","mechanical","analog","gear","spring","tension","magnet",
    "suction","portable","folding","collapsible","magnetic",
    "heirloom","generation","built to last","lifetime","timeless",
    "classic","throwback","nostalgic","retro design","heritage",
    "creative","imaginative","whimsical","playful","fun","delight",
    "surprising","unexpected","charming",
    "viral","tiktok","instagram","must-have","mind-blowing","life-changing",
    "game-changer","hilarious","funny","weird","bizarre","fascinating",
    "jaw-dropping","addictive","satisfying","oddly satisfying",
    "head-turning","eye-catching","showstopper","wow factor",
    "you need this","never knew you needed","life hack","genius design",
    "not your average","reimagined","reinvented",
]

FUN_BORING_PATTERNS = [
    r"basic",r"standard",r"ordinary",r"plain",r"simple",r"generic",
    r"replacement",r"refill",r"bulk",r"value pack",r"economy",
    r"set of \d",r"pack of \d",r"\d+ pack",r"combo pack",r"variety pack",
]


def fun_score(title, brand=""):
    t = title.lower()
    score = 0.3
    for kw in FUN_KEYWORDS:
        if kw in t:
            score += 0.12
    for pat in FUN_BORING_PATTERNS:
        if re.search(pat, t):
            score -= 0.15
    if re.search(r"\b(patent|award|design|invention|shark tank|dragon|kickstarter|indiegogo|reddot|iF design|good design)\b", t, re.I):
        score += 0.30
    if re.search(r"\b(2-in-1|3-in-1|4-in-1|multi|universal|adjustable|folding|collapsible|rechargeable|solar)\b", t, re.I):
        score += 0.10
    if re.search(r"\b(titanium|bamboo|copper|solid wood|ceramic|leather|carbon fiber|marble|walnut|oak|brass|aluminum|wool|canvas)\b", t, re.I):
        score += 0.10
    if re.search(r"\b(kit|DIY|build|assemble|custom|maker|craft)\b", t, re.I):
        score += 0.08
    if re.search(r"\b(bluetooth|smart|app|sensor|LED|digital|eink|analog|mechanical)\b", t, re.I):
        score += 0.06
    if re.search(r"\b(retro|vintage|nostalgia|classic|modern|minimalist|unique)\b", t, re.I):
        score += 0.06
    if re.search(r"\b(heirloom|lifetime|timeless|heritage|generation)\b", t, re.I):
        score += 0.10
    if re.search(r"\b(whimsical|playful|delight|surprising|unexpected|charming)\b", t, re.I):
        score += 0.08
    if re.search(r"\b(shark tank|dragon's den|as seen on tv|kickstarter|indiegogo|funded)\b", t, re.I):
        score += 0.20
    return max(0.0, min(1.0, score))


def assign_badge(product):
    """Return (badge_string_or_None, was_updated_bool)."""
    price = product.get('price')
    score = product.get('_fun_score', 0)
    
    # Recompute fun_score if not set
    if score == 0:
        score = fun_score(product.get('title', ''))
        product['_fun_score'] = round(score, 2)
    
    # Priority 1: Hidden Gem — clever, unique, well-designed products
    if score >= 0.70 and price is not None:
        old = product.get('badge')
        product['badge'] = '🎯 Hidden Gem'
        return ('🎯 Hidden Gem', old != '🎯 Hidden Gem')
    
    # Priority 2: Under $10 — bargains that aren't boring
    if price is not None and price <= 10 and score >= 0.45:
        old = product.get('badge')
        product['badge'] = '💰 Under $10'
        return ('💰 Under $10', old != '💰 Under $10')
    
    # No badge qualifies — clear any existing badge
    if product.get('badge'):
        product.pop('badge', None)
        return (None, True)
    
    return (None, False)


def process_products(products):
    """Score and badge a list of products. Modifies in place."""
    stats = {'total': len(products), 'hidden_gem': 0, 'under_10': 0, 'cleared': 0, 'unchanged': 0}
    
    for p in products:
        badge, changed = assign_badge(p)
        if badge == '🎯 Hidden Gem':
            stats['hidden_gem'] += 1
        elif badge == '💰 Under $10':
            stats['under_10'] += 1
        elif changed:
            stats['cleared'] += 1
        else:
            stats['unchanged'] += 1
    
    return stats


def main():
    dry_run = '--dry-run' in sys.argv
    
    # Determine target: specific batch file or the main product DB
    files = [a for a in sys.argv[1:] if a.endswith('.json') and a != '--dry-run']
    
    if files:
        targets = files
    else:
        repo = Path(__file__).resolve().parent.parent
        targets = [str(repo / 'data' / 'sample_products.json')]
    
    for fpath in targets:
        with open(fpath) as f:
            products = json.load(f)
        
        stats = process_products(products)
        
        badged = stats['hidden_gem'] + stats['under_10']
        pct = badged / max(stats['total'], 1) * 100
        
        print(f"\n{fpath}")
        print(f"  Total: {stats['total']} products")
        print(f"  🎯 Hidden Gems: {stats['hidden_gem']}")
        print(f"  💰 Under $10:   {stats['under_10']}")
        print(f"  Badged: {badged} ({pct:.0f}%)")
        print(f"  Clean:  {stats['unchanged'] + stats['cleared']}")
        
        if stats['hidden_gem'] > 0:
            print(f"\n  Hidden Gems:")
            for p in products:
                if p.get('badge') == '🎯 Hidden Gem':
                    print(f"    [{p['_fun_score']:.2f}] ${p.get('price','?')} — {p['title'][:65]}")
        
        if not dry_run:
            with open(fpath, 'w') as f:
                json.dump(products, f, indent=2)
            print(f"  ✅ Saved")
        else:
            print(f"  (dry run — not saved)")


if __name__ == '__main__':
    main()