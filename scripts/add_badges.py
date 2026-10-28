#!/usr/bin/env python3
"""
add_badges.py — Assign varied, data-driven badges to products.
5 badge types from independent data dimensions (at most ONE per product):
  1. Hidden Gem     — design novelty (fun_score >= 0.75)
  2. Gift Pick      — giftability (gift keywords + solid fun_score)
  3. Premium Design — high price + standout design (price > $50, fun >= 0.70)
  4. Problem Solver — practical utility (utility keywords + solid fun_score)
  5. Best Value     — low price + good design (price <= $15, fun >= 0.50)

Target: ~12-15% badged. Priority order prevents overlap.
"""

import json, re, sys
from pathlib import Path
from collections import Counter


FUN_KEYWORDS = [
    "innovative","patented","unique","award","genius","clever","ingenious",
    "unusual","creative","one-of-a-kind","conversation","novel","original",
    "multifunctional","2-in-1","3-in-1","multi-functional",
    "titanium","premium","handmade","artisan","compact","portable",
    "transforms","converts","folds","collapsible","solar","rechargeable",
    "bamboo","ceramic","copper","solid wood","leather","magnetic",
    "retro","vintage","modern","minimalist",
    "DIY","kit","build","assemble","custom","modular","adjustable",
    "bluetooth","smart","app","LED","sensor",
    "award-winning","as seen on","shark tank","kickstarter",
    "viral","tiktok","instagram","mind-blowing","hilarious","funny","weird","bizarre",
    "fascinating","satisfying","oddly satisfying",
    "head-turning","eye-catching","showstopper","wow factor",
    "never knew you needed","life hack","genius design",
    "not your average","reimagined","reinvented",
]

GIFT_KEYWORDS = [
    "gift","present","stocking stuffer","birthday","christmas","holiday",
    "valentine","fathers day","mothers day","anniversary","graduation",
    "secret santa","white elephant","housewarming","giftable","gift for",
    "gifts for","present for","dad gift","mom gift","boyfriend gift",
    "girlfriend gift","husband gift","wife gift","gift idea",
]

UTILITY_KEYWORDS = [
    "saves","solves","eliminates","prevents","stops","relieves",
    "reduces","fixes","protects","organizes","manages","keeps",
    "essential","must-have","everyday","daily","go-to",
    "heavy duty","durable","long-lasting","waterproof","leakproof",
    "reusable","washable","easy clean","dishwasher safe","microwave safe",
    "no more","never again","finally","at last",
]

FUN_BORING = [
    r"basic",r"standard",r"ordinary",r"plain",r"simple",r"generic",
    r"replacement",r"refill",r"bulk",r"value pack",r"economy",
]


def fun_score(title):
    t = title.lower()
    s = 0.3
    for kw in FUN_KEYWORDS:
        if kw in t: s += 0.12
    for pat in FUN_BORING:
        if re.search(pat, t): s -= 0.15
    if re.search(r"\b(patent|award|design|invention|shark tank)\b", t, re.I): s += 0.30
    if re.search(r"\b(2-in-1|3-in-1|multi|folding|collapsible|rechargeable|solar)\b", t, re.I): s += 0.10
    if re.search(r"\b(titanium|bamboo|copper|solid ood|ceramic|leather|carbon iber)\b", t, re.I): s += 0.10
    if re.search(r"\b(bluetooth|smart|LED|retro|vintage|modern)\b", t, re.I): s += 0.08
    if re.search(r"\b(kit|DIY|build|assemble|custom|maker|craft)\b", t, re.I): s += 0.08
    if re.search(r"\b(whimsical|playful|delight|surprising|unexpected|charming)\b", t, re.I): s += 0.08
    if re.search(r"\b(shark tank|kickstarter|indiegogo|funded)\b", t, re.I): s += 0.20
    return max(0.0, min(1.0, s))


def gift_score(title, desc=""):
    t = (title + " " + desc).lower()
    s = 0.15
    for kw in GIFT_KEYWORDS:
        if kw in t: s += 0.25
    return max(0.0, min(1.0, s))


def utility_score(title, desc=""):
    t = (title + " " + desc).lower()
    s = 0.2
    for kw in UTILITY_KEYWORDS:
        if kw in t: s += 0.14
    return max(0.0, min(1.0, s))


def has_real_desc(p):
    d = p.get('description', '')
    return d and 'edit me' not in d.lower() and len(d) > 30


def assign_badge(product):
    """Return badge string or None. Modifies product in place."""
    fs = fun_score(product.get('title', ''))
    gs = gift_score(product.get('title', ''), product.get('description', ''))
    us = utility_score(product.get('title', ''), product.get('description', ''))
    price = product.get('price')
    real_desc = has_real_desc(product)

    product['_fun_score'] = round(fs, 2)
    product['_gift_score'] = round(gs, 2)
    product['_utility_score'] = round(us, 2)

    # Priority order — first match wins, at most ONE badge

    # 1. Hidden Gem: genuinely novel/clever design
    if fs >= 0.75 and real_desc:
        product['badge'] = '🎯 Hidden Gem'
        return '🎯 Hidden Gem'

    # 2. Gift Pick: title or description signals giftability + solid quality
    if gs >= 0.65 and fs >= 0.45:
        product['badge'] = '🎁 Gift Pick'
        return '🎁 Gift Pick'

    # 3. Premium Design: higher-priced items with standout design
    if price and price > 40 and fs >= 0.68:
        product['badge'] = '✨ Premium Design'
        return '✨ Premium Design'

    # 4. Problem Solver: practical utility, actually useful
    if us >= 0.65 and fs >= 0.35:
        product['badge'] = '🔧 Problem Solver'
        return '🔧 Problem Solver'

    # 5. Best Value: cheap AND interesting (not just cheap)
    if price and price <= 15 and fs >= 0.50:
        product['badge'] = '💰 Best Value'
        return '💰 Best Value'

    # No badge qualifies — clear any stale badge
    product.pop('badge', None)
    return None


def process_products(products):
    """Score and badge a list of products. Returns stats dict."""
    stats = {'total': len(products), 'badged': 0, 'types': Counter()}

    for p in products:
        badge = assign_badge(p)
        if badge:
            stats['badged'] += 1
            stats['types'][badge] += 1

    return stats


def main():
    dry_run = '--dry-run' in sys.argv
    files = [a for a in sys.argv[1:] if a.endswith('.json') and a != '--dry-run']

    if not files:
        repo = Path(__file__).resolve().parent.parent
        files = [str(repo / 'data' / 'sample_products.json')]

    for fpath in files:
        with open(fpath) as f:
            products = json.load(f)

        stats = process_products(products)
        pct = stats['badged'] / max(stats['total'], 1) * 100

        print(f"\n{fpath}")
        print(f"  Total: {stats['total']} | Badged: {stats['badged']} ({pct:.0f}%)")
        for btype, count in stats['types'].most_common():
            print(f"    {btype}: {count}")

        if not dry_run:
            with open(fpath, 'w') as f:
                json.dump(products, f, indent=2)
            print(f"  ✅ Saved")


if __name__ == '__main__':
    main()