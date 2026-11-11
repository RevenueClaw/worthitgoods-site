#!/usr/bin/env python3
"""
check_dedup.py — ASIN + title-similarity dedup check for product batches.
Flags exact ASIN duplicates AND products too similar to coexist in a batch.

Usage: python3 check_dedup.py <new_batch.json> <existing_products.json>

Returns:
  - Exit 0: no issues found
  - Exit 1: duplicates or similar-product conflicts detected (prints details)
"""
import json
import re
import sys
from collections import defaultdict


# ── Stop words to ignore when comparing titles ───────────────────────────────
STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "of", "to", "is", "it",
    "on", "at", "by", "as", "no", "up", "be", "its", "not", "but", "from",
    "all", "are", "was", "one", "two", "our", "can", "has", "had", "this",
    "that", "will", "you", "your", "just", "new", "pro", "mini", "max",
    "inch", "pack", "set", "size", "large", "small", "big",
}

# ── Narrow-category keyword groups: products sharing a group are too similar ─
# Format: group_name -> list of keyword phrases (lowercase, matched against title)
NARROW_CATEGORIES = {
    "posture_corrector": ["posture corrector", "posture brace", "back brace", "posture support"],
    "optical_device": ["binocular", "monocular", "night vision", "telescope", "spotting scope"],
    "mosquito_repellent": ["mosquito repellent", "mosquito bracelet", "bug repellent", "insect repellent"],
    "laptop_stand": ["laptop stand", "laptop riser", "notebook stand", "computer stand"],
    "electric_duster": ["electric air duster", "electric duster", "compressed air", "air blower"],
    "label_maker": ["label maker", "label printer", "label tape", "thermal label"],
    "bluetooth_speaker": ["bluetooth speaker", "portable speaker", "wireless speaker"],
    "desk_lamp": ["desk lamp", "led desk light", "office lamp", "task lamp"],
    "screwdriver_set": ["screwdriver set", "precision screwdriver", "repair kit", "magnetic screwdriver"],
    "kitchen_knife": ["chef knife", "kitchen knife", "paring knife", "knife set"],
}


def extract_asin(url):
    """Extract ASIN from Amazon URL."""
    if not url:
        return None
    m = re.search(r'/dp/([A-Z0-9]{10})', url)
    return m.group(1) if m else None


def tokenize(title):
    """Extract significant lowercase words from title."""
    words = re.findall(r'[a-zA-Z]+', title.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def title_overlap(tokens1, tokens2):
    """Return fraction of overlap: shared / min(|t1|, |t2|)."""
    if not tokens1 or not tokens2:
        return 0.0
    s1, s2 = set(tokens1), set(tokens2)
    shared = s1 & s2
    return len(shared) / min(len(s1), len(s2))


def category_conflicts(products):
    """Find products in the same narrow category within a batch."""
    conflicts = []
    for group_name, keywords in NARROW_CATEGORIES.items():
        matches = []
        for i, p in enumerate(products):
            t = p.get("title", "").lower()
            if any(kw in t for kw in keywords):
                matches.append((i, p.get("title", "")[:70]))
        if len(matches) > 1:
            conflicts.append((group_name, matches))
    return conflicts


def main():
    if len(sys.argv) < 3:
        print("Usage: check_dedup.py <new_batch.json> <existing_products.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        new_batch = json.load(f)
    with open(sys.argv[2]) as f:
        existing = json.load(f)

    # ── Phase 1: ASIN dedup against existing products ────────────────────────
    existing_asins = set()
    for ep in existing:
        url = ep.get("url") or ep.get("affiliate_url") or ""
        asin = extract_asin(url)
        if asin:
            existing_asins.add(asin)

    asin_dupes = []
    for product in new_batch:
        title = product.get("title", "")
        url = product.get("affiliate_url") or product.get("url") or ""
        asin = extract_asin(url)
        if asin and asin in existing_asins:
            asin_dupes.append((asin, title[:70]))

    # ── Phase 2: Within-batch title similarity ───────────────────────────────
    batch_tokens = [tokenize(p.get("title", "")) for p in new_batch]
    similar_pairs = []
    for i in range(len(new_batch)):
        for j in range(i + 1, len(new_batch)):
            overlap = title_overlap(batch_tokens[i], batch_tokens[j])
            if overlap > 0.45:  # >45% keyword overlap = too similar
                similar_pairs.append((i, j, overlap))

    # ── Phase 3: Within-batch narrow-category conflicts ──────────────────────
    category_conflicts_found = category_conflicts(new_batch)

    # ── Report ───────────────────────────────────────────────────────────────
    errors = False

    if asin_dupes:
        errors = True
        print("❌ EXACT ASIN DUPLICATES — batch will NOT be added:")
        for asin, title in asin_dupes:
            print(f"  ⚠️  {asin} — {title}")

    if similar_pairs:
        errors = True
        print("\n❌ SIMILAR PRODUCTS IN BATCH — too alike to coexist:")
        for i, j, overlap in similar_pairs:
            t1 = new_batch[i].get("title", "")[:60]
            t2 = new_batch[j].get("title", "")[:60]
            print(f"  ⚠️  {overlap:.0%} title overlap:")
            print(f"      [{i+1}] {t1}...")
            print(f"      [{j+1}] {t2}...")

    if category_conflicts_found:
        errors = True
        print("\n❌ CATEGORY CONFLICTS — too many similar products in one batch:")
        for group, items in category_conflicts_found:
            print(f"  ⚠️  Category: {group} ({len(items)} products)")
            for idx, title in items:
                print(f"      [{idx+1}] {title}")

    if errors:
        print(f"\nRemove conflicting products and re-run.")
        sys.exit(1)

    total = len(new_batch)
    print(f"✅ All {total} products pass ASIN + similarity checks — safe to add")


if __name__ == "__main__":
    main()