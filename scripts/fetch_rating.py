#!/usr/bin/env python3
"""
Lightweight Amazon product page rating scraper.

Hybrid approach:
  1. Try PAAPI get_items() FIRST (batch of 10 ASINs, ~1.5s per batch)
  2. Fall back to HTML scrape via curl for any ASINs PAAPI couldn't rate
  3. Cache results so we rarely need to re-fetch

Usage:
    python3 scripts/fetch_rating.py B0C4JTPPYY
    python3 scripts/fetch_rating.py B0C4JTPPYY B0DNJJ6RJY --batch --check

Returns JSON with star_rating, review_count, and asin per product.
"""

import sys, re, json, time, os, subprocess, tempfile
from pathlib import Path

# Rate limits
MAX_CURL_REQUESTS = 30  # curl is slow, use sparingly
PAAPI_SLEEP = 1.5       # between PAAPI batches
CURL_SLEEP = 2.0        # between curl scrapes

MIN_STAR_RATING = 4.5
MIN_REVIEW_COUNT = 100

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_FILE = SCRIPT_DIR.parent / 'data' / 'rating_cache.json'

CURL_HEADERS = [
    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    '-H', 'Accept-Language: en-US,en;q=0.9',
    '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    '-H', 'Accept-Encoding: identity',
    '--max-time', '10',
    '-s', '-L',
]


def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = str(CACHE_FILE) + '.tmp'
    with open(temp, 'w') as f:
        json.dump(cache, f, indent=2)
    os.replace(temp, CACHE_FILE)


def _get_paapi():
    """Lazy-import PAAPI. Returns AmazonCreatorsAPI instance or None."""
    try:
        sys.path.insert(0, str(Path.home() / 'workspace' / 'chipradar'))
        from amazon_creators_api_v3 import AmazonCreatorsAPI
        return AmazonCreatorsAPI()
    except Exception as e:
        print(f"  PAAPI import failed: {e}", file=sys.stderr)
        return None


def fetch_via_paapi(asins, cache):
    """Fetch ratings for a batch of ASINs via PAAPI get_items().
    
    PAAPI returns ratings natively via customerReviews.starRating
    and customerReviews.count — no scraping needed. Much faster
    (~1.5s per 10 ASINs) vs curl scraping (~15-18s per ASIN).
    """
    api = _get_paapi()
    if not api:
        return asins  # all unretrieved

    # Batch into groups of 10 (PAAPI limit per call)
    BATCH_SIZE = 10
    remaining = asins[:]

    for start in range(0, len(asins), BATCH_SIZE):
        batch = asins[start:start + BATCH_SIZE]
        try:
            results = api.get_items(batch)
            if isinstance(results, dict):
                # Single item result from get_item
                results = {batch[0]: results}
        except Exception as e:
            print(f"  PAAPI batch error ({batch[0]}..): {e}", file=sys.stderr)
            time.sleep(PAAPI_SLEEP)
            continue

        for asin in batch:
            item = results.get(asin, {}) if isinstance(results, dict) else {}
            if isinstance(item, dict) and not item.get('error'):
                cr = item.get('customer_reviews', {}) or {}
                star = cr.get('star_rating') or item.get('rating') or item.get('star_rating')
                count = cr.get('count') or item.get('review_count') or item.get('reviews_count')
                if star and count:
                    cache[asin] = {
                        'asin': asin,
                        'star_rating': round(float(star), 1),
                        'review_count': int(count),
                        'fetched_at': time.time(),
                    }
                    print(f"  📡 PAAPI: {asin} → {star}★/{count} reviews")
                    remaining = [a for a in remaining if a != asin]

        time.sleep(PAAPI_SLEEP)

    save_cache(cache)
    return remaining


def fetch_via_curl(asin, cache):
    """Fallback: scrape Amazon product page via curl.
    
    Only used when PAAPI can't return ratings for a specific ASIN.
    """
    # Check cache first
    if asin in cache:
        entry = cache[asin]
        if time.time() - entry.get('fetched_at', 0) < 30 * 86400:
            return {**entry, 'source': 'cache'}

    result = {'asin': asin, 'star_rating': None, 'review_count': None, 'error': None}

    try:
        url = f'https://www.amazon.com/dp/{asin}'
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as tmp:
            tmp_path = tmp.name

        curl_cmd = ['curl'] + CURL_HEADERS + ['-o', tmp_path, url]
        subprocess.run(curl_cmd, capture_output=True, timeout=18)

        with open(tmp_path, encoding='utf-8', errors='replace') as f:
            html = f.read()

        try:
            os.unlink(tmp_path)
        except:
            pass

        if len(html) < 10000:
            result['error'] = f'Page too small ({len(html)} bytes) — likely blocked'
            return result

        # Extract star rating
        star_match = re.search(
            r'acrPopover[^>]*title="([\d.]+)\s*out\s*of\s*5\s*stars', html, re.I
        )
        if not star_match:
            star_match = re.search(
                r'reviewCountTextLinkedHistogram[^>]*title="([\d.]+)\s*out\s*of\s*5\s*stars', html, re.I
            )
        if not star_match:
            star_match = re.search(
                r'a-icon-alt[^>]*>([\d.]+)\s*out\s*of\s*5\s*stars', html, re.I
            )
        if not star_match:
            star_match = re.search(r'([\d.]+)\s*out\s*of\s*5\s*stars?', html, re.I)

        if star_match:
            result['star_rating'] = float(star_match.group(1))

        # Extract review count
        count_match = re.search(
            r'id="acrCustomerReviewText"[^>]*aria-label="([\d,]+)\s*Reviews', html, re.I
        )
        if not count_match:
            count_match = re.search(
                r'id="acrCustomerReviewText"[^>]*>\(([\d,]+)\)', html
            )
        if not count_match:
            count_match = re.search(
                r'id="pqv-ratings"[^>]*>[^<]*<[^>]*>[^<]*<[^>]*>\s*([\d,.]+)\s*ratings?', html, re.I
            )
        if not count_match:
            count_match = re.search(
                r'a-icon-alt[^>]*>[\d.]+\s*out\s*of\s*5[^<]*<[^<]*<[^>]*>\s*([\d,]+)\s*ratings?', html, re.I
            )

        if count_match:
            result['review_count'] = int(count_match.group(1).replace(',', ''))

        if not result['star_rating'] and not result['review_count']:
            result['error'] = 'Could not extract rating data from page'

    except subprocess.TimeoutExpired:
        result['error'] = 'curl timed out'
    except Exception as e:
        result['error'] = f'Unexpected error: {e}'

    cache[asin] = {k: v for k, v in result.items() if k != 'source'}
    cache[asin]['fetched_at'] = time.time()
    save_cache(cache)
    time.sleep(CURL_SLEEP)

    return result


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    asins = [a.split('/')[-1].split('?')[0] for a in args if not a.startswith('--')]
    batch_mode = '--batch' in args
    check_mode = '--check' in args

    cache = load_cache()
    curl_requests = 0

    # Phase 1: Try PAAPI for all ASINs first (fast, batch of 10)
    print(f"PHASE 1: Checking {len(asins)} ASINs via PAAPI...", file=sys.stderr)
    paapi_cache_before = len(cache)
    remaining = fetch_via_paapi(asins, cache)
    paapi_found = len(asins) - len(remaining)
    paapi_cache_after = len(cache)
    print(f"  PAAPI found {paapi_found}/{len(asins)} ratings (cache grew by {paapi_cache_after - paapi_cache_before})", file=sys.stderr)

    # Phase 2: Fall back to curl for any PAAPI couldn't handle
    results = []
    for asin in asins:
        if asin in cache:
            entry = cache[asin]
            if time.time() - entry.get('fetched_at', 0) < 30 * 86400:
                results.append({**entry, 'source': 'cache'})
                continue

        if curl_requests >= MAX_CURL_REQUESTS:
            print(f"Max curl requests ({MAX_CURL_REQUESTS}) reached. Skipping {asin}.", file=sys.stderr)
            results.append({'asin': asin, 'star_rating': None, 'review_count': None, 'error': 'max_curl_reached'})
            continue

        result = fetch_via_curl(asin, cache)
        curl_requests += 1
        results.append(result)

    # Print per-ASIN results
    for result in results:
        status = '✅' if (result.get('star_rating') or 0) >= 4.5 and (result.get('review_count') or 0) >= 100 else '⚠️'
        print(f"{status} {result['asin']}: {result.get('star_rating', '?')}★ / {result.get('review_count', '?')} reviews")
        if result.get('error'):
            print(f"   ERROR: {result['error']}")

    if batch_mode:
        print(json.dumps(results, indent=2))

    if check_mode:
        all_pass = all(
            (r.get('star_rating') or 0) >= MIN_STAR_RATING and
            (r.get('review_count') or 0) >= MIN_REVIEW_COUNT
            for r in results
        )
        sys.exit(0 if all_pass else 1)

    save_cache(cache)
    successes = [r for r in results if r.get('star_rating') or r.get('review_count')]
    sys.exit(0 if successes else 1)


if __name__ == '__main__':
    main()