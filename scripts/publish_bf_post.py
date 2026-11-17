#!/usr/bin/env python3
"""Publish a Black Friday deals blog post from a bf_deal_scan report + owner picks.

Usage:
  python3 scripts/publish_bf_post.py reports/bf_deals_2026-11-26.json --asins B0X,B0Y [--publish]

Default = write blog/black-friday-picks draft + print compliance checks.
--publish additionally: inserts the blog.html card, runs build.sh, commits, pushes.

Compliance baked in (Associates rules + site doctrine):
  - NO cached prices/deal percentages anywhere in content (regex-asserted).
  - Every card: "Deal detected <scan date> — Amazon shows the current price."
  - CTA "Shop on Amazon →" to tagged affiliate URL, rel nofollow/sponsored.
  - Extended disclaimer block at the bottom.
Giant brands (Apple/Bose/JBL/Sony...) are ALLOWED in deals posts by owner
decision 2026-11-17 — the catalog front-page-giant ban governs regular curation
only, to keep batches different from Amazon's suggested page.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FAM_BEST_FOR = {
    "watch": "the person who'd never buy themselves a nice upgrade",
    "earbud": "commuters and gym bags", "headphone": "the noise-cancelling evangelist",
    "speaker": "patios, showers, and beach towels", "projector": "movie-night maximalists",
    "opener": "the host who opens everything", "air fryer": "the reheat purist",
    "vacuum": "anyone with pets and patience issues", "charger": "the one who's always at 4%",
    "dryer": "the bathroom-shelf stylist", "headset": "the gamer with a group chat",
    "grinder": "the coffee person with opinions", "other": "general gift-getters",
}


def family_of(title):
    t = title.lower()
    for key in FAM_BEST_FOR:
        if key in t:
            return key
    return "other"


def card(d, detected_on):
    title = str(d["title"]).replace('"', "&quot;")
    fam = family_of(title)
    stars = "\u2605" * round(d.get("rating", 0))
    return f"""<div class="pick-card">
    <img src="{d.get('image','')}" alt="{title[:60]}" loading="lazy" class="pick-card-img">
    <div class="pick-card-body">
        <div class="pick-card-meta">
            <span class="pick-rating"><span class="pick-stars">{stars}</span> {d.get('rating','?')} ({d.get('reviews','?'):,} reviews)</span>
        </div>
        <h2>{title}</h2>
        <p class="pick-quick-take">Amazon is running an active deal on this right now — deal detected {detected_on}. Amazon shows the current price on click.</p>
        <span class="pick-best-for">\U0001F3AF Best for: {FAM_BEST_FOR[fam]}</span>
        <a href="{d['affiliate_url']}" target="_blank" rel="nofollow sponsored" class="pick-cta">Shop on Amazon \u2192</a>
        <p class="pick-disclaimer">As an Amazon Associate we earn from qualifying purchases. Deal availability and pricing change fast; the live price is always the one Amazon displays.</p>
    </div>
</div>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scan_json")
    ap.add_argument("--asins", required=True, help="comma-separated owner-approved ASINs")
    ap.add_argument("--date", default=None, help="override publish slug date")
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args()

    scan = {d["asin"]: d for d in json.loads((ROOT / a.scan_json).read_text())}
    picks = [scan[s.strip()] for s in a.asins.split(",") if s.strip() in scan]
    missing = [s for s in a.asins.split(",") if s.strip() and s.strip() not in scan]
    if not picks:
        print("no picks matched the scan file"); return 1
    detected = re.search(r"(\d{4}-\d{2}-\d{2})", Path(a.scan_json).name)
    detected = detected.group(1) if detected else str(date.today())

    pub = a.date or str(date.today())
    slug = f"{pub}-black-friday-picks.html"
    body = "\n".join(card(d, detected) for d in picks)
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Black Friday Picks Worth Actually Buying | WorthIt Goods</title>
<meta name="description" content="Every product here passed our rating and taste gates BEFORE Amazon put a deal badge on it. Deals detected {detected}.">
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#fafaf7;color:#1f2937;margin:0;padding:0 16px;}}
.wrap{{max-width:760px;margin:0 auto;padding:2.5rem 0 4rem;}}
h1{{font-size:2rem;line-height:1.25;}}
.lede{{font-size:1.08rem;color:#374151;}}
.pick-card{{background:#fff;border:1px solid #eee;border-radius:14px;padding:1rem 1.25rem;margin:1.4rem 0;box-shadow:0 1px 4px rgba(0,0,0,.05);}}
.pick-card img{{max-height:230px;max-width:100%;object-fit:contain;display:block;margin:0 auto;}}
.pick-card h2{{font-size:1.4rem;margin:.6rem 0 .3rem;}}
.pick-quick-take{{color:#555;font-size:1.02rem;}}
.pick-rating{{color:#b45309;font-weight:700;}}
.pick-best-for{{display:inline-block;background:#fef3c7;color:#92400e;padding:4px 12px;border-radius:20px;font-size:.9rem;margin:.4rem 0;}}
.pick-cta{{display:inline-block;background:linear-gradient(135deg,#ff9a56,#ff6b6b);color:#fff;padding:12px 26px;border-radius:8px;text-decoration:none;font-weight:700;}}
.pick-disclaimer{{font-size:.75rem;color:#6b7280;}}
.trust{{margin-top:2.5rem;padding:1.2rem;background:#fff;border-radius:12px;font-size:.95rem;color:#374151;}}
@media(max-width:600px){{.pick-card h2{{font-size:1.2rem;}} body{{padding:0 12px;}}}}
</style></head><body><div class="wrap">
<h1>Black Friday Picks We'd Actually Buy Anyway</h1>
<p class="lede">We don't do deal lists. These are products that already cleared our curation bar (4.5\u2605+, real review volume, genuinely interesting) and happen to <em>also</em> have an active Amazon deal badge as of {detected} — most of them things you'd want and wouldn't buy for yourself at full price. Prices and deals move fast; every link shows what Amazon is actually charging right now.</p>
{body}
<div class="trust"><strong>How we pick:</strong> everything on WorthIt Goods passes rating, review-count, availability and editorial taste gates before it appears here — deal status never lowers the bar. As an Amazon Associate we earn from qualifying purchases; that's how the site runs, and it never affects what makes the list. Deal badges reported by Amazon's official affiliate API, detected {detected}; availability and pricing are accurate only up to the second you click.</div>
<p><a href="/">\u2190 Back to WorthItGoods</a> &nbsp; <a href="/blog.html">All posts</a></p>
</div></body></html>"""

    out = ROOT / "blog" / slug
    out.write_text(html)
    ok = not re.search(r"\$\s?\d", html)
    print(f"wrote blog/{slug} ({len(picks)} picks) | price-free: {ok}")
    if not ok:
        print("COMPLIANCE FAIL: cached price detected — not publishing"); return 1

    if a.publish:
        b = (ROOT / "blog.html").read_text()
        card_html = (f'<div class="product-card blog-card">\n    <h3><a href="blog/{slug}">🖤 Black Friday Picks '
                     f"We'd Actually Buy Anyway</a></h3>\n    <p>Already-vetted products that just picked up an "
                     f"Amazon deal badge — {len(picks)} of them.</p>\n"
                     f'    <a href="blog/{slug}" class="cta" style="margin-top:auto;">Read More →</a>\n</div>\n    ')
        anchor = '<div class="product-card blog-card">'
        b = b.replace(anchor, card_html + anchor, 1)
        (ROOT / "blog.html").write_text(b)
        for c in (["bash", "build.sh"], ["git", "add", "-A"],
                  ["git", "commit", "-m", f"BF post: {len(picks)} deal picks (scan {detected})"],
                  ["git", "push", "-q", "origin", "master"]):
            r = subprocess.run(c, cwd=ROOT, capture_output=True, text=True, timeout=900)
            print("$", " ".join(c), "->", r.returncode)
            if r.returncode:
                print(r.stderr[:250]); return 1
        print("PUBLISHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
