#!/usr/bin/env python3
"""
Rating Cache Re-Check — recover "nearly passed" products.

Scans the rating cache for products that were CLOSE to passing the
4.5★/100 review gate but fell short (≥4.3★ but <100 reviews,
or ≥80 reviews but <4.5★). Re-fetches their ratings via fetch_rating.py.

As products age on Amazon, ratings accumulate. A product that had
4.3★/80 reviews last month might now have 4.6★/200 reviews.
This recovers previously-interesting products without new PAAPI searches.

Usage:
    python3 scripts/recheck_near_pass.py          # dry-run
    python3 scripts/recheck_near_pass.py --apply   # actually re-fetch
    python3 scripts/recheck_near_pass.py --cron    # auto-apply, quiet output

Schedule: Weekly (Sunday 3 AM) via cron.
"""

import json, os, sys, subprocess, time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_FILE = SCRIPT_DIR.parent / 'data' / 'rating_cache.json'
FETCH_SCRIPT = SCRIPT_DIR / 'fetch_rating.py'

MIN_PASS_RATING = 4.5
MIN_PASS_REVIEWS = 100

# Products that are CLOSE to passing
NEAR_RATING = 4.3    # re-check if star_rating >= this
NEAR_REVIEWS = 80    # re-check if review_count >= this


def load_cache():
    with open(CACHE_FILE) as f:
        data = json.load(f)
    # Normalize to dict keyed by ASIN
    if isinstance(data, list):
        return {e.get('asin', ''): e for e in data if e.get('asin')}
    return data


def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = str(CACHE_FILE) + '.tmp'
    with open(temp, 'w') as f:
        json.dump(cache, f, indent=2)
    os.replace(temp, CACHE_FILE)


def main():
    apply = '--apply' in sys.argv or '--cron' in sys.argv
    quiet = '--cron' in sys.argv

    cache = load_cache()
    total = len(cache)

    # Find nearly-passed products
    near_pass = []
    for asin, entry in cache.items():
        if not isinstance(entry, dict):
            continue
        star = entry.get('star_rating', 0) or 0
        reviews = entry.get('review_count', 0) or 0
        
        # Already passing — skip
        if star >= MIN_PASS_RATING and reviews >= MIN_PASS_REVIEWS:
            continue
        
        # Close enough to re-check
        if star >= NEAR_RATING or reviews >= NEAR_REVIEWS:
            near_pass.append(asin)

    new_passing = 0

    if not near_pass:
        if not quiet:
            print(f"📊 Rating cache re-check: {total} entries, 0 near-pass candidates")
        return 0

    if not quiet:
        print(f"📊 Rating cache re-check: {total} entries, {len(near_pass)} near-pass candidates")
        for asin in near_pass[:15]:
            e = cache.get(asin, {})
            print(f"   {asin}: {e.get('star_rating','?')}★ / {e.get('review_count','?')} reviews")
        if len(near_pass) > 15:
            print(f"   ... and {len(near_pass) - 15} more")

    if not apply:
        if not quiet:
            print(f"\n⚠️  Dry run — pass --apply to actually re-fetch ratings")
        return 0

    # Re-fetch ratings in batches
    BATCH = 20
    for start in range(0, len(near_pass), BATCH):
        batch = near_pass[start:start + BATCH]
        if not quiet:
            print(f"\n  Batch {start//BATCH + 1}/{(len(near_pass)-1)//BATCH + 1}: {batch[0]}..{batch[-1]}")

        result = subprocess.run(
            [sys.executable, str(FETCH_SCRIPT)] + batch,
            capture_output=True, text=True, timeout=300
        )

        for line in result.stdout.split('\n'):
            if '✅' in line or '⚠️' in line:
                parts = line.split()
                if len(parts) >= 2:
                    asin = parts[1].replace(':', '')
                    # Reload from cache to check if it now passes
                    fresh = load_cache().get(asin, {})
                    star = fresh.get('star_rating', 0) or 0
                    reviews = fresh.get('review_count', 0) or 0
                    if star >= MIN_PASS_RATING and reviews >= MIN_PASS_REVIEWS:
                        new_passing += 1
                        if not quiet:
                            print(f"    🆕 NOW PASSES: {asin} → {star}★/{reviews} reviews")

        if start + BATCH < len(near_pass):
            time.sleep(2)

    if not quiet:
        print(f"\n{'='*45}")
        print(f" RECOVERED: {new_passing} new products now pass the rating gate")
        print(f" Total rating cache: {len(cache)} ASINs")
        print(f"{'='*45}")

    return new_passing


if __name__ == '__main__':
    sys.exit(main())