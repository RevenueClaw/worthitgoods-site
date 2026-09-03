#!/usr/bin/env python3
"""
check_dedup.py — Pure ASIN-based dedup check for product batches.
No fuzzy title matching, no false positives.

Usage: python3 check_dedup.py <new_batch.json> <existing_products.json>

Returns:
  - Exit 0: no duplicates found
  - Exit 1: duplicates detected (prints details)
"""
import json
import re
import sys


def extract_asin(url):
    if not url:
        return None
    m = re.search(r'/dp/([A-Z0-9]{10})', url)
    if m:
        return m.group(1)
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: check_dedup.py <new_batch.json> <existing_products.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        new_batch = json.load(f)
    with open(sys.argv[2]) as f:
        existing = json.load(f)

    # Build set of existing ASINs
    existing_asins = set()
    for ep in existing:
        url = ep.get("url") or ep.get("affiliate_url") or ""
        asin = extract_asin(url)
        if asin:
            existing_asins.add(asin)

    # Check each new product's ASIN
    duplicates = []
    for product in new_batch:
        title = product.get("title", "")
        url = product.get("affiliate_url") or product.get("url") or ""
        asin = extract_asin(url)
        if not asin:
            continue  # No ASIN to check
        if asin in existing_asins:
            duplicates.append((asin, title[:70]))

    if duplicates:
        print("❌ DUPLICATE ASINS DETECTED — batch will NOT be added:")
        for asin, title in duplicates:
            print(f"  ⚠️ {asin} — {title}")
        print(f"\nRemove these products and re-run add_batch.sh")
        sys.exit(1)
    else:
        total = len(new_batch)
        print(f"✅ All {total} products are unique by ASIN — safe to add")


if __name__ == "__main__":
    main()