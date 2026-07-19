#!/usr/bin/env python3
"""WorthItGoods overnight price sweep - check all ASINs via AmazonCreatorsAPI."""
import sys, json, time

sys.path.insert(0, '/home/rock/workspace/chipradar')
from amazon_creators_api_v1 import AmazonCreatorsAPI

api = AmazonCreatorsAPI(partner_tag='worthitgoods-20')

products_path = '/home/rock/.openclaw/workspace/worthitgoods-repo/worthitgoods_products.json'
with open(products_path) as f:
    products = json.load(f)

results = {'checked': 0, 'ok': 0, 'unavailable': 0, 'price_changed': [], 'new_unavailable': [], 'errors': 0}
start = time.time()
total = len(products)

for i, p in enumerate(products):
    asin = p.get('asin')
    if not asin:
        continue

    results['checked'] += 1
    try:
        item = api.get_item(asin)
        price = item.get('price')
        old_price = p.get('price')
        p['price'] = price
        p['features'] = item.get('features', [])

        if price is None:
            results['unavailable'] += 1
            results['new_unavailable'].append(f"{p.get('title','?')[:50]} ({asin}) — was ${old_price} now UNAVAILABLE")
        elif old_price and abs(price - old_price) / old_price > 0.1:
            results['price_changed'].append(f"{p.get('title','?')[:50]} ({asin}): ${old_price:.2f} → ${price:.2f}")
        else:
            results['ok'] += 1
    except Exception as e:
        results['errors'] += 1

    if (i + 1) % 20 == 0 or i == total - 1:
        elapsed = time.time() - start
        print(f"PROGRESS: {i+1}/{total} ({elapsed:.0f}s)")

with open(products_path, 'w') as f:
    json.dump(products, f, indent=2)

elapsed = time.time() - start
print(f"RESULT: checked={results['checked']} ok={results['ok']} unavail={results['unavailable']} errors={results['errors']} changed={len(results['price_changed'])} time={elapsed:.0f}s")
for c in results['price_changed']:
    print(f"CHG: {c}")
for u in results['new_unavailable']:
    print(f"UNAV: {u}")
if not results['price_changed'] and not results['new_unavailable']:
    print("NO_CHANGES")
