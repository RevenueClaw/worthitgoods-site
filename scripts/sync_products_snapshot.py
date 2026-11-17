#!/usr/bin/env python3
"""Regenerate worthitgoods_products.json (PAAPI snapshot schema) from the
validated site catalog (data/sample_products.valid.json).

Background: the site builds from data/sample_products*.json, but
telegram_poster.py / batch_price_sweep.py / scout_comparisons.py read the
legacy worthitgoods_products.json snapshot. When weekly curation batches were
merged only into the build source, the snapshot silently drifted (147 stale vs
246 live) and downstream automation posted/rechecked dead products. Wired into
build.sh so the snapshot can never lag the catalog again.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "sample_products.valid.json"
DST = ROOT / "worthitgoods_products.json"

ASIN_RE = re.compile(r"(?:/dp/|/go/asin/)([A-Z0-9]{10})")


def main():
    if not SRC.exists():
        print(f"missing {SRC} — run filter_valid_products.py first")
        return 1
    catalog = json.loads(SRC.read_text())

    old_by_asin = {}
    if DST.exists():
        try:
            for p in json.loads(DST.read_text()):
                a = p.get("asin")
                if a:
                    old_by_asin[a] = p
        except Exception:
            pass

    out, skipped = [], 0
    for p in catalog:
        url = p.get("affiliate_url") or p.get("url") or ""
        m = ASIN_RE.search(url)
        asin = m.group(1) if m else (p.get("asin") or "")
        if not asin:
            skipped += 1
            continue
        desc = (p.get("description") or "").strip()
        old = old_by_asin.get(asin, {})
        feats = p.get("features") or old.get("features") or []
        if not feats and p.get("blurb"):
            feats = [p["blurb"].strip()]
        try:
            price = float(p.get("price") or old.get("price") or 0)
        except (TypeError, ValueError):
            price = 0.0
        out.append({
            "asin": asin,
            "title": p.get("title") or old.get("title") or "",
            "url": url,
            "affiliate_url": url,
            "price": price,
            "price_display": f"${price:,.2f}",
            "currency": "USD",
            "availability": p.get("availability") or "In Stock",
            "description": desc,
            "features": feats,
            "image": p.get("image") or old.get("image") or "",
            "category": p.get("category") or old.get("category") or "",
        })

    out.sort(key=lambda x: x["title"].lower())
    tmp = DST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=2))
    tmp.replace(DST)
    print(f"products snapshot synced: {len(out)} items "
          f"(was {len(old_by_asin)} legacy, {skipped} skipped-no-asin)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
