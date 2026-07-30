#!/usr/bin/env python3
"""
Post WorthItGoods content to Moltbook (agent social network).

Posts a comparison article to Moltbook with affiliate link.
Run via cron when new comparisons are published.

Usage:
  python3 post_to_moltbook.py --comparison camping-lantern-vs-neck-light-vs-spotlight

Requires: Moltbook API key in ~/.config/moltbook/credentials.json
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ─── CONFIG ───────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
COMPARISONS_DIR = BASE_DIR / "comparisons"
CREDENTIALS_FILE = Path.home() / ".config" / "moltbook" / "credentials.json"
MOLTBOOK_API = "https://www.moltbook.com/api/v1"
SITE_URL = "https://www.worthitgoods.com"
MAX_CONTENT_LENGTH = 2000  # Moltbook character limit
# ──────────────────────────────────────────────────────────────────


def load_credentials():
    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: Moltbook credentials not found at {CREDENTIALS_FILE}")
        print("Create the file with: {\"api_key\": \"YOUR_KEY\", \"agent_name\": \"rockclaw\"}")
        sys.exit(1)
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)


def get_comparison_meta(slug: str) -> dict:
    """Get comparison title and description from the HTML file."""
    html_path = COMPARISONS_DIR / f"{slug}.html"
    if not html_path.exists():
        print(f"ERROR: Comparison not found: {html_path}")
        sys.exit(1)

    with open(html_path) as f:
        html = f.read()

    # Extract title from <title> tag or <h1>
    title = ""
    import re
    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
    else:
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        if h1_match:
            title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()

    # Extract meta description
    meta_match = re.search(r'<meta name="description" content="(.*?)"', html)
    description = meta_match.group(1).strip() if meta_match else ""

    # Get first product image (for thumbnail)
    img_match = re.search(r'<img[^>]+src="(https://m\.media-amazon\.com[^"]+)"', html)
    image_url = img_match.group(1) if img_match else ""

    return {
        "title": title or slug.replace("-", " ").title(),
        "description": description,
        "image_url": image_url,
        "url": f"{SITE_URL}/comparisons/{slug}.html"
    }


def post_to_moltbook(api_key: str, content: str, title: str = "", submolt: str = "general"):
    """Post content to Moltbook. Returns response data."""
    url = f"{MOLTBOOK_API}/posts"
    payload_dict = {
        "content": content,
        "submolt": submolt
    }
    if title:
        payload_dict["title"] = title[:300]
    payload = json.dumps(payload_dict).encode("utf-8")

    req = urllib.request.Request(
        url,
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
            return {
                "status": resp.status,
                "data": json.loads(resp.read().decode("utf-8"))
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return {
            "status": e.code,
            "error": error_body[:500]
        }
    except urllib.error.URLError as e:
        return {
            "status": 0,
            "error": str(e.reason)
        }


def build_post_text(meta: dict) -> str:
    """Build a compelling Moltbook post from comparison metadata."""
    title = meta["title"]
    description = meta["description"]
    url = meta["url"]

    # Clean up the title - remove site name if present
    clean_title = title.replace(" - WorthItGoods", "").replace(" | WorthItGoods", "").strip()

    # Build the post content
    post = f"📊 {clean_title}\n\n"

    # Add description (truncated)
    if description:
        post += f"{description[:300].strip()}\n\n"

    # Add the link
    post += f"Full comparison → {url}"

    # Ensure we don't exceed max length
    if len(post) > MAX_CONTENT_LENGTH:
        post = post[:MAX_CONTENT_LENGTH - 50] + "...\n\nFull comparison → " + url
        if len(post) > MAX_CONTENT_LENGTH:
            post = post[:MAX_CONTENT_LENGTH - 3] + "..."

    return post


def main():
    parser = argparse.ArgumentParser(description="Post WorthItGoods comparison to Moltbook")
    parser.add_argument("--comparison", required=True, help="Comparison slug (e.g., camping-lantern-vs-neck-light-vs-spotlight)")
    parser.add_argument("--submolt", default="general", help="Moltbook submolt/category")
    parser.add_argument("--dry-run", action="store_true", help="Print post without sending")
    args = parser.parse_args()

    slug = args.comparison
    print(f"=== Posting to Moltbook: {slug} ===")

    # Load creds
    creds = load_credentials()
    api_key = creds.get("api_key")
    agent_name = creds.get("agent_name", "rockclaw")
    print(f"Agent: {agent_name}")

    # Get comparison metadata
    meta = get_comparison_meta(slug)
    print(f"Title: {meta['title']}")
    print(f"URL: {meta['url']}")

    # Build post content
    post_text = build_post_text(meta)
    print(f"\nPost content ({len(post_text)} chars):")
    print("─" * 40)
    print(post_text)
    print("─" * 40)

    if len(post_text) > MAX_CONTENT_LENGTH:
        print(f"\n⚠️  WARNING: Post exceeds {MAX_CONTENT_LENGTH} char limit by {len(post_text) - MAX_CONTENT_LENGTH} chars")

    if args.dry_run:
        print("\n=== DRY RUN — not posting ===")
        return 0

    # Post
    print(f"\nPosting to Moltbook ({args.submolt})...")
    result = post_to_moltbook(api_key, post_text, meta["title"], args.submolt)

    if result["status"] in (200, 201):
        print(f"✅ Posted successfully!")
        post_id = result.get("data", {}).get("id", "unknown")
        print(f"Post ID: {post_id}")
        print(f"View at: https://www.moltbook.com/u/{agent_name}")
    else:
        print(f"❌ Failed ({result['status']}): {result.get('error', 'Unknown error')}")
        sys.exit(1)

    print("=== Done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())