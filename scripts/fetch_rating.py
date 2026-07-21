#!/usr/bin/env python3
"""
Lightweight Amazon product page rating scraper.
Fallback for when PAAPI doesn't return customerReviews.

Usage:
    python3 scripts/fetch_rating.py B0C4JTPPYY
    python3 scripts/fetch_rating.py B0C4JTPPYY B0DNJJ6RJY --batch

Returns JSON with star_rating, review_count, and asin per product.
"""

import sys, re, json, time, os, subprocess, tempfile

# Rate limit: max requests per run
MAX_REQUESTS = 40
MIN_STAR_RATING = 4.5
MIN_REVIEW_COUNT = 100

# Cache
CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rating_cache.json')

CURL_HEADERS = [
    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    '-H', 'Accept-Language: en-US,en;q=0.9',
    '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    '-H', 'Accept-Encoding: identity',
    '--max-time', '15',
    '-s', '-L',
]


def load_cache():
    """Load rating cache from disk."""
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    """Save rating cache to disk."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    temp = CACHE_FILE + '.tmp'
    with open(temp, 'w') as f:
        json.dump(cache, f, indent=2)
    os.replace(temp, CACHE_FILE)


def fetch_rating(asin: str, cache: dict) -> dict:
    """Fetch star rating and review count for a single ASIN.
    
    Tries cache first, then scrapes Amazon product page.
    Returns dict with asin, star_rating, review_count, source.
    """
    # Check cache
    if asin in cache:
        entry = cache[asin]
        # Cache valid for 7 days
        if time.time() - entry.get('fetched_at', 0) < 7 * 86400:
            return {**entry, 'source': 'cache'}
    
    result = {
        'asin': asin,
        'star_rating': None,
        'review_count': None,
        'error': None,
    }
    
    try:
        # Use curl via subprocess for reliable page fetching (bypasses bot detection)
        url = f'https://www.amazon.com/dp/{asin}'
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as tmp:
            tmp_path = tmp.name
        
        curl_cmd = ['curl'] + CURL_HEADERS + ['-o', tmp_path, url]
        subprocess.run(curl_cmd, capture_output=True, timeout=20)
        
        with open(tmp_path, encoding='utf-8', errors='replace') as f:
            html = f.read()
        
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if len(html) < 10000:
            result['error'] = f'Page too small ({len(html)} bytes) — likely blocked'
            return result
        
        # Extract star rating (try most specific patterns first)
        # Pattern 1: acrPopover title attribute (most reliable for primary product)
        star_match = re.search(
            r'acrPopover[^>]*title="([\d.]+)\s*out\s*of\s*5\s*stars',
            html, re.I
        )
        if not star_match:
            # Pattern 2: reviewCountTextLinkedHistogram title
            star_match = re.search(
            r'reviewCountTextLinkedHistogram[^>]*title="([\d.]+)\s*out\s*of\s*5\s*stars',
            html, re.I
        )
        if not star_match:
            # Pattern 3: a-icon-alt with star text (near the product)
            star_match = re.search(
                r'a-icon-alt[^>]*>([\d.]+)\s*out\s*of\s*5\s*stars',
                html, re.I
            )
        if not star_match:
            # Pattern 4: pqv-ratings id
            star_match = re.search(
                r'id="pqv-ratings"[^>]*>\s*([\d.]+)\s*out\s*of\s*5',
                html, re.I
            )
        if not star_match:
            # Pattern 5: Simplest: just "X out of 5 stars" with a decimal
            star_match = re.search(r'([\d.]+)\s*out\s*of\s*5\s*stars?', html, re.I)
        
        if star_match:
            result['star_rating'] = float(star_match.group(1))
        
        # Extract review count from acrCustomerReviewText
        # Pattern 1: aria-label like "8,086 Reviews"
        count_match = re.search(
            r'id="acrCustomerReviewText"[^>]*aria-label="([\d,]+)\s*Reviews',
            html, re.I
        )
        if not count_match:
            # Pattern 2: inner text like "(8,086)"
            count_match = re.search(
                r'id="acrCustomerReviewText"[^>]*>\(([\d,]+)\)',
                html
            )
        if not count_match:
            # Pattern 3: pqv-ratings format (reliable secondary pattern)
            count_match = re.search(
                r'id="pqv-ratings"[^>]*>[^<]*<[^>]*>[^<]*<[^>]*>\s*([\d,.]+)\s*ratings?',
                html, re.I
            )
        if not count_match:
            # Pattern 4: "X ratings" after a product star rating
            count_match = re.search(
                r'a-icon-alt[^>]*>[\d.]+\s*out\s*of\s*5[^<]*<[^<]*<[^>]*>\s*([\d,]+)\s*ratings?',
                html, re.I
            )
        
        if count_match:
            result['review_count'] = int(count_match.group(1).replace(',', ''))
        
        if not result['star_rating'] and not result['review_count']:
            result['error'] = 'Could not extract rating data from page'
        
    except subprocess.TimeoutExpired:
        result['error'] = 'curl timed out'
    except Exception as e:
        result['error'] = f'Unexpected error: {e}'
    
    # Update cache
    cache[asin] = {k: v for k, v in result.items() if k != 'source'}
    cache[asin]['fetched_at'] = time.time()
    save_cache(cache)
    
    # Small delay to avoid hammering Amazon
    time.sleep(1.5)
    
    return result


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)
    
    # Extract ASINs from arguments
    asins = [a.split('/')[-1].split('?')[0] for a in args if not a.startswith('--')]
    batch_mode = '--batch' in args
    check_mode = '--check' in args
    
    cache = load_cache()
    results = []
    requests_made = 0
    
    for asin in asins:
        if requests_made >= MAX_REQUESTS:
            print(f"Max requests ({MAX_REQUESTS}) reached. Skipping remaining.", file=sys.stderr)
            break
        
        result = fetch_rating(asin, cache)
        if result.get('source') != 'cache':
            requests_made += 1
        
        results.append(result)
        
        if not batch_mode:
            status = '✅' if (result.get('star_rating') or 0) >= 4.5 and (result.get('review_count') or 0) >= 100 else '⚠️'
            print(f"{status} {asin}: {result.get('star_rating', '?')}★ / {result.get('review_count', '?')} reviews")
            if result.get('error'):
                print(f"   ERROR: {result['error']}")
    
    if batch_mode:
        print(json.dumps(results, indent=2))
    
    if check_mode:
        # --check: exit 0 if ALL ASINs pass the threshold, 1 otherwise
        all_pass = all(
            (r.get('star_rating') or 0) >= MIN_STAR_RATING and
            (r.get('review_count') or 0) >= MIN_REVIEW_COUNT
            for r in results
        )
        sys.exit(0 if all_pass else 1)
    
    save_cache(cache)
    
    # Exit with success if any ratings found, error if all failed
    successes = [r for r in results if r.get('star_rating') or r.get('review_count')]
    sys.exit(0 if successes else 1)


if __name__ == '__main__':
    main()
