#!/usr/bin/env python3
"""
WorthItGoods Deal of the Day — auto-posts the best deal with image
to Mastodon, Telegram, and Moltbook.

Usage:
  python3 deal_of_the_day.py [--dry-run]
  python3 deal_of_the_day.py --product 42   # force specific product
"""

import json
import os
import sys
import io
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

# ─── CONFIG ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
PRODUCTS_FILE = BASE_DIR / "worthitgoods_products.json"
STATE_FILE = BASE_DIR / ".deal_of_the_day_state.json"
SITE_URL = "https://www.worthitgoods.com"

# Mastodon
MASTODON_TOKEN_FILE = Path("/home/rock/.openclaw/credentials/mastodon-worthitgoods.env")
MASTODON_INSTANCE = "mastodon.social"
MASTODON_API = f"https://{MASTODON_INSTANCE}/api/v1"

# Telegram
TELEGRAM_API = "https://api.telegram.org/bot"

# Moltbook
MOLTBOOK_CREDS = Path.home() / ".config" / "moltbook" / "credentials.json"
MOLTBOOK_API = "https://www.moltbook.com/api/v1"
# ──────────────────────────────────────────────────────────────────


def load_products():
    if not PRODUCTS_FILE.exists():
        print(f"ERROR: Products file not found: {PRODUCTS_FILE}")
        sys.exit(1)
    with open(PRODUCTS_FILE) as f:
        return json.load(f)


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"posted_indices": [], "last_date": None}


def save_state(state):
    state["last_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_product_image(product):
    """Fetch product image from product's image field or fallback to ASIN-based URL.
    Returns (image_bytes, mime_type) or (None, None)."""
    asin = product.get("asin", "")
    product_image = product.get("image", "")

    urls = []

    # 1. Use the product's stored image URL directly
    if product_image:
        urls.append(product_image)

    # 2. Fallback: try ASIN-based URL patterns
    if asin:
        urls += [
            f"https://m.media-amazon.com/images/P/{asin}._SL500_.jpg",
            f"https://m.media-amazon.com/images/I/{asin}._SL500_.jpg",
            f"https://m.media-amazon.com/images/I/{asin}._AC_SL500_.jpg",
        ]

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
        if p.get("badge"):
            value_score += 20
        scored.append((value_score, i, p))

    scored.sort(key=lambda x: -x[0])

    for score, idx, product in scored:
        if idx not in posted:
            print(f"  Picked: {product['title'][:50]}... (score: {score})")
            return idx, product

    print("  All deals posted — resetting rotation")
    state["posted_indices"] = []
    if scored:
        idx = scored[0][1]
        return idx, products[idx]
    return None, None


def format_deal_text(product):
    """Format a compelling deal post (text-only, image sent separately)."""
    title = product.get("title", "")
    price = product.get("price", 0)
    url = product.get("url", "")
    description = product.get("description", "")

    short_title = title[:80] + "..." if len(title) > 80 else title

    badge_emoji = ""
    badge = product.get("badge", "")
    if "Editor" in badge or "Pick" in badge:
        badge_emoji = "🔥"
    elif "Value" in badge or "Deal" in badge:
        badge_emoji = "💰"
    elif "Premium" in badge:
        badge_emoji = "⭐"

    price_str = f"${price:.2f}" if price else "Check price"
    short_desc = description[:200].strip() if description else ""

    text = f"""{badge_emoji} Deal of the Day: {short_title}

💵 {price_str}

{short_desc}

🛒 Shop now → {url}

#WorthItGoods #DealOfTheDay #AmazonDeals"""
    return text.strip()


def post_to_mastodon(text, img_bytes):
    """Post with image to Mastodon. Uploads media first, then attaches to status."""
    token = None
    with open(MASTODON_TOKEN_FILE) as f:
        for line in f:
            if line.startswith("MASTODON_ACCESS_TOKEN="):
                token = line.strip().split("=", 1)[1].strip().strip('"')
                break

    if not token:
        print("  ⚠️ No Mastodon token found")
        return False

    try:
        # Step 1: Upload image as media attachment
        media_id = None
        if img_bytes:
            boundary = b"----WebKitFormBoundary7MA4YWxkTrZu0gW"
            body = (
                b"--" + boundary + b"\r\n"
                b'Content-Disposition: form-data; name="file"; filename="product.jpg"\r\n'
                b"Content-Type: image/jpeg\r\n\r\n"
                + img_bytes + b"\r\n"
                b"--" + boundary + b"--\r\n"
            )
            media_req = urllib.request.Request(
                f"{MASTODON_API}/media",
                data=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": f"multipart/form-data; boundary={boundary.decode()}",
                },
                method="POST"
            )
            with urllib.request.urlopen(media_req, timeout=30) as resp:
                media_result = json.loads(resp.read().decode("utf-8"))
                media_id = media_result.get("id")
                if media_id:
                    print(f"  📷 Mastodon media upload: id={media_id}")

        # Step 2: Post status with media attachment (use JSON body, not form-encoded)
        status_data = {"status": text}
        if media_id:
            status_data["media_ids"] = [media_id]

        data = json.dumps(status_data).encode("utf-8")
        status_req = urllib.request.Request(
            f"{MASTODON_API}/statuses",
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Idempotency-Key": f"dotd-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            },
            method="POST"
        )
        with urllib.request.urlopen(status_req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            mastodon_id = result.get("id", "")
            if media_id:
                print(f"  ✅ Mastodon: https://mastodon.social/@{mastodon_id} (with image)")
            else:
                print(f"  ✅ Mastodon: https://mastodon.social/@{mastodon_id} (no image)")
            return True

    except Exception as e:
        print(f"  ❌ Mastodon failed: {e}")
        return False


def post_to_telegram(text, img_bytes):
    """Post with photo and caption to Telegram."""
    bot_token = os.environ.get("TELEGRAM_WIG_BOT_TOKEN")
    channel_id = os.environ.get("TELEGRAM_WIG_CHANNEL_ID", "@worthitgoods")

    if not bot_token:
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("TELEGRAM_WIG_BOT_TOKEN="):
                        bot_token = line.strip().split("=", 1)[1].strip().strip('"')
                        break

    if not bot_token:
        print("  ⚠️ No Telegram bot token found")
        return False

    try:
        if img_bytes:
            # Send as photo with caption (much higher engagement)
            boundary = "----Boundary7MA4YWxkTrZu0gW"
            body_parts = []
            body_parts.append(f"--{boundary}\r\n")
            body_parts.append('Content-Disposition: form-data; name="chat_id"\r\n\r\n')
            body_parts.append(f"{channel_id}\r\n")
            body_parts.append(f"--{boundary}\r\n")
            body_parts.append('Content-Disposition: form-data; name="photo"; filename="product.jpg"\r\n')
            body_parts.append("Content-Type: image/jpeg\r\n\r\n")
            body_parts_before = "".join(body_parts).encode("utf-8")
            body_parts_after = f"\r\n--{boundary}\r\n".encode("utf-8") + \
                               'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode("utf-8") + \
                               text.encode("utf-8") + \
                               f"\r\n--{boundary}--\r\n".encode("utf-8")

            body = body_parts_before + img_bytes + body_parts_after

            req = urllib.request.Request(
                f"{TELEGRAM_API}{bot_token}/sendPhoto",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST"
            )
        else:
            # Fallback: text-only message
            data = json.dumps({
                "chat_id": channel_id,
                "text": text,
                "disable_web_page_preview": False
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{TELEGRAM_API}{bot_token}/sendMessage",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            msg_id = result.get("result", {}).get("message_id", "?")
            if img_bytes:
                print(f"  ✅ Telegram: message {msg_id} (with photo)")
            else:
                print(f"  ✅ Telegram: message {msg_id} (no image)")
            return True

    except Exception as e:
        print(f"  ❌ Telegram failed: {e}")
        return False


def post_to_moltbook(text):
    """Post to Moltbook (text-only — no image support in their API)."""
    if not MOLTBOOK_CREDS.exists():
        print("  ⚠️ No Moltbook credentials found")
        return False

    with open(MOLTBOOK_CREDS) as f:
        creds = json.load(f)

    api_key = creds.get("api_key")
    if not api_key:
        print("  ⚠️ No Moltbook API key")
        return False

    first_line = text.split("\n")[0][:300]
    title = first_line.replace("🔥", "").replace("💰", "").replace("⭐", "").strip()

    content_lines = text.split("\n")[1:]
    content = "\n".join(content_lines).strip()
    if len(content) > 1900:
        content = content[:1850] + "...\n\nFull post → " + SITE_URL

    payload = json.dumps({
        "title": title,
        "content": content,
        "submolt": "general"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{MOLTBOOK_API}/posts",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "rockclaw-agent/1.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"  ✅ Moltbook: https://www.moltbook.com/u/rockclaw")
            return True
    except Exception as e:
        print(f"  ❌ Moltbook failed: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="WorthItGoods Deal of the Day")
    parser.add_argument("--dry-run", action="store_true", help="Print post without sending")
    parser.add_argument("--product", type=int, help="Force a specific product index")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== WorthItGoods Deal of the Day — {today} ===")

    products = load_products()
    print(f"Loaded {len(products)} products")

    state = load_state()

    if state.get("last_date") == today and not args.product:
        print("  Already posted today. Use --product to force.")
        return 0

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
    mastodon_ok = post_to_mastodon(text, img_bytes)
    telegram_ok = post_to_telegram(text, img_bytes)
    moltbook_ok = post_to_moltbook(text)

    if mastodon_ok or telegram_ok or moltbook_ok:
        posted = state.get("posted_indices", [])
        if idx not in posted:
            posted.append(idx)
        state["posted_indices"] = posted
        state["last_date"] = today
        save_state(state)
        print(f"\nPosted to: {'Mastodon ' if mastodon_ok else ''}{'Telegram ' if telegram_ok else ''}{'Moltbook ' if moltbook_ok else ''}")
    else:
        print("\n❌ All channels failed")

    print("=== Done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())