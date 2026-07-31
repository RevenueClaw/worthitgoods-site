#!/usr/bin/env python3
"""
Submit WorthItGoods sitemap to search engines for indexing.

Note: Google and Bing deprecated their sitemap ping endpoints.
Yandex and Seznam still accept pings. Add IndexNow key when available.

Runs after site rebuilds to ensure new content gets indexed.

Usage:
  python3 submit_sitemap.py [--dry-run]
"""

import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────
SITEMAP_URL = "https://www.worthitgoods.com/sitemap.xml"
SITE_URL = "https://www.worthitgoods.com"
# ──────────────────────────────────────────────────────────────────

SEARCH_ENGINES = [
    {
        "name": "Yandex",
        "url": "https://webmaster.yandex.com/ping",
        "params": {"sitemap": SITEMAP_URL},
        "method": "GET"
    },
    {
        "name": "Seznam (Czech)",
        "url": "https://search.seznam.cz/ping",
        "params": {"sitemap": SITEMAP_URL},
        "method": "GET"
    }
]


def ping_search_engine(engine):
    name = engine["name"]
    params = engine["params"]
    method = engine.get("method", "GET")

    try:
        if method == "GET":
            query_string = urllib.parse.urlencode(params)
            url = f"{engine['url']}?{query_string}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "WorthItGoodsBot/1.0 (sitemap submitter)"},
                method="GET"
            )
        elif method == "POST":
            data = json.dumps(params).encode("utf-8")
            req = urllib.request.Request(
                engine["url"],
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WorthItGoodsBot/1.0"
                },
                method="POST"
            )
        else:
            return {"name": name, "status": "error", "error": f"Unknown method: {method}"}

        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"name": name, "status": resp.status, "reason": "ok"}

    except urllib.error.HTTPError as e:
        return {"name": name, "status": e.code, "reason": str(e.reason)}
    except urllib.error.URLError as e:
        return {"name": name, "status": "error", "reason": str(e.reason)}
    except Exception as e:
        return {"name": name, "status": "error", "reason": str(e)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Submit sitemap to search engines")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    args = parser.parse_args()

    BASE_DIR = Path(__file__).parent.parent
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"=== WorthItGoods Sitemap Submission — {today} ===")
    print(f"Sitemap: {SITEMAP_URL}")

    results = []
    for engine in SEARCH_ENGINES:
        if args.dry_run:
            print(f"  Would ping {engine['name']}: {engine['url']}")
            results.append({"name": engine["name"], "status": "dry-run"})
            continue

        result = ping_search_engine(engine)
        results.append(result)

        if result["status"] in (200, 202):
            print(f"  ✅ {result['name']}: {result['status']}")
        else:
            print(f"  ⚠️ {result['name']}: {result['status']} — {result.get('reason', '?')}")

    success = sum(1 for r in results if r.get("status") in (200, 202, "dry-run"))
    print(f"\n  Submitted to {success}/{len(results)} search engines")

    log_path = BASE_DIR / "sitemap_submit_log.json"
    log = {"date": today, "results": results}
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())