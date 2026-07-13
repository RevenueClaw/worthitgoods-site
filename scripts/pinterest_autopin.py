#!/usr/bin/env python3
"""
Pinterest Auto-Pin for WorthItGoods
Pins the latest batch products to the "Worth It Finds" board.

Usage:
  python3 pinterest_autopin.py data/sample_products.json  (pins latest batch)

Requires:
  - PINTEREST_ACCESS_TOKEN in environment or .env
  - Board ID set in script or env
  
Notes:
  - Works on API Sandbox (trial) or Production (standard access)
  - Set PINTEREST_SANDBOX=true for sandbox testing
  - Skips products already pinned (checks by URL)
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────────
ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
BOARD_ID = os.environ.get("PINTEREST_BOARD_ID", "1088956453590786635")
SANDBOX = os.environ.get("PINTEREST_SANDBOX", "").lower() in ("1", "true", "yes")

BASE_URL = "https://api-sandbox.pinterest.com" if SANDBOX else "https://api.pinterest.com"
API_VERSION = "v5"

# ── Paths ───────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PRODUCTS_FILE = Path("/home/rock/.openclaw/workspace/worthitgoods-repo/data/sample_products.json")


def send_request(method, path, data=None):
    """Send an authenticated Pinterest API request."""
    url = f"{BASE_URL}/{API_VERSION}/{path}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode("utf-8") if data else None
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"  ❌ API error {e.code}: {err_body[:200]}", flush=True)
        return None


def get_existing_pins():
    """Get all existing pins on the board to avoid duplicates."""
    pins = []
    bookmark = None
    while True:
        path = f"boards/{BOARD_ID}/pins"
        if bookmark:
            path += f"?bookmark={urllib.parse.quote(bookmark)}"
        result = send_request("GET", path)
        if not result:
            break
        pins.extend(result.get("items", []))
        bookmark = result.get("bookmark")
        if not bookmark:
            break
    return pins


def create_pin(product, index, total):
    """Create a pin for a single product."""
    title = product.get("title", "")
    description = product.get("description", "")
    blurb = product.get("blurb", "")
    affiliate_url = product.get("affiliate_url", "")
    image = product.get("image", "")
    
    if not title or not image or not affiliate_url:
        print(f"  ⏭️  Skipping — missing required fields", flush=True)
        return False
    
    # Clean title for Pinterest (max 100 chars)
    clean = title.strip()
    if len(clean) > 90:
        clean = clean[:87] + "..."
    
    # Build description (max 500 chars)
    pin_desc = blurb or description[:200]
    pin_desc = pin_desc + f"\n\nFind more worth-it picks at WorthItGoods.com"
    if len(pin_desc) > 480:
        pin_desc = pin_desc[:477] + "..."
    
    result = send_request("POST", "pins", {
        "board_id": BOARD_ID,
        "title": clean,
        "description": pin_desc,
        "link": affiliate_url,
        "media_source": {
            "source_type": "image_url",
            "url": image,
        },
    })
    
    if result:
        print(f"  ✅ Pinned: {clean[:50]}...", flush=True)
        return True
    else:
        print(f"  ❌ Failed: {clean[:50]}...", flush=True)
        return False


def main():
    if not ACCESS_TOKEN:
        print("❌ Set PINTEREST_ACCESS_TOKEN environment variable", flush=True)
        return 1
    
    if not PRODUCTS_FILE.exists():
        print(f"❌ Products file not found: {PRODUCTS_FILE}", flush=True)
        return 1
    
    # Load products
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    
    print(f"\n{'='*60}", flush=True)
    print(f"WorthItGoods — Pinterest Auto-Pin", flush=True)
    print(f"Board: {BOARD_ID}", flush=True)
    print(f"Mode: {'SANDBOX' if SANDBOX else 'PRODUCTION'}", flush=True)
    print(f"Products: {len(products)}", flush=True)
    print(f"{'='*60}\n", flush=True)
    
    # Get existing pins to avoid duplicates
    print("Fetching existing pins...", flush=True)
    existing = get_existing_pins()
    existing_urls = {p.get("link", "") for p in existing}
    print(f"  Found {len(existing)} existing pins\n", flush=True)
    
    # Pin only the latest batch (first 12-18 products)
    batch_size = min(18, len(products))
    batch = products[:batch_size]
    
    pinned = 0
    skipped = 0
    for i, product in enumerate(batch):
        af_url = product.get("affiliate_url", "")
        if af_url in existing_urls:
            print(f"  ⏭️  Already pinned: {product.get('title', '')[:40]}...", flush=True)
            skipped += 1
            continue
        if create_pin(product, i + 1, len(batch)):
            pinned += 1
    
    print(f"\n{'='*60}", flush=True)
    print(f"Done: {pinned} pinned, {skipped} skipped", flush=True)
    print(f"{'='*60}", flush=True)
    return 0 if pinned > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
