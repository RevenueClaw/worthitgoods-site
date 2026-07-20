#!/usr/bin/env python3
"""
check_dedup.py — Auto-deduplicate new products against existing site products.
Called by add_batch.sh before merging.

Usage: python3 check_dedup.py <new_batch.json> <existing_products.json>

Returns:
  - Exit 0: no duplicates found
  - Exit 1: duplicates detected (prints details)
"""
import json
import sys

# Extended product nouns — must stay in sync with curate_products.py
PRODUCT_NOUNS = {
    'rest', 'spoon', 'cup', 'bowl', 'knife', 'ladle', 'spatula', 'grater', 'zester',
    'shears', 'skillet', 'mold', 'scale', 'timer', 'board', 'rack', 'holder',
    'bag', 'pack', 'case', 'hat', 'shirt', 'pants', 'socks', 'gloves',
    'lamp', 'light', 'fan', 'charger', 'cable', 'stand', 'mount',
    'tool', 'pouch', 'organizer', 'mat', 'towel', 'kit', 'set', 'caddy',
    'scoop', 'shooter', 'launcher', 'disc', 'puzzle', 'game',
    'tumbler', 'mug', 'glass', 'bottle', 'jar', 'container',
    'blanket', 'pillow', 'plush', 'coaster', 'vase', 'journal',
    'brush', 'comb', 'mirror', 'tray', 'basket', 'bin',
    'screwdriver', 'socket', 'wrench', 'hammer', 'level',
    'camera', 'lens', 'tripod', 'speaker', 'adapter', 'hub', 'dock',
    'flag', 'banner', 'windsock', 'bunting',
    'paddleboard', 'hammock', 'cooler', 'lunchbox',
    'plug', 'registration', 'purifier', 'filter', 'trimmer', 'shaver',
    'sander', 'detector', 'monitor', 'tracker', 'alarm', 'lock',
    'straps', 'harness', 'leash', 'collar', 'feeder',
    'brush', 'clipper', 'dryer', 'heater', 'humidifier', 'diffuser',
    'projector', 'keyboard', 'mouse', 'tablet', 'laptop', 'monitor',
    'headphones', 'earbuds', 'microphone', 'webcam', 'router',
    'backpack', 'duffle', 'tote', 'sling', 'pouch', 'wallet',
    'stool', 'chair', 'desk', 'shelf', 'cabinet', 'drawer',
    'curtain', 'blind', 'rug', 'cushion', 'throw',
}

STOP_WORDS = {"and", "the", "for", "with", "in", "of", "to", "a", "an", "is", "-", "|", ",", "."}


def is_duplicate(new_title, existing_titles):
    """Check if new_title is essentially the same as any existing product."""
    t = new_title.lower().strip()
    for et in existing_titles:
        if not et:
            continue
        et_lower = et.lower().strip()
        new_words = set(t.split())
        exist_words = set(et_lower.split())
        common = new_words & exist_words

        meaningful = [w for w in common if len(w) > 3 and w not in STOP_WORDS]
        shared_nouns = set(meaningful) & PRODUCT_NOUNS

        if shared_nouns and len(meaningful) >= 2:
            return True, et[:60]
        if len(meaningful) >= 4:
            return True, et[:60]
    return False, None


def main():
    if len(sys.argv) < 3:
        print("Usage: check_dedup.py <new_batch.json> <existing_products.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        new_batch = json.load(f)
    with open(sys.argv[2]) as f:
        existing = json.load(f)

    existing_titles = [p.get("title", "") for p in existing]
    duplicates = []

    for i, product in enumerate(new_batch):
        title = product.get("title", "")
        if not title:
            continue
        is_dup, match = is_duplicate(title, existing_titles)
        if is_dup:
            duplicates.append((title[:70], match))

    if duplicates:
        print("❌ DUPLICATES DETECTED — batch will NOT be added:")
        for title, match in duplicates:
            print(f"  ⚠️ '{title}'")
            print(f"     → matches existing: '{match}'")
        print(f"\nRemove these products from the batch and re-run add_batch.sh")
        sys.exit(1)
    else:
        print(f"✅ All {len(new_batch)} products are unique — safe to add")


if __name__ == "__main__":
    main()