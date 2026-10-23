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
        :root {{ --grad-start: #ff9a56; --grad-end: #ff6b6b; --green: #16a34a; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; background: #f8fafc; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
        .top-nav {{ background: #fff; border-bottom: 1px solid #e5e7eb; padding: 12px 0; margin-bottom: 0; position: sticky; top: 0; z-index: 10; }}
        .top-nav .container {{ display: flex; align-items: center; gap: 24px; }}
        .top-nav .logo {{ font-size: 1.3rem; font-weight: 700; color: #1f2937; text-decoration: none; }}
        .top-nav .logo span {{ background: linear-gradient(135deg,var(--grad-start),var(--grad-end)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .top-nav a {{ color: #6b7280; text-decoration: none; font-size: 14px; font-weight: 500; }}
        .top-nav a:hover {{ color: #1f2937; }}
        .hero {{ background: linear-gradient(135deg, #ff9a56, #ff6b6b, #4ecdc4); background-size: 300% 300%; color: #fff; text-align: center; padding: 50px 20px 40px; animation: gradient-shift 15s ease infinite; }}
        @keyframes gradient-shift {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
        .hero h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; }}
        .hero p {{ font-size: 1.1rem; opacity: 0.92; max-width: 550px; margin: 0 auto; }}
        .cat-nav {{ display: flex; flex-wrap: wrap; gap: 6px; padding: 16px 0 20px; justify-content: center; border-bottom: 1px solid #e5e7eb; margin-bottom: 30px; }}
        .cat-nav a {{ padding: 7px 16px; background: #fff; color: #374151; border-radius: 50px; text-decoration: none; font-size: 13px; font-weight: 500; border: 1.5px solid #e5e7eb; transition: all 0.2s; }}
        .cat-nav a:hover {{ border-color: var(--grad-start); color: var(--grad-end); }}
        .cat-nav a.active {{ background: linear-gradient(135deg,var(--grad-start),var(--grad-end)); color: #fff; border-color: transparent; font-weight: 600; }}
        .product-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .product-card {{ background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04); transition: transform .2s, box-shadow .2s; }}
        .product-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }}
        .product-img-link {{ display: block; background: #f9fafb; padding: 16px; }}
        .product-img {{ width: 100%; height: 200px; object-fit: contain; }}
        .product-info {{ padding: 0 16px 16px; }}
        .product-title {{ color: #1f2937; text-decoration: none; font-size: 14px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 8px; display: block; font-weight: 500; }}
        .product-title:hover {{ color: var(--grad-end); }}
        .product-price {{ font-size: 1.2rem; font-weight: 700; color: var(--green); display: block; margin-bottom: 10px; }}
        .product-links {{ display: flex; gap: 8px; }}
        .amazon-btn {{ flex: 1; text-align: center; padding: 8px 0; background: linear-gradient(135deg,#ff9a56,#ff6b6b); color: #fff; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; transition: opacity .2s; }}
        .amazon-btn:hover {{ opacity: 0.9; }}
        .ebay-btn {{ flex: 1; text-align: center; padding: 8px 0; background: #fff; color: #6b7280; border-radius: 8px; text-decoration: none; font-size: 12px; border: 1.5px solid #e5e7eb; transition: all .2s; }}
        .ebay-btn:hover {{ border-color: #9ca3af; color: #374151; }}
        .footer {{ margin-top: 50px; padding: 30px 0; border-top: 1px solid #e5e7eb; font-size: 13px; color: #9ca3af; text-align: center; }}
        .footer a {{ color: var(--grad-end); text-decoration: none; }}
    </style>
</head>
<body>
    <div class="top-nav">
        <div class="container">
            <a href="/" class="logo"><span>WorthIt</span>Goods</a>
            <a href="/">Home</a>
            <a href="/comparisons/">Comparisons</a>
            <a href="/blog/">Blog</a>
            <a href="/categories/" style="font-weight:600;color:#1f2937;">Categories</a>
        </div>
    </div>
    <div class="hero">
        <h1>{meta['name']}</h1>
        <p>{meta['desc']} — {len(products)} hand-picked products</p>
    </div>
    <div class="container">
        <div class="cat-nav">
            <a href="/categories/">All</a>
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
cat_meta = {
    "kitchen-dining": "🍳", "electronics": "🔌", "automotive": "🚗", "outdoor": "🏕️",
    "health": "💊", "home-decor": "🏠", "tools": "🔧", "toys-games": "🎮",
    "pets": "🐾", "gifts-novelty": "🎁", "office": "📎", "clothing-accessories": "👕", "other": "📦"
}
cat_links = ""
for cat_key in sorted(categories.keys(), key=lambda x: -len(categories[x])):
    if len(categories[cat_key]) < 2: continue
    meta = CATEGORY_META.get(cat_key, {})
    products = categories[cat_key]
    # Use first product's image as category hero, with emoji fallback
    hero_img = ""
    for p in products:
        img = p.get("image", "")
        if img and img.startswith("http"):
            hero_img = img
            break
    emoji = cat_meta.get(cat_key, "📦")
    img_html = f'<div class="cat-img"><img src="{hero_img}" alt="{meta.get("name", cat_key)}" loading="lazy" onerror="this.parentElement.innerHTML=&apos;<span class=cat-emoji>{emoji}</span>&apos;"></div>' if hero_img else f'<div class="cat-img cat-img-fallback"><span class="cat-emoji">{emoji}</span></div>'
    cat_links += f"""        <a href="/categories/{meta.get('slug', cat_key)}/" class="cat-card">
            {img_html}
            <div class="cat-text">
                <h3>{meta.get('name', cat_key.replace('-',' ').title())}</h3>
                <p>{meta.get('desc', '')}</p>
                <span class="count">{len(products)} products</span>
            </div>
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
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; background: #f8fafc; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .top-nav {{ background: #fff; border-bottom: 1px solid #e5e7eb; padding: 12px 0; margin-bottom: 0; }}
        .top-nav .container {{ display: flex; align-items: center; gap: 24px; }}
        .top-nav .logo {{ font-size: 1.3rem; font-weight: 700; color: #1f2937; text-decoration: none; }}
        .top-nav .logo span {{ background: linear-gradient(135deg,#ff9a56,#ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .top-nav a {{ color: #6b7280; text-decoration: none; font-size: 14px; font-weight: 500; }}
        .hero {{ background: linear-gradient(135deg, #ff9a56, #ff6b6b, #4ecdc4); background-size: 300% 300%; color: #fff; text-align: center; padding: 50px 20px 40px; animation: gradient-shift 15s ease infinite; }}
        @keyframes gradient-shift {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
        .hero h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; }}
        .hero p {{ font-size: 1.1rem; opacity: 0.92; max-width: 500px; margin: 0 auto; }}
        .cat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; margin: 30px 0; }}
        .cat-card {{ background: #fff; border-radius: 12px; text-decoration: none; color: #1f2937; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.03); transition: transform .2s, box-shadow .2s; border: 1px solid #f3f4f6; overflow: hidden; display: flex; }}
        .cat-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-color: #ff9a56; }}
        .cat-img {{ width: 100px; min-height: 100px; background: #f9fafb; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
        .cat-img img {{ width: 80px; height: 80px; object-fit: contain; }}
        .cat-img-fallback {{ background: linear-gradient(135deg, #fff7ed, #fef2f2); }}
        .cat-emoji {{ font-size: 2.4rem; line-height: 1; }}
        .cat-text {{ padding: 16px; flex: 1; }}
        .cat-text h3 {{ margin-bottom: 6px; font-size: 1rem; font-weight: 600; }}
        .cat-text p {{ color: #6b7280; font-size: .83rem; margin-bottom: 8px; line-height: 1.4; }}
        .cat-text .count {{ font-size: .78rem; color: #16a34a; font-weight: 600; }}
        .footer {{ margin-top: 40px; padding: 30px 0; border-top: 1px solid #e5e7eb; font-size: 13px; color: #9ca3af; text-align: center; }}
        .footer a {{ color: #ff6b6b; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="top-nav"><div class="container"><a href="/" class="logo"><span>WorthIt</span>Goods</a><a href="/">Home</a><a href="/comparisons/">Comparisons</a><a href="/blog/">Blog</a><a href="/categories/" style="font-weight:600;color:#1f2937;">Categories</a></div></div>
    <div class="hero"><h1>Product Categories</h1><p>149 hand-picked products across 12 categories — every one with real prices and honest takes.</p></div>
    <div class="container">
        <div class="cat-grid">
{cat_links}
        </div>
        <div class="footer"><p>&#x1f6d2; As an Amazon Associate and eBay Partner, we earn from qualifying purchases.</p><p style="margin-top:8px"><a href="/">&#8592; Back to WorthIt Goods</a></p></div>
    </div>
</body>
</html>"""

os.makedirs("categories", exist_ok=True)
with open("categories/index.html", "w") as f:
    f.write(index_html)

print(f"Built category index page ({len(categories)} categories)")
print("Category pages ready in categories/")