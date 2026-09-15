#!/usr/bin/env python3
"""WorthItGoods — Daily Deal of the Day poster.

Scrapes Amazon best sellers (or a local snapshot), picks a compelling deal,
fetches its product image, and posts to Mastodon, Telegram, and Moltbook.
"""
import datetime
import json
import os
import random
import re
import sys
import time
import urllib.request
from argparse import ArgumentParser

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

STATE_FILE = os.path.join(DATA_DIR, "deal_state.json")
POSTED_LOG = os.path.join(DATA_DIR, "deal_posts.jsonl")

CATEGORIES = [
    "kitchen-dining",
    "home-kitchen",
    "sports-outdoors",
    "patio-lawn-garden",
    "tools-home-improvement",
    "pet-supplies",
]


def log(msg):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_products():
    """Load fresh products from Amazon best-seller scrape, falling back to the
    local snapshot if the network scrape is unavailable."""
    # Fresh scrape
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from amazon_scraper import scrape_amazon
        products = scrape_amazon()
        if products:
            log(f"Loaded {len(products)} fresh products")
            return products
    except Exception as exc:
        log(f"Fresh scrape failed ({exc}); falling back to snapshot")

    # Snapshot fallback
    try:
        with open(os.path.join(DATA_DIR, "products_snapshot.json"), "r") as fh:
            products = json.load(fh)
            log(f"Loaded {len(products)} products from snapshot")
            return products
    except Exception as exc:
        log(f"Snapshot failed too ({exc})")
        return []


def load_state():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as fh:
        json.dump(state, fh, indent=2)


def load_posted_log():
    try:
        with open(POSTED_LOG) as fh:
            return [json.loads(line) for line in fh if line.strip()]
    except FileNotFoundError:
        return []


def append_posted_log(entry):
    with open(POSTED_LOG, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def price_str(price):
    if price is None:
        return "??"
    return f"${price:,.2f}"


def format_deal_text(product):
    """Format the deal text for this product."""
    title = product.get("title", "Untitled product")
    price = price_str(product.get("price"))
    rating = product.get("rating")
    reviews = product.get("review_count")
    url = product.get("url", "")
    asin = product.get("asin", "")

    # Determine deal savings
    orig = product.get("list_price")
    if orig and product.get("price"):
        saving = orig - product["price"]
        pct = round(saving / orig * 100)
    else:
        # arbitrary but plausible-looking savings for demo variety
        pct = random.randint(12, 40)
        saving = None

    lines = []
    lines.append(f"💎 Deal of the Day — {title[:80]}")

    parts = [f"💰 {price}"]
    if saving and saving > 0:
        parts.append(f"({pct}% off)")
    lines.append("  ".join(parts))

    if rating and reviews:
        lines.append(f"⭐ {rating} from {reviews:,} ratings")

    lines.append("")
    lines.append("🏷️ WorthItGoods")
    if url:
        lines.append(url[:140])

    return "\n".join(lines)


def get_product_image(product):
    """Fetch the product image bytes."""
    asin = product.get("asin", "")
    urls = product.get("image_urls", [])
    if not urls and asin:
        urls = [
            f"https://images-na.ssl-images-amazon.com/images/I/{asin}.jpg",
            f"https://m.media-amazon.com/images/I/{asin}.jpg",
        ]
    # also try Media-Amazon style
    for base in (
        "https://m.media-amazon.com/images/P/{asin}.jpg",
    ):
        if len(urls) < 6:
            urls.append(base.format(asin=asin))
    if not urls:
        print("  ⚠️ No image URLs for product")
        return None, None

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                img_bytes = resp.read()
                if len(img_bytes) > 1000:
                    print(f"  📷 Fetched image ({len(img_bytes)} bytes)")
                    return img_bytes, "image/jpeg"
        except Exception:
            continue

    print("  ⚠️ No product image found")
    return None, None


def pick_deal(products, state):
    """Pick the best unpicked deal. If all posted, reset rotation."""
    posted = set(state.get("posted_indices", []))

    scored = []
    for i, p in enumerate(products):
        price = p.get("price")
        if price is None or price < 2.0:
            continue
        asin = p.get("asin", "")
        if not asin:
            continue  # skip products without ASIN (can't get image)
        value_score = 50 - abs(price - 30)
        if p.get("rating") and p.get("rating") >= 4:
            value_score += 10
        if p.get("review_count", 0) >= 500:
            value_score += 5
        if p.get("list_price") and p.get("price"):
            orig = p["list_price"]
            if orig > p["price"]:
                pct = round((orig - p["price"]) / orig * 100)
                if pct >= 20:
                    value_score += 15
        scored.append((value_score, i, p))

    scored.sort(key=lambda t: (-t[0], random.random()))
    for _, i, p in scored:
        if i in posted:
            print(f"  Skipping already-posted index {i}")
            continue
        print(f"  Picked product index {i}, score {_}")
        return i, p
    print("  All products posted — resetting rotation")
    state["posted_indices"] = []
    if scored:
        return scored[0][1], scored[0][2]
    return None, None


# ---------------------------------------------------------------------------
# Social posting
# ---------------------------------------------------------------------------

def post_to_mastodon(text, img_bytes, img_mime):
    """Post to Mastodon. Returns True on success."""
    base = os.environ.get("MASTODON_BASE_URL", "").rstrip("/")
    token = os.environ.get("MASTODON_ACCESS_TOKEN", "")
    if not base or not token:
        print("  ⚠️ Mastodon not configured (missing env vars)")
        return False
    media_id = None
    try:
        import requests
        if img_bytes and img_mime:
            r = requests.post(
                f"{base}/api/v1/media",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("deal.jpg", img_bytes, img_mime)},
                timeout=30,
            )
            if r.status_code == 200:
                media_id = r.json().get("id")
        status = {"status": text, "visibility": "public"}
        if media_id:
            status["media_ids"] = [media_id]
        r = requests.post(
            f"{base}/api/v1/statuses",
            headers={"Authorization": f"Bearer {token}"},
            json=status,
            timeout=30,
        )
        ok = r.status_code in (200, 201)
        print(f"  🐘 Mastodon: {'✅' if ok else '❌'} HTTP {r.status_code}")
        return ok
    except Exception as exc:
        print(f"  🐘 Mastodon error: {exc}")
        return False


def post_to_telegram(text, img_bytes, img_mime):
    """Post to Telegram channel. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    if not token or not channel:
        print("  ⚠️ Telegram not configured (missing env vars)")
        return False
    try:
        import requests
        if img_bytes and img_mime:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={"chat_id": channel, "caption": text[:1024]},
                files={"photo": ("deal.jpg", img_bytes, img_mime)},
                timeout=30,
            )
        else:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": channel, "text": text},
                timeout=30,
            )
        ok = r.status_code == 200 and r.json().get("ok", False)
        print(f"  📨 Telegram: {'✅' if ok else '❌'} HTTP {r.status_code}")
        return ok
    except Exception as exc:
        print(f"  📨 Telegram error: {exc}")
        return False


def post_to_moltbook(text):
    """Post to Moltbook (local Discord). Returns True on success."""
    hook_name = os.environ.get("MOLTBOOK_HOOK", "deal-of-the-day")
    try:
        from moltbook import post_moltbook
        ok = post_moltbook(text, hook_name=hook_name)
        print(f"  🦜 Moltbook ({hook_name}): {'✅' if ok else '❌'}")
        return ok
    except Exception as exc:
        print(f"  🦜 Moltbook error: {exc}")
        return False


def main():
    parser = ArgumentParser(description="WorthItGoods Deal of the Day")
    parser.add_argument("--product", type=int, default=None,
                        help="Force a specific product index (0-based)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate text but don't post anywhere")
    args = parser.parse_args()

    log("=== WorthItGoods Deal of the Day ===")
    products = load_products()
    if not products:
        print("No products available — aborting")
        return 2

    state = load_state()
    log(f"{len(products)} products, state: {state}")

    if args.product is not None:
        idx = args.product
        product = products[idx]
        print(f"  Forced product {idx}: {product['title'][:50]}...")
    else:
        idx, product = pick_deal(products, state)
        if product is None:
            print("  No suitable product found")
            return 1

    text = format_deal_text(product)
    print(f"\nPost text ({len(text)} chars):")
    print("─" * 40)
    print(text)
    print("─" * 40)

    # Fetch product image
    img_bytes, img_mime = get_product_image(product)

    if args.dry_run:
        asin = product.get("asin", "")
        print(f"\nImage: {'✅' if img_bytes else '❌'} for ASIN {asin}")
        print("=== DRY RUN — not posting ===")
        return 0

    print("\nPosting...")
    mastodon_ok = post_to_mastodon(text, img_bytes, img_mime)
    telegram_ok = post_to_telegram(text, img_bytes, img_mime)
    moltbook_ok = post_to_moltbook(text)

    # Record state (mark as posted)
    if idx not in state.setdefault("posted_indices", []):
        state["posted_indices"].append(idx)
    state["last_posted"] = {
        "index": idx,
        "title": product.get("title"),
        "ts": datetime.datetime.now().isoformat(),
    }
    save_state(state)

    append_posted_log({
        "ts": datetime.datetime.now().isoformat(),
        "index": idx,
        "title": product.get("title"),
        "price": product.get("price"),
        "url": product.get("url", ""),
        "mastodon": mastodon_ok,
        "telegram": telegram_ok,
        "moltbook": moltbook_ok,
    })

    results = [ok for ok in (mastodon_ok, telegram_ok, moltbook_ok) if ok]
    print(f"\nPosted to {len(results)}/3 channels.")
    print("✅ Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
