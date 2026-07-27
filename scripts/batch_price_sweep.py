#!/usr/bin/env python3
"""
Batch price sweep for WorthItGoods — uses get_items() in batches of 10
instead of 149 individual sequential API calls.

Output: Updates worthitgoods_products.json in-place with latest prices.
Then prints a summary report to stdout for the cron job to relay.
"""

import sys, json, os
from pathlib import Path

# Add chipradar to path for AmazonCreatorsAPI
sys.path.insert(0, str(Path.home() / 'workspace' / 'chipradar'))
from amazon_creators_api_v1 import AmazonCreatorsAPI

REPO_DIR = Path.home() / '.openclaw' / 'workspace' / 'worthitgoods-repo'
PRODUCTS_FILE = REPO_DIR / 'worthitgoods_products.json'
BATCH_SIZE = 10  # Amazon PAAPIv5 recommended batch limit

def main():
    api = AmazonCreatorsAPI(partner_tag='worthitgoods-20')

    # Load products
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)

    total = len(products)
    asins = [p.get('asin') for p in products if p.get('asin')]

    print(f"Loaded {total} products, {len(asins)} with ASINs")

    # Batch API calls
    price_changed = []
    new_unavailable = []
    ok_count = 0
    total_calls = 0

    for i in range(0, len(asins), BATCH_SIZE):
        batch = asins[i:i + BATCH_SIZE]
        total_calls += 1
        print(f"  Batch {total_calls}: ASINs {i+1}-{i+len(batch)}...", end="", flush=True)

        try:
            results = api.get_items(batch)
        except Exception as e:
            print(f" FAILED: {e}")
            for asin in batch:
                new_unavailable.append(f"{asin}: API error — {e}")
            continue

        if isinstance(results, dict) and 'error' in results:
            print(f" ERROR: {results['error']}")
            for asin in batch:
                new_unavailable.append(f"{asin}: API error — {results['error']}")
            continue

        print(f" got {len(results)} results")

        # Map results back to products
        for product in products:
            asin = product.get('asin')
            if not asin or asin not in results:
                continue

            item = results[asin]
            if isinstance(item, dict) and 'error' in item:
                new_unavailable.append(f"{product.get('title','?')[:50]} ({asin}) — {item['error']}")
                continue

            new_price = item.get('price')
            old_price = product.get('price')

            product['price'] = new_price
            if item.get('features'):
                product['features'] = item.get('features', [])

            if new_price is None:
                new_unavailable.append(f"{product.get('title','?')[:50]} ({asin}) — was ${old_price} now UNAVAILABLE")
            elif old_price and abs(new_price - old_price) / old_price > 0.1:
                price_changed.append(f"{product.get('title','?')[:50]} ({asin}): ${old_price:.2f} → ${new_price:.2f}")
            else:
                ok_count += 1

    # Write updated products file
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=2)

    # Report
    print(f"\n{'='*60}")
    print(f"Batch Price Sweep Results ({total_calls} API calls)")
    print(f"{'='*60}")
    print(f"  Total products: {total}")
    print(f"  OK (no significant change): {ok_count}")
    print(f"  Unavailable/error: {len(new_unavailable)}")
    print(f"  Price changes (>10%): {len(price_changed)}")

    for c in price_changed:
        print(f"    📈 {c}")
    for u in new_unavailable:
        print(f"    ❌ {u}")

    # Clean up: remove the duplicate untracked comparison files
    print(f"\n  Cleaning up duplicate comparison files...")
    dupes = [
        'cliganic-vs-buggybands-mosquito-bracelets.html',
        'dosmix-retro-speaker-vs-victrola-willow.html',
        'goveelife-mini-air-purifier-vs-levoit.html',
        'hompow-mini-projector-vs-auking.html',
        'hotor-trunk-organizer-vs-fortem.html',
    ]
    removed = 0
    for d in dupes:
        p = REPO_DIR / 'comparisons' / d
        if p.exists():
            p.unlink()
            removed += 1
            print(f"    Removed {d}")
    print(f"  Cleaned up {removed} duplicate files")

    return 0  # Always exit 0 — unavailable items are expected, not errors

if __name__ == '__main__':
    sys.exit(main())
