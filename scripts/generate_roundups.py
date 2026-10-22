#!/usr/bin/env python3
"""Programmatic category roundup generator for WorthItGoods.

Generates high-intent "Best <Category> Picks (2026)" pages from the real
product catalog (data/sample_products.json). All prices come from the catalog —
nothing is invented. Each page carries ItemList + FAQPage JSON-LD so search and
answer engines can quote it.

Output: comparisons/best-<cat-slug>-<year>.html  (+ best-of/index.html)

Usage: python3 scripts/generate_roundups.py
"""
import html
import json
import re
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PRODUCTS = REPO / "data" / "sample_products.json"
OUT_DIR = REPO / "comparisons"
INDEX_DIR = REPO / "best-of"
SITE = "https://www.worthitgoods.com"
YEAR = 2026
MIN_PER_CATEGORY = 4
MAX_PER_PAGE = 8

CSS = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="../style.css">
<style>
body { background:#f8f9fa; }
.article-header { background:linear-gradient(135deg,#0f2027,#203a43,#2c5364,#436b7a); background-size:400% 400%; animation:gradient-shift 20s ease infinite; color:#fff; padding:3.5rem 2rem; text-align:center; }
@keyframes gradient-shift { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
.article-header h1 { font-size:2.3rem; line-height:1.2; max-width:760px; margin:0 auto 1rem; }
.article-header .subtitle { font-size:1.05rem; color:rgba(255,255,255,0.85); max-width:620px; margin:0 auto; }
.article-content { max-width:800px; margin:0 auto; padding:2rem 24px 4rem; }
.article-content p { color:#333; line-height:1.8; margin-bottom:1.25rem; }
.article-content h2 { font-size:1.5rem; margin:2.4rem 0 1rem; color:#1a1a1a; border-bottom:2px solid #f0f0f0; padding-bottom:8px; }
.article-product-card { background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:22px; margin:1.5rem 0; box-shadow:0 2px 8px rgba(0,0,0,0.04); display:flex; gap:18px; flex-wrap:wrap; }
.article-product-card img { width:120px; height:120px; object-fit:contain; border-radius:10px; background:#fff; }
.article-product-card .pc-body { flex:1; min-width:220px; }
.article-product-card h3 { margin:0 0 6px; font-size:1.15rem; }
.article-product-card .rank { color:#ff6b6b; font-weight:700; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.04em; }
.article-product-card .blurb { color:#4b5563; font-size:0.95rem; margin:6px 0 10px; }
.article-product-card .price { font-weight:700; color:#111827; }
.article-cta { display:inline-block; padding:11px 20px; background:linear-gradient(135deg,#ff9a56,#ff6b6b); color:#fff; text-decoration:none; border-radius:8px; font-weight:600; margin-top:8px; }
.article-cta:hover { transform:translateY(-1px); box-shadow:0 4px 12px rgba(255,107,53,0.3); }
.article-content a.sup { color:#2563eb; text-decoration:underline; }
.related { margin-top:2.5rem; padding:20px; background:#fff; border:1px solid #e5e7eb; border-radius:12px; }
.related h3 { margin:0 0 10px; font-size:1.05rem; }
.related li { margin:6px 0; }
.footer-note { color:#6b7280; font-size:0.8rem; margin-top:2.5rem; }
</style>"""

HEADER = """<header class="site-header" style="background:#fff;border-bottom:1px solid #eee;padding:14px 20px;">
  <a href="/" style="font-weight:800;color:#111827;text-decoration:none;font-size:1.05rem;">WorthItGoods</a>
  <span style="float:right;"><a href="/" style="margin-left:16px;color:#6b7280;text-decoration:none;">Home</a>
  <a href="/blog.html" style="margin-left:16px;color:#6b7280;text-decoration:none;">Blog</a>
  <a href="/best-of/" style="margin-left:16px;color:#6b7280;text-decoration:none;">Best-Of</a></span>
</header>"""

FOOTER = """<footer style="text-align:center;padding:28px;color:#9ca3af;font-size:0.8rem;border-top:1px solid #eee;">
  <p>&copy; 2026 WorthItGoods &middot; <a href="/" style="color:#9ca3af;">Home</a> &middot; <a href="/blog.html" style="color:#9ca3af;">Blog</a></p>
  <p style="margin-top:8px;">Some links are affiliate links. We may earn a commission at no extra cost to you.</p>
</footer>"""


def slugify(s):
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:50].strip("-")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def load_products():
    data = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    out = []
    for p in data:
        cat = (p.get("category") or "").strip()
        if not cat or cat == "?":
            continue
        try:
            price = float(p["price"]) if p.get("price") not in (None, "", "None") else None
        except (TypeError, ValueError):
            price = None
        out.append({
            "title": p.get("title", "").strip(),
            "image": p.get("image", ""),
            "blurb": (p.get("blurb") or p.get("description") or "").strip(),
            "url": p.get("affiliate_url", ""),
            "price": price,
            "asin": p.get("asin", ""),
            "badge": p.get("badge", ""),
            "fun": p.get("_fun_score", 0) or 0,
            "cat": cat,
        })
    return out


def card_html(p, rank):
    price = f'<span class="price">${p["price"]:.2f}</span>' if p["price"] is not None else ""
    img = f'<img src="{esc(p["image"])}" alt="{esc(p["title"])}" loading="lazy" width="120" height="120">' if p["image"] else ""
    badge = f' <span style="color:#059669;font-size:0.8rem;font-weight:600;">{esc(p["badge"])}</span>' if p["badge"] else ""
    short = p["title"].split(" - ")[0].split(",")[0][:70]
    return f"""<div class="article-product-card">
  {img}
  <div class="pc-body">
    <div class="rank">#{rank} pick</div>
    <h3>{esc(short)}{badge}</h3>
    <p class="blurb">{esc(p["blurb"][:220])}</p>
    {price}
    <div><a class="article-cta" href="{esc(p["url"])}" target="_blank" rel="noopener nofollow">Check price on Amazon &rarr;</a></div>
  </div>
</div>"""


def build_page(cat, items, siblings):
    slug = slugify(cat)
    name = esc(cat)
    title = f"Best {name} Picks ({YEAR}) — WorthIt Goods"
    desc = f"Our hand-picked best {cat.lower()} finds for {YEAR} — real picks, real prices, no filler."
    cards = "\n".join(card_html(p, i + 1) for i, p in enumerate(items))
    cheapest = min((p for p in items if p["price"] is not None), key=lambda p: p["price"], default=None)
    faq = [
        {"@type": "Question", "name": f"What is the best {cat.lower()} pick right now?",
         "acceptedAnswer": {"@type": "Answer",
                            "text": f"Our top {cat.lower()} pick is {items[0]['title'].split(' - ')[0]}."}},
    ]
    if cheapest:
        faq.append({"@type": "Question", "name": f"What is the cheapest {cat.lower()} pick?",
                    "acceptedAnswer": {"@type": "Answer",
                                       "text": f"The cheapest on this list is {cheapest['title'].split(' - ')[0]} at ${cheapest['price']:.2f}."}})
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": f"{SITE}/#org", "name": "WorthItGoods", "url": f"{SITE}/"},
            {"@type": "WebSite", "@id": f"{SITE}/#website", "url": f"{SITE}/", "name": "WorthItGoods"},
            {"@type": "ItemList", "name": f"Best {cat} picks {YEAR}",
             "itemListElement": [
                 {"@type": "ListItem", "position": i + 1, "name": p["title"],
                  "url": p["url"] or f"{SITE}/"}
                 for i, p in enumerate(items)
             ]},
            {"@type": "FAQPage", "mainEntity": faq},
        ],
    }
    related = "".join(
        f'<li><a class="sup" href="/comparisons/best-{slugify(s)}-{YEAR}.html">Best {esc(s)} Picks ({YEAR})</a></li>'
        for s in siblings[:6]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{CSS}
<title>{title}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}/comparisons/best-{slug}-{YEAR}.html">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<script type="application/ld+json">
{json.dumps(structured, indent=2)}
</script>
</head>
<body>
{HEADER}
<div class="article-header">
  <h1>Best {name} Picks We Actually Recommend ({YEAR})</h1>
  <p class="subtitle">{esc(desc)}</p>
</div>
<div class="article-content">
  <p>We went through our {name.lower()} shelf and pulled the ones worth your money — no filler, no
  sponsored placements. Prices below are the ones we last verified; always check the current price on
  Amazon before buying.</p>
  {cards}
  <div class="related">
    <h3>More worth-it lists</h3>
    <ul>{related}</ul>
  </div>
  <p class="footer-note">Prices change often. This page was generated from our curated catalog on {date.today().isoformat()}.
  Some links are affiliate links — we may earn a small commission at no extra cost to you.</p>
</div>
{FOOTER}
</body>
</html>"""


def main():
    products = load_products()
    by_cat = {}
    for p in products:
        by_cat.setdefault(p["cat"], []).append(p)

    pages = []
    for cat, items in by_cat.items():
        if len(items) < MIN_PER_CATEGORY:
            continue
        items.sort(key=lambda p: (-p["fun"], p["price"] if p["price"] is not None else 9999))
        pages.append((cat, items[:MAX_PER_PAGE]))

    pages.sort(key=lambda x: -len(x[1]))
    cats = [c for c, _ in pages]

    OUT_DIR.mkdir(exist_ok=True)
    written = 0
    for cat, items in pages:
        slug = slugify(cat)
        siblings = [c for c in cats if c != cat]
        path = OUT_DIR / f"best-{slug}-{YEAR}.html"
        path.write_text(build_page(cat, items, siblings), encoding="utf-8")
        written += 1
        print(f"  wrote comparisons/best-{slug}-{YEAR}.html ({len(items)} picks)")

    # Index page
    INDEX_DIR.mkdir(exist_ok=True)
    links = "\n".join(
        f'<li><a class="sup" href="/comparisons/best-{slugify(c)}-{YEAR}.html">Best {esc(c)} Picks ({YEAR})</a> '
        f'<span style="color:#9ca3af;font-size:0.85rem;">— {len(i)} picks</span></li>'
        for c, i in pages
    )
    INDEX_DIR.joinpath("index.html").write_text(
        f"""<!DOCTYPE html>
<html lang="en"><head>{CSS}<title>Best-Of Guides ({YEAR}) — WorthIt Goods</title>
<meta name="description" content="Every WorthItGoods best-of list in one place — hand-picked products by category.">
<link rel="canonical" href="{SITE}/best-of/"></head>
<body>{HEADER}
<div class="article-header"><h1>Best-Of Guides ({YEAR})</h1>
<p class="subtitle">Hand-picked products by category — no filler, just the ones worth your money.</p></div>
<div class="article-content"><ul style="line-height:2;">{links}</ul></div>
{FOOTER}</body></html>""",
        encoding="utf-8",
    )
    print(f"  wrote best-of/index.html ({len(pages)} categories)")
    print(f"Done: {written} roundup pages + index")


if __name__ == "__main__":
    main()
