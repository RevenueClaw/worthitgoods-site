#!/usr/bin/env python3
"""
WorthItGoods Deal of the Day — auto-posts the best deal to Mastodon, Telegram, and Moltbook.

Picks the top deal based on great value rating, rotates through products daily.
Designed to run via cron.

Usage:
  python3 deal_of_the_day.py [--dry-run]

Environment:
  MASTODON_WIG_ACCESS_TOKEN - from mastodon-worthitgoods.env
  TELEGRAM_WIG_BOT_TOKEN / TELEGRAM_WIG_CHANNEL_ID - for Telegram posting
  Moltbook credentials at ~/.config/moltbook/credentials.json
"""

import json
import os
import sys
import random
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


def pick_deal(products, state):
    """Pick the best unpicked deal. If all posted, reset rotation."""
    posted = set(state.get("posted_indices", []))

    # Score products: prefer ones with prices, good badges, and shorter descriptions
    scored = []
    for i, p in enumerate(products):
        price = p.get("price")
        if price is None or price < 2.0:
            continue
        # Prefer products with better value (subjective: middle-priced items tend to be best deals)
        value_score = 50 - abs(price - 30)  # Peak at $30
        if p.get("badge"):
            value_score += 20
        scored.append((value_score, i, p))

    # Sort by score descending
    scored.sort(key=lambda x: -x[0])

    # First try: pick highest-scored unpicked
    for score, idx, product in scored:
        if idx not in posted:
            print(f"  Picked: {product['title'][:50]}... (score: {score})")
            return idx, product

    # All posted — reset and pick the best overall
    print("  All deals posted — resetting rotation")
    state["posted_indices"] = []
    if scored:
        idx = scored[0][1]
        return idx, products[idx]
    return None, None


def format_deal_text(product):
    """Format a compelling deal post."""
    title = product.get("title", "")
    price = product.get("price", 0)
    url = product.get("url", "")
    asin = product.get("asin", "")
    description = product.get("description", "")

    # Clean title
    short_title = title[:80] + "..." if len(title) > 80 else title

    # Build post
    badge_emoji = ""
    badge = product.get("badge", "")
    if "Editor" in badge or "Pick" in badge:
        badge_emoji = "🔥"
    elif "Value" in badge or "Deal" in badge:
        badge_emoji = "💰"
    elif "Premium" in badge:
        badge_emoji = "⭐"

    price_str = f"${price:.2f}" if price else "Check price"

    # Short description
    short_desc = description[:200].strip() if description else ""

    text = f"""{badge_emoji} Deal of the Day: {short_title}

💵 {price_str}

{short_desc}

🛒 Shop now → {url}

#WorthItGoods #DealOfTheDay #AmazonDeals"""

    return text.strip()


def post_to_mastodon(text):
    """Post to WorthItGoods Mastodon account."""
    # Read token
    token = None
    with open(MASTODON_TOKEN_FILE) as f:
        for line in f:
            if line.startswith("MASTODON_ACCESS_TOKEN="):
                token = line.strip().split("=", 1)[1].strip().strip('"')
                break

    if not token:
        print("  ⚠️ No Mastodon token found")
        return False

    data = json.dumps({"status": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{MASTODON_API}/statuses",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Idempotency-Key": f"dotd-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"  ✅ Mastodon: https://mastodon.social/@{result.get('id','')}")
            return True
    except Exception as e:
        print(f"  ❌ Mastodon failed: {e}")
        return False


def post_to_telegram(text):
    """Post to WorthItGoods Telegram channel."""
    bot_token = os.environ.get("TELEGRAM_WIG_BOT_TOKEN")
    channel_id = os.environ.get("TELEGRAM_WIG_CHANNEL_ID", "@worthitgoods")

    if not bot_token:
        # Try reading from .env
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

    data = json.dumps({
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{TELEGRAM_API}{bot_token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"  ✅ Telegram: message {result.get('result',{}).get('message_id','?')}")
            return True
    except Exception as e:
        print(f"  ❌ Telegram failed: {e}")
        return False


def post_to_moltbook(text):
    """Post to Moltbook agent social network."""
    if not MOLTBOOK_CREDS.exists():
        print("  ⚠️ No Moltbook credentials found")
        return False

    with open(MOLTBOOK_CREDS) as f:
        creds = json.load(f)

    api_key = creds.get("api_key")
    if not api_key:
        print("  ⚠️ No Moltbook API key")
        return False

    # Extract title from the first line
    first_line = text.split("\n")[0][:300]
    title = first_line.replace("🔥", "").replace("💰", "").replace("⭐", "").strip()

    # Content: everything after the title
    content_lines = text.split("\n")[1:]
    content = "\n".join(content_lines).strip()
    # Truncate for Moltbook
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
            result = json.loads(resp.read().decode("utf-8"))
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

    # Check if already posted today
    if state.get("last_date") == today and not args.product:
        print("  Already posted today. Use --product to force.")
        return 0

    # Pick deal
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

    if args.dry_run:
        print("\n=== DRY RUN — not posting ===")
        return 0

    # Post to all channels
    print("\nPosting...")
    mastodon_ok = post_to_mastodon(text)
    telegram_ok = post_to_telegram(text)
    moltbook_ok = post_to_moltbook(text)

    # Update state
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