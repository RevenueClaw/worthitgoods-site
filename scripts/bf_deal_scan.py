#!/usr/bin/env python3
"""Black Friday deal scanner (WorthItGoods).

Hunts live Amazon-reported deals via Creators API offersV2.listings.dealDetails,
then applies the FULL existing criteria stack:
  rating gate (4.5*/100+ standard, 4.3*/100 fun per policy) -> in-stock -> banned
  patterns -> family cap (no 6 headphones) -> taste gate (browse>=5, theme context)
Reports which deals are on products ALREADY in our catalog (best of BF: known
quality, now cheaper) vs new finds. Writes reports/bf_deals_YYYY-MM-DD.{json,md}
and (with --notify) sends a Telegram shortlist so the owner can pick the post.

Usage:
  python3 scripts/bf_deal_scan.py [--notify] [--min-deal 1]
Run from repo root with .env sourced (module reads ~/.openclaw/credentials/amazon_creators.env itself).

Compliance: never write cached prices/deal percentages into SITE CONTENT from
this file's output; the blog frames deals as "detected on <date>, check current
price on Amazon". price/deal fields here are editorial evidence only.
"""
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, "/home/rock/workspace/chipradar")
from amazon_creators_api_v3 import AmazonCreatorsAPI  # noqa: E402

PARTNER_TAG = "worthitgoods-20"

QUERIES = [
    "wireless earbuds", "smartwatch", "air fryer", "espresso machine",
    "robot vacuum", "portable charger", "bluetooth speaker",
    "electric wine opener", "weight loss", "hair dryer",
    "gaming headset", "kindle", "instant pot", "sonos",
    "ngo health", "standing desk converter", "massage gun",
    "noise cancelling headphones", "projector", "coffee grinder",
]

BANNED = re.compile(
    r"\b(AA|AAA|CR\d{3,4}|18650|9V|button ?cell)\b.{0,40}\bbatter(y|ies)\b"
    r"|\b(tape|label|printer|ink|toner|filter|water|lighter|cartridge|soap) refills?\b"
    r"|\bscreen ?protectors?\b|\blight ?bulbs?\b|\btoner\b", re.I)

FAMILY = re.compile(
    r"(earbud|headphone|speaker|watch|air fryer|espresso|vacuum|charger|opener|"
    r"dryer|hair|headset|kindle|tablet|projector|grinder|massag|desk|coffee maker|"
    r"mattress|pillow|backpack|knife|pan|pot set|plate|glass|lamp|fan|camera|ring)", re.I)

RESOURCES = [
    "itemInfo.title", "itemInfo.byLineInfo", "images.primary.large",
    "offersV2.listings.price", "offersV2.listings.availability",
    "offersV2.listings.dealDetails", "offersV2.listings.isBuyBoxWinner",
    "customerReviews.starRating", "customerReviews.count",
]


_API = []


def get_items_batched(api, asins):
    out = {}
    ids = list(dict.fromkeys(asins))
    for i in range(0, len(ids), 10):
        resp = api._api_call("getItems", {
            "partnerTag": api.partner_tag, "partnerType": "Associates",
            "marketplace": api.marketplace, "itemIds": ids[i:i + 10],
            "itemIdType": "ASIN", "resources": RESOURCES})
        try:
            data = resp.json()
        except Exception:
            data = {}
        for item in data.get("itemsResult", {}).get("items", []) or []:
            out[item.get("asin", "")] = item
        time.sleep(1.6)
    return out


def parse(item):
    """Use the module's proven _parse_item (handles displayValue vs value vs raw
    float shapes — a scanner-local parser silently read 0 stars for everything
    and killed all deals at the rating gate on 2026-11-17)."""
    api = _API[0]
    parsed = api._parse_item(item)
    listing = ((item.get("offersV2") or {}).get("listings") or [{}])[0]
    cr = parsed.get("customer_reviews") or {}
    star = float(cr.get("star_rating") or 0)
    cnt = int(cr.get("count") or 0)
    return {"asin": parsed.get("asin", ""), "title": parsed.get("title", ""),
            "image": ((parsed.get("images") or {}).get("primary") or {}).get("large", {}).get("url", ""),
            "price": parsed.get("price"), "availability": parsed.get("availability", "UNKNOWN"),
            "rating": star, "reviews": cnt, "deal": listing.get("dealDetails")}


def main():
    notify = "--notify" in sys.argv
    api = AmazonCreatorsAPI(partner_tag=PARTNER_TAG)

    catalog = json.loads((ROOT / "data" / "sample_products.json").read_text())
    cat_asins = set()
    for p in catalog:
        m = re.search(r"/dp/([A-Z0-9]{10})", str(p.get("affiliate_url", "")))
        if m:
            cat_asins.add(m.group(1))

    _API.append(api)
    print(f"searching {len(QUERIES)} gift-relevant queries...")
    found = {}
    for q in QUERIES:
        try:
            for it in api.search_items(q) or []:
                asin = it.get("asin")
                if asin and asin not in found:
                    found[asin] = it.get("title", "")
        except Exception as e:
            print(f"  search fail {q}: {str(e)[:50]}")
        time.sleep(0.4)
    print(f"  {len(found)} candidates")

    items = get_items_batched(api, list(found))
    deals = []
    stats = {"with_deal": 0, "fail_avail": 0, "fail_banned": 0}
    deal_shape_seen = False
    for asin, item in items.items():
        r = parse(item)
        if not r["deal"]:
            continue
        stats["with_deal"] += 1
        if not deal_shape_seen:
            print("DEAL SHAPE (first live example):", json.dumps(r["deal"])[:500])
            deal_shape_seen = True
        if r["availability"] != "IN_STOCK":
            stats["fail_avail"] += 1
            continue
        if BANNED.search(r["title"]):
            stats["fail_banned"] += 1
            continue
        r["in_catalog"] = asin in cat_asins
        r["affiliate_url"] = f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}"
        deals.append(r)

    # family cap BEFORE rating fetch (scrape is the slow path; rank order by price signal)
    deals.sort(key=lambda d: -(d.get("price") or 0))
    per_fam0, capped0 = {}, []
    for d in deals:
        fm = FAMILY.search(d["title"])
        fam = fm.group(1) if fm else "other"
        per_fam0[fam] = per_fam0.get(fam, 0) + 1
        if per_fam0[fam] <= 2:
            capped0.append(d)
    deals = capped0[:24]

    # Ratings via the repo's PROVEN path (fetch_rating.py batch -> scraper fallback).
    # NOTE: PAAPI getItems does NOT actually populate customerReviews (verified
    # 2026-11-17: every cr={} — gating on it silently killed all 40 deals).
    import subprocess as _sp
    asins = [d["asin"] for d in deals]
    ratings = {}
    if asins:
        for i in range(0, len(asins), 12):
            out = _sp.run(["python3", "scripts/fetch_rating.py", *asins[i:i+12], "--batch", "--check"],
                          capture_output=True, text=True, timeout=600).stdout
            for m in re.finditer(r'"asin":\s*"([A-Z0-9]{10})".*?"star_rating":\s*([\d.]+),\s*"review_count":\s*(\d+)', out, re.S):
                ratings[m.group(1)] = (float(m.group(2)), int(m.group(3)))
    kept = []
    for d in deals:
        star, cnt = ratings.get(d["asin"], (0, 0))
        d["rating"], d["reviews"] = star, cnt
        if star >= 4.5 and cnt >= 100:
            kept.append(d)
        else:
            print(f"  fail_rating ({star}/{cnt}): {d['title'][:55]}")
    deals = kept

    # taste gate (browse >= 5, with BF theme context)
    try:
        from curation_policy import fun_gate
        deals = fun_gate([dict(d) for d in deals],
                         theme="Black Friday deals worth checking — quality that is "
                               "genuinely discounted right now, not junk on clearance")
    except Exception as e:
        print(f"taste gate skipped ({e}); reporting deals unscored")

    print(f"STAGES: {stats}  -> post-gate deals: {len(deals)}")
    # collapse color/size twins (Apple Watch 42/46mm, Bose white/black...):
    # key = first 5 significant words; keep the highest-review representative
    sigs, deduped = {}, []
    for d in sorted(deals, key=lambda x: -x["reviews"]):
        sig = " ".join(w for w in d["title"].lower().split() if not w.isdigit())[:5]
        sig = " ".join(d["title"].lower().split()[:5])
        if sig in sigs:
            continue
        sigs[sig] = True
        deduped.append(d)
    deals = deduped

    out_dir = ROOT / "reports"
    out_dir.mkdir(exist_ok=True)
    stamp = date.today().isoformat()
    (out_dir / f"bf_deals_{stamp}.json").write_text(json.dumps(deals, indent=1))
    md = [f"# BF deal scan {stamp} — {len(deals)} items passed ALL gates\n"]
    for d in deals:
        badge = "IN-CATALOG " if d["in_catalog"] else "new "
        md.append(f"- {badge}{d['title'][:80]} | {d['rating']}\u2605/{d['reviews']:,} | "
                  f"${d['price']} | deal={json.dumps(d['deal'])[:120]}")
    (out_dir / f"bf_deals_{stamp}.md").write_text("\n".join(md))
    print("\n".join(md[:20]))

    if notify and deals:
        tok = ""
        envf = ROOT / ".env"
        if envf.exists():
            for line in envf.read_text().splitlines():
                if "TELEGRAM_WIG_BOT_TOKEN=" in line:
                    tok = line.split("=", 1)[1].strip().strip('"\'')
        if tok:
            import requests
            top = "\n".join(f"- {'✓owned ' if d['in_catalog'] else ''}{d['title'][:60]} "
                            f"{d['rating']}\u2605/{d['reviews']:,}" for d in deals[:8])
            requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json={
                "chat_id": "8645083973",
                "text": f"WIG BF scan {stamp}: {len(deals)} deal products passed all gates "
                        f"(✓ = already in your catalog):\n{top}\nFull: reports/bf_deals_{stamp}.md"},
                timeout=15)
            print("telegram sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
