#!/usr/bin/env python3
"""Inject live catalog/traffic figures into the BUILT press page (_site/press.html).

Product count: exact length of data/sample_products.valid.json (the same file
the site is generated from, so the press page cannot claim more than it serves).
Readership: latest gateway press_stats archive (weekly Cloudflare edge-analytics
job, ~/.openclaw/workspace/data/press_stats_YYYY-MM-DD.json); if absent, the
source line stays untouched. Idempotent: anchors on the sentence, not the number.
"""
import glob
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRESS = ROOT / "_site" / "press.html"
CATALOG = ROOT / "data" / "sample_products.valid.json"
ARCHIVE_GLOB = os.path.expanduser("~/.openclaw/workspace/data/press_stats_*.json")


REPO_STATS = ROOT / "data" / "site_stats.json"

def latest_traffic():
    # 1) committed repo stats (present on CF Pages builders too)
    if REPO_STATS.exists():
        try:
            d = json.loads(REPO_STATS.read_text())
            u = (d.get("sites", {}).get("worthitgoods") or {}).get("uniques_30d")
            if u:
                return int(u), d.get("asof") or ""
        except Exception:
            pass
    # 2) fallback: latest gateway archive (local builds)
    best = None
    for f in sorted(glob.glob(ARCHIVE_GLOB)):
        try:
            d = json.loads(Path(f).read_text())
        except Exception:
            continue
        u = (d.get("sites", {}).get("worthitgoods") or {}).get("uniques_30d")
        if u:
            best = (int(u), d.get("asof") or "")
    return best


def main():
    if not PRESS.exists():
        print("no _site/press.html — skipping")
        return 0
    s = PRESS.read_text()

    n = 0
    try:
        n = len(json.loads(CATALOG.read_text()))
    except Exception as e:
        print(f"catalog unreadable: {e}")
    if n >= 50:
        s = re.sub(r"<li>\d[\d,]*\+? products tracked",
                   f"<li>{n:,} products tracked", s, count=1)
        print(f"press product count -> {n:,}")

    traffic = latest_traffic()
    if traffic:
        u, asof = traffic
        month = ""
        try:
            from datetime import datetime
            month = datetime.strptime(asof, "%Y-%m-%d").strftime("%B %Y")
        except Exception:
            pass
        repl = f"<li>~{u:,} readers/month"
        if month:
            repl += f" (as of {month})"
        repl += ", primarily organic search"
        s2 = re.sub(r"<li>[Rr]oughly \d[\d,]*\+? readers/month[^<]*organic search",
                    repl, s, count=1)
        if s2 == s:  # already injected once (idempotent re-run)
            s2 = re.sub(r"<li>~?\d[\d,]* readers/month[^<]*organic search",
                        repl, s, count=1)
        s = s2
        print(f"press readership -> ~{u:,}/30d ({asof})")

    PRESS.write_text(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
