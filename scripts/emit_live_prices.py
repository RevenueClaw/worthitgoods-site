#!/usr/bin/env python3
"""Publish fresh WorthItGoods prices as a small JSON the static site can hydrate from.

Why: comparison pages bake prices into CTA/prose text at build time, but the site
was built from a stale copy of the product data, so visitors saw prices Amazon
would not honor (e.g. $18.98 shown vs $21.99 actual). That is a conversion killer.

This script reads the freshest product dataset (the repo copy that the price sweep
updates) and writes site/data/live-prices.json, keyed by ASIN, which price-sync.js
uses to correct displayed prices in the browser.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
CANDIDATES = [
    HOME / ".openclaw" / "workspace" / "worthitgoods-repo" / "worthitgoods_products.json",
    Path(__file__).resolve().parent.parent / "worthitgoods_products.json",
    HOME / "workspace" / "worthitgoods-site" / "worthitgoods_products.json",
]

OUT = Path(__file__).resolve().parent.parent / "assets" / "live-prices.json"


def newest_dataset():
    """Pick the most recently modified dataset that parses."""
    best = None
    for p in CANDIDATES:
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        mtime = p.stat().st_mtime
        if best is None or mtime > best[0]:
            best = (mtime, p, data)
    if best is None:
        raise SystemExit("no readable product dataset found")
    return best[1], best[2]


def main():
    src, data = newest_dataset()
    prods = data if isinstance(data, list) else list(data.values())
    checked = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    out = {}
    for p in prods:
        asin = p.get("asin")
        if not asin:
            continue
        price = p.get("price")
        try:
            price = float(price) if price not in (None, "") else None
        except (TypeError, ValueError):
            price = None
        if not price or price <= 0:
            continue
        out[asin] = {
            "price": round(price, 2),
            "availability": p.get("availability") or "",
            "checked": checked,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": str(src),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checked": checked,
        "prices": out,
    }, separators=(",", ":")))

    print(f"source: {src}")
    print(f"wrote {OUT} with {len(out)} priced ASINs (checked {checked})")


if __name__ == "__main__":
    main()