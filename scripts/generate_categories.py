#!/usr/bin/env python3
"""Generate category landing pages for WorthItGoods from categorized products."""

import json, os
from collections import defaultdict

CATEGORY_META = {
    "kitchen-dining": {"name": "Kitchen & Dining", "slug": "kitchen",
        "desc": "Cooking gadgets, drinkware, and clever kitchen tools that make mealtime better.",
        "keywords": "kitchen gadgets, cooking tools, unique kitchen gifts, drinkware, bar accessories"},
    "electronics": {"name": "Electronics & Gadgets", "slug": "electronics",
        "desc": "Desk accessories, charging solutions, and clever electronics for work and play.",
        "keywords": "desk accessories, electronic gadgets, charging stations, computer accessories"},
    "health": {"name": "Health & Personal Care", "slug": "health",
        "desc": "First aid, pain relief, insect repellent, and wellness products that actually work.",
        "keywords": "first aid kit, insect repellent, pain relief, muscle care, health products"},
    "automotive": {"name": "Automotive & Car Care", "slug": "automotive",
        "desc": "Car accessories, emergency kits, cleaning supplies, and tools for your vehicle.",
        "keywords": "car accessories, automotive tools, car cleaning, emergency car kit, car care products"},
    "toys-games": {"name": "Toys & Games", "slug": "toys-games",
        "desc": "Creative toys, puzzles, art supplies, and fun activities for all ages.",
        "keywords": "toys, games, puzzles, art supplies, craft kits, creative play"},
    "outdoor": {"name": "Outdoor & Camping", "slug": "outdoor",
        "desc": "Camping gear, hiking essentials, and outdoor living products for adventurers.",
        "keywords": "camping gear, hiking equipment, outdoor living, hammock, lantern, outdoor tools"},
    "clothing-accessories": {"name": "Clothing & Accessories", "slug": "clothing",
        "desc": "Socks, hats, wallets, bags, and wearable accessories with personality.",
        "keywords": "socks, hats, wallets, bags, accessories, wearable gifts"},
    "tools": {"name": "Tools & Hardware", "slug": "tools",
        "desc": "Multi-tools, screwdrivers, wrenches, and practical hardware for DIY projects.",
        "keywords": "multi-tool, screwdriver set, wrench, DIY tools, hardware"},
    "home-decor": {"name": "Home Decor", "slug": "home-decor",
        "desc": "Vases, candles, blankets, pillows, and decorative touches for every room.",
        "keywords": "home decor, vases, candles, blankets, pillows, decorative accessories"},
    "pets": {"name": "Pet Supplies", "slug": "pets",
        "desc": "Collars, leashes, feeders, and accessories for your furry friends.",
        "keywords": "dog collar, cat accessories, pet feeder, pet supplies"},
    "gifts-novelty": {"name": "Gifts & Novelty", "slug": "gifts",
        "desc": "Funny, quirky, and unexpected gifts that make people laugh and remember you.",
        "keywords": "funny gifts, novelty items, quirky presents, unique gifts, gag gifts"},
    "office": {"name": "Office & Stationery", "slug": "office",
        "desc": "Briefcases, organizers, notepads, and desk tools for productive workspaces.",
        "keywords": "office supplies, briefcase, desk organizer, stationery, work accessories"},
    "other": {"name": "General", "slug": "general",
        "desc": "Useful products that don't fit neatly into one category — but still worth it.",
        "keywords": "useful products, everyday items, practical gifts"},
}

with open("data/categorized_products.json") as f:
    categories = json.load(f)

EBAY_CAMPID = "5339174383"
AMAZON_TAG = "worthitgoods-20"

def product_card(p):
    title = p.get("title", "")
    price = p.get("price_display", f"${p.get('price', '?')}")
    image = p.get("image", "")
    asin = p.get("asin", "")
    url = p.get("url", "")
    if not url and asin:
        url = f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
    
    # eBay search link
    clean_title = ''.join(c if c.isalnum() or c in ' -' else '' for c in title)[:100]
    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={clean_title.replace(' ', '+')}&campid={EBAY_CAMPID}&mkcid=1&mkevt=1&mkrid=711-53200-19255-0&siteid=0"
    
    # Image fallback
    img_src = image if image and image.startswith("http") else "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect fill='%231a1a2e' width='200' height='200'/><text fill='%23666' x='50%25' y='50%25' text-anchor='middle' dy='.3em'>No Image</text></svg>"
    
    return f"""
    <div class="product-card">
        <a href="{url}" target="_blank" rel="nofollow sponsored" class="product-img-link">
            <img src="{img_src}" alt="{title[:60]}" loading="lazy" class="product-img" onerror="this.src='data:image/svg+xml,<svg xmlns=%27http://www.w3.org/2000/svg%27 width=%27200%27 height=%27200%27><rect fill=%27%231a1a2e%27 width=%27200%27 height=%27200%27/></svg>'">
        </a>
        <div class="product-info">
            <a href="{url}" target="_blank" rel="nofollow sponsored" class="product-title">{title[:80]}</a>
            <span class="product-price">{price}</span>
            <div class="product-links">
                <a href="{url}" target="_blank" rel="nofollow sponsored" class="amazon-btn">🛒 Amazon</a>
                <a href="{ebay_url}" target="_blank" rel="nofollow" class="ebay-btn">📦 eBay</a>
            </div>
        </div>
    </div>"""

pages_built = 0
for cat_key, products in sorted(categories.items(), key=lambda x: -len(x[1])):
    if len(products) < 2 and cat_key != "other":
        continue  # Skip single-product categories
    meta = CATEGORY_META.get(cat_key, {"name": cat_key.replace("-", " ").title(), "slug": cat_key,
        "desc": "Browse our curated picks in this category.", "keywords": "amazon deals, best products"})
    
    cards = "\n".join(product_card(p) for p in products[:50])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta['name']} — WorthIt Goods | Honest Product Picks</title>
    <meta name="description" content="{meta['desc']}">
    <meta name="keywords" content="{meta['keywords']}">
    <link rel="canonical" href="https://www.worthitgoods.com/categories/{meta['slug']}/">
    <meta property="og:title" content="{meta['name']} — WorthIt Goods">
    <meta property="og:description" content="{meta['desc']}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://www.worthitgoods.com/categories/{meta['slug']}/">
    <style>
        :root {{ --bg: #0f0f1a; --card: #1a1a2e; --text: #e5e5e5; --muted: #9ca3af; --accent: #f59e0b; --link: #60a5fa; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
        .nav {{ background: var(--card); border-bottom: 1px solid #2a2a3e; padding: 12px 0; margin-bottom: 30px; }}
        .nav a {{ color: var(--link); text-decoration: none; margin-right: 20px; font-size: 14px; }}
        .nav a:hover {{ color: #93c5fd; }}
        h1 {{ font-size: 2rem; margin-bottom: 8px; }}
        h1 span {{ color: var(--accent); }}
        .cat-desc {{ color: var(--muted); margin-bottom: 30px; font-size: 1.1rem; }}
        .cat-nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 30px; }}
        .cat-nav a {{ padding: 6px 14px; background: var(--card); border-radius: 20px; color: var(--text); text-decoration: none; font-size: 13px; border: 1px solid #2a2a3e; }}
        .cat-nav a:hover, .cat-nav a.active {{ background: var(--accent); color: #000; border-color: var(--accent); }}
        .product-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .product-card {{ background: var(--card); border-radius: 10px; overflow: hidden; border: 1px solid #2a2a3e; transition: transform .15s; }}
        .product-card:hover {{ transform: translateY(-2px); }}
        .product-img-link {{ display: block; background: #111; }}
        .product-img {{ width: 100%; height: 220px; object-fit: contain; padding: 15px; background: #111; }}
        .product-info {{ padding: 12px; }}
        .product-title {{ color: var(--text); text-decoration: none; font-size: 14px; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 8px; display: block; }}
        .product-title:hover {{ color: var(--accent); }}
        .product-price {{ font-size: 1.2rem; font-weight: 700; color: var(--accent); display: block; margin-bottom: 10px; }}
        .product-links {{ display: flex; gap: 8px; }}
        .amazon-btn {{ padding: 6px 12px; background: var(--accent); color: #000; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600; }}
        .ebay-btn {{ padding: 6px 12px; background: #2a2a3e; color: var(--muted); border-radius: 6px; text-decoration: none; font-size: 11px; }}
        .footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #2a2a3e; font-size: 13px; color: var(--muted); }}
        .footer a {{ color: var(--link); }}
    </style>
</head>
<body>
    <div class="nav">
        <div class="container">
            <a href="/">🏠 Home</a>
            <a href="/comparisons/">📊 Comparisons</a>
            <a href="/blog/">📝 Blog</a>
        </div>
    </div>
    <div class="container">
        <h1><span>&#9878;</span> {meta['name']}</h1>
        <p class="cat-desc">{meta['desc']} — {len(products)} products</p>
        <div class="cat-nav">
            <a href="/categories/">All Categories</a>
{chr(10).join(f'            <a href="/categories/{CATEGORY_META.get(ck, {}).get("slug", ck)}/"{" class=active" if ck == cat_key else ""}>{CATEGORY_META.get(ck, {}).get("name", ck.replace("-"," ").title())}</a>' for ck in sorted(categories.keys(), key=lambda kk: -len(categories[kk])) if len(categories[ck]) >= 2)}
        </div>
        <div class="product-grid">
{cards}
        </div>
        <div class="footer">
            <p>🛒 As an Amazon Associate and eBay Partner, we earn from qualifying purchases. Product data updated daily.</p>
            <p style="margin-top:8px"><a href="/">← Back to WorthIt Goods</a></p>
        </div>
    </div>
</body>
</html>"""
    
    os.makedirs(f"categories/{meta['slug']}", exist_ok=True)
    with open(f"categories/{meta['slug']}/index.html", "w") as f:
        f.write(html)
    pages_built += 1

print(f"Built {pages_built} category pages")

# Build category index page (all categories)
cat_links = ""
for cat_key in sorted(categories.keys(), key=lambda x: -len(categories[x])):
    if len(categories[cat_key]) < 2: continue
    meta = CATEGORY_META.get(cat_key, {})
    cat_links += f"""        <a href="/categories/{meta.get('slug', cat_key)}/" class="cat-card">
            <h3>{meta.get('name', cat_key.replace('-',' ').title())}</h3>
            <p>{meta.get('desc', '')}</p>
            <span class="count">{len(categories[cat_key])} products</span>
        </a>\n"""

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Categories — WorthIt Goods</title>
    <meta name="description" content="Browse WorthIt Goods by category. Kitchen, electronics, automotive, outdoor, and more — honest product picks with real prices.">
    <link rel="canonical" href="https://www.worthitgoods.com/categories/">
    <meta property="og:title" content="Product Categories — WorthIt Goods">
    <style>
        :root {{ --bg: #0f0f1a; --card: #1a1a2e; --text: #e5e5e5; --muted: #9ca3af; --accent: #f59e0b; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .nav {{ background: var(--card); border-bottom: 1px solid #2a2a3e; padding: 12px 0; margin-bottom: 30px; }}
        .nav a {{ color: #60a5fa; text-decoration: none; margin-right: 20px; }}
        h1 {{ font-size: 2rem; margin-bottom: 8px; }} h1 span {{ color: var(--accent); }}
        .sub {{ color: var(--muted); margin-bottom: 30px; }}
        .cat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }}
        .cat-card {{ background: var(--card); padding: 20px; border-radius: 10px; text-decoration: none; color: var(--text); border: 1px solid #2a2a3e; transition: transform .15s; }}
        .cat-card:hover {{ transform: translateY(-2px); border-color: var(--accent); }}
        .cat-card h3 {{ margin-bottom: 8px; font-size: 1.1rem; }}
        .cat-card p {{ color: var(--muted); font-size: .9rem; margin-bottom: 10px; }}
        .cat-card .count {{ font-size: .8rem; color: var(--accent); }}
        .footer {{ margin-top: 50px; padding: 20px 0; border-top: 1px solid #2a2a3e; font-size: 13px; color: var(--muted); }}
    </style>
</head>
<body>
    <div class="nav"><div class="container"><a href="/">🏠 Home</a><a href="/comparisons/">📊 Comparisons</a><a href="/blog/">📝 Blog</a></div></div>
    <div class="container">
        <h1><span>&#9878;</span> Product Categories</h1>
        <p class="sub">149 products across 12 categories. Click a category to browse.</p>
        <div class="cat-grid">
{cat_links}
        </div>
        <div class="footer"><p>🛒 As an Amazon Associate and eBay Partner, we earn from qualifying purchases.</p><p style="margin-top:8px"><a href="/" style="color:#60a5fa">← Back to WorthIt Goods</a></p></div>
    </div>
</body>
</html>"""

os.makedirs("categories", exist_ok=True)
with open("categories/index.html", "w") as f:
    f.write(index_html)

print(f"Built category index page ({len(categories)} categories)")
print("Category pages ready in categories/")