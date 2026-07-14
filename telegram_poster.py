#!/usr/bin/env python3
"""
WorthItGoods Telegram Channel Auto-Poster
Posts new products to a Telegram channel as they're added to the site.
Designed to be run via cron.

Usage:
  TELEGRAM_WIG_BOT_TOKEN=xxx TELEGRAM_WIG_CHANNEL_ID=@worthitgoods python3 telegram_poster.py

First run: Posts all 149 products (with proper rate limiting, ~3 min)
Subsequent runs: Only posts new products not yet shared
"""

import json
import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# ─── CONFIG ───────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_WIG_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_ID = os.environ.get("TELEGRAM_WIG_CHANNEL_ID", "@worthitgoods")

BASE_DIR = Path(__file__).parent
PRODUCTS_FILE = BASE_DIR / "worthitgoods_products.json"
STATE_FILE = BASE_DIR / ".telegram_posted.json"
# ──────────────────────────────────────────────────────────────────

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def load_products():
    if not PRODUCTS_FILE.exists():
        print(f"❌ Products file not found: {PRODUCTS_FILE}")
        sys.exit(1)
    with open(PRODUCTS_FILE) as f:
        return json.load(f)


def load_state():
    if not STATE_FILE.exists():
        return {"posted_urls": [], "last_run": None}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_product(product):
    """Send a product post to Telegram. Returns True on success."""
    title = product["title"]
    desc = product["description"]
    url = product["url"]
    image = product.get("image", "")

    # Try with photo first (more engaging)
    if image:
        caption = f"<b>{title}</b>\n\n{url}"
        try:
            resp = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                json={
                    "chat_id": CHANNEL_ID,
                    "photo": image,
                    "caption": caption,
                    "parse_mode": "HTML",
                },
                timeout=20,
            )
            if resp.status_code == 200:
                return True
        except Exception:
            pass

    # Text fallback
    message = f"<b>{title}</b>\n\n{desc}\n\n🔗 <a href='{url}'>Shop on Amazon</a>"
    try:
        resp = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=20,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"  ⚠ Network error: {e}")
        return False


def verify_bot():
    """Check bot token and channel access before posting."""
    try:
        resp = requests.get(f"{TELEGRAM_API}/getMe", timeout=10)
        if resp.status_code != 200:
            print(f"❌ Invalid bot token. Check TELEGRAM_WIG_BOT_TOKEN")
            print(f"   Response: {resp.text}")
            sys.exit(1)
        bot = resp.json()["result"]
        print(f"✅ Bot: @{bot['username']}")
    except Exception as e:
        print(f"❌ Cannot reach Telegram API: {e}")
        sys.exit(1)

    # Send a health check message on first run
    state = load_state()
    if not state["posted_urls"]:
        try:
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": CHANNEL_ID,
                    "text": "🤖 <b>WorthItGoods Bot Active</b>\nI'll be posting hand-picked product finds here. Stay tuned!",
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            print(f"✅ Channel: {CHANNEL_ID}")
        except Exception as e:
            print(f"❌ Cannot access channel {CHANNEL_ID}: {e}")
            print("   Make sure the bot is added as an admin to the channel.")
            sys.exit(1)


def main():
    verify_bot()

    products = load_products()
    state = load_state()
    posted_urls = set(state.get("posted_urls", []))

    new_products = [p for p in products if p["url"] not in posted_urls]

    if not new_products:
        print(f"✓ No new products. ({len(products)} total, {len(posted_urls)} posted)")
        return

    total_new = len(new_products)
    is_bulk = total_new == len(products)

    if is_bulk:
        print(f"First run — posting all {total_new} products (this will take a few minutes)...")
    else:
        print(f"Found {total_new} new product{'s' if total_new != 1 else ''} to post...")

    posted = 0
    failed = 0

    for i, product in enumerate(new_products):
        if send_product(product):
            posted_urls.add(product["url"])
            posted += 1
            short = product["title"][:45]
            print(f"  ✓ [{posted}/{total_new}] {short}...")
        else:
            failed += 1
            short = product["title"][:45]
            print(f"  ✗ [{i+1}/{total_new}] Failed: {short}...")

        # Save after each post so we can resume if interrupted
        state["posted_urls"] = list(posted_urls)
        save_state(state)

        # Rate limit: 1 post per second to stay well under Telegram's 20/min limit
        time.sleep(1.2)

    print(f"\n{'─' * 40}")
    print(f"Done: {posted} posted, {failed} failed, {len(products) - len(posted_urls)} remaining")
    print(f"Next run will only post whatever's new.")

    # Set up for cron
    if is_bulk:
        print(f"\n💡 Tip: The initial bulk post is one-time. Schedule this to run daily:")
        print(f"   0 9 * * * cd {BASE_DIR} && TELEGRAM_WIG_BOT_TOKEN=$TOKEN python3 telegram_poster.py")


if __name__ == "__main__":
    main()