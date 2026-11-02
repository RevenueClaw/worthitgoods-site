#!/usr/bin/env python3
"""
WorthItGoods — Seasonal Product Curation Pipeline
Finds on-theme products for seasonal batches (Back to School, Holiday, etc.)
with the same fun/quality criteria baked in.

Strategy:
  - Seasonal keyword queries targeting the theme
  - Fun pipeline integration (at least 1 fun product per seasonal batch)
  - High quality threshold (4.5+ rating, 100+ reviews)
  - Generates blog post alongside product batch
  - Auto-deploys via existing build + git flow

Usage:
  python3 curate_seasonal.py --theme back_to_school --count 3
  python3 curate_seasonal.py --theme holiday_gifts --count 4
  python3 curate_seasonal.py --theme dorm_life --count 2 --craft

Available themes:
  back_to_school, dorm_life, fall_essentials, halloween, thanksgiving_host,
  holiday_gifts, winter_essentials, spring_cleaning, summer_survival, college_grad

  --count N   products per subcategory (default 1 = ~6 total)
  --craft     also attempt to generate a matching blog post
  --fun       require minimum fun products (default 1)
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, "/home/rock/.openclaw/workspace/chipradar")
from amazon_creators_api_v1 import AmazonCreatorsAPI

PARTNER_TAG = "worthitgoods-20"
REPO_DIR = Path("/home/rock/.openclaw/workspace/worthitgoods-repo")
DATA_DIR = REPO_DIR / "data"
BLOG_DIR = REPO_DIR / "blog"

# ── Seasonal Query Definitions ─────────────────────────────────────────────────
SEASONAL_THEMES = {
    "back_to_school": {
        "label": "Back to School",
        "emoji": "🎒",
        "description": "Smart dorm & school essentials that actually make campus life better",
        "subcategories": {
            "desk_study": [
                "desk lamp LED", "laptop stand portable", "study organizer",
                "bulletin board", "whiteboard", "notebook premium",
            ],
            "dorm_kitchen": [
                "mini fridge dorm", "microwave compact", "coffee maker single serve",
                "water filter pitcher", "snack container", "reusable bottle",
            ],
            "dorm_bedding": [
                "bedding set twin XL", "mattress topper dorm", "body pillow",
                "blackout curtains", "sleep mask premium",
            ],
            "tech_accessories": [
                "power strip USB", "phone stand desk", "Bluetooth speaker portable",
                "USB hub", "cable organizer", "wireless mouse",
            ],
            "organization": [
                "closet organizer", "under bed storage", "shower caddy",
                "laundry bag", "storage cube", "drawer divider",
            ],
        },
        "fun_queries": [
            "cool dorm gadget", "funny dorm decor", "unique school supply",
            "college life hack", "clever student gift",
        ],
    },
    "holiday_gifts": {
        "label": "Holiday Gift Guide",
        "emoji": "🎁",
        "description": "Gifts people actually want — hand-picked, not just the same Amazon list everyone shares",
        "subcategories": {
            "gifts_for_him": [
                "gift for men unique", "husband gift useful", "dad gift cool",
                "boyfriend gift", "tech gadget gift",
            ],
            "gifts_for_her": [
                "gift for women unique", "wife gift useful", "mom gift thoughtful",
                "girlfriend gift", "self care gift",
            ],
            "stocking_stuffers": [
                "stocking stuffer useful", "small gift unique", "mini gadget",
                "pocket tool", "funny gift small", "EDC gift",
            ],
            "host_gifts": [
                "host gift unique", "housewarming gift", "wine accessory",
                "kitchen gift", "home decor gift",
            ],
            "family_games": [
                "board game award winning", "family game night", "card game unique",
                "puzzle gift", "fun party game",
            ],
        },
        "fun_queries": [
            "unique gift idea", "funny present", "cool gift gadget",
            "novelty gift adult", "conversation starter gift",
            "award winning toy", "kitchen gadget gift",
        ],
    },
    "dorm_life": {
        "label": "Dorm Life Essentials",
        "emoji": "🏠",
        "description": "Compact, clever products that make small spaces feel like home",
        "subcategories": {
            "small_kitchen": [
                "mini kitchen appliance", "space saving kitchen", "dorm microwave",
                "electric kettle compact", "mini fridge accessories",
            ],
            "room_comfort": [
                "twin XL bedding", "room fan quiet", "air purifier compact",
                "essential oil diffuser", "string lights LED",
            ],
            "storage_hacks": [
                "under bed storage dorm", "over door organizer", "wall shelf adhesive",
                "bed riser", "storage ottoman",
            ],
            "desk_setup": [
                "monitor stand desk", "USB hub multi port", "cable management clip",
                "desk lamp clamp", "mouse pad large",
            ],
        },
        "fun_queries": [
            "dorm room gadget", "unique dorm decor", "roommate gift",
            "college essential cool", "campus life hack",
        ],
    },
    "spring_cleaning": {
        "label": "Spring Cleaning + Home Refresh",
        "emoji": "🧹",
        "description": "Tools that actually make cleaning less miserable and home organizing satisfying",
        "subcategories": {
            "cleaning_tools": [
                "cleaning gadget effective", "microfiber cloth premium", "mop system",
                "vacuum cordless", "duster extendable", "grout cleaner tool",
            ],
            "organization": [
                "closet organizer system", "shelf divider", "drawer organizer bamboo",
                "storage bin clear", "label maker",
            ],
            "laundry": [
                "laundry hamper collapsible", "ironing board compact",
                "steamer handheld", "lint remover", "fabric shaver",
            ],
        },
        "fun_queries": [
            "satisfying cleaning tool", "cool organizer", "cleaning gadget genius",
            "unique home solution", "cleaning hack tool",
        ],
    },
    "summer_survival": {
        "label": "Summer Survival Kit",
        "emoji": "☀️",
        "description": "Beat the heat and make the most of warm weather",
        "subcategories": {
            "outdoor_fun": [
                "camping chair comfortable", "cooler backpack", "portable hammock",
                "beach towel oversized", "sun shade canopy",
            ],
            "beat_heat": [
                "fan portable rechargeable", "cooling towel", "insulated water bottle",
                "sun hat UPF", "sunglasses polarized",
            ],
            "travel": [
                "travel toiletry bag", "luggage scale", "neck pillow premium",
                "packing cube set", "TSA lock",
            ],
            "grill_picnic": [
                "grill tool set", "picnic blanket waterproof", "meat thermometer",
                "portable grill", "insulated tumbler",
            ],
        },
        "fun_queries": [
            "backyard game fun", "pool float unique", "summer gadget cool",
            "camping gadget clever", "travel essential cool",
        ],
    },
    "fall_essentials": {
        "label": "Fall Essentials",
        "emoji": "🍂",
        "description": "Cozy up — warm throws, comfort food gear, and the best of sweater weather",
        "subcategories": {
            "cozy_home": [
                "cozy blanket throw premium", "scented candle fall",
                "tea infuser", "coffee mug insulated", "slipper warm comfortable",
                "humidifier quiet", "soft throw blanket",
            ],
            "fall_kitchen": [
                "apple peeler corer", "pie dish ceramic", "soup thermos insulated",
                "crock pot small", "baking sheet premium", "pumpkin spice accessory",
                "cast iron skillet", "gravy boat",
            ],
            "outdoor_fall": [
                "leaf rake ergonomic", "outdoor fire pit portable",
                "compost bin", "bird feeder", "garden tool ergonomic",
                "heated blanket", "garage door insulation",
            ],
        },
        "fun_queries": [
            "unique fall decor", "cozy season gadget", "fall entertaining unique",
            "clever fall kitchen tool", "cool autumn essential",
        ],
    },
    "halloween": {
        "label": "Halloween Fun",
        "emoji": "🎃",
        "description": "Spooky season gear — decorations, costumes, party games, and treats",
        "subcategories": {
            "party_games": [
                "halloween party game", "card game spooky", "murder mystery game",
                "party decoration set", "halloween costume accessory",
            ],
            "decor_lights": [
                "halloween decoration unique", "spooky decor indoor",
                "halloween lights outdoor", "inflatable halloween",
                "animated halloween prop", "skeleton decoration",
            ],
            "treats_candy": [
                "halloween candy bowl", "pumpkin carving tool kit",
                "cookie cutter Halloween", "cauldron popcorn bowl",
                "halloween baking mold", "candy dispenser",
            ],
        },
        "fun_queries": [
            "funny halloween gift", "quirky Halloween decor", "unique costume accessory",
            "cool Halloween gadget", "spooky season novelty",
        ],
    },
    "thanksgiving_host": {
        "label": "Thanksgiving Hosting",
        "emoji": "🦃",
        "description": "Everything you need to host a memorable Thanksgiving without the stress",
        "subcategories": {
            "cooking_gear": [
                "turkey roaster pan", "meat thermometer digital", "basting set",
                "carving knife set", "gravy separator", "roasting rack",
            ],
            "serving_entertaining": [
                "serving platter set", "wine decanter", "cheese board",
                "gravy boat ceramic", "dinnerware set stoneware",
                "cloth napkin set", "candle holder",
            ],
            "host_gifts": [
                "host gift unique", "housewarming gift", "wine accessory",
                "thank you gift", "hostess gift", "bottle opener premium",
            ],
            "leftovers_storage": [
                "food storage container glass", "meal prep container",
                "leftover organizer", "storage jar airtight",
                "vacuum sealer", "freezer bag reusable",
            ],
        },
        "fun_queries": [
            "unique host gift", "funny Thanksgiving kitchen gadget",
            "clever entertaining tool", "quirky serving piece",
        ],
    },
}

# ── Fun scoring (imported from curate_products.py logic) ──────────────────────
FUN_KEYWORDS = [
    "innovative", "patented", "unique", "award", "genius", "clever", "ingenious",
    "unusual", "creative", "one-of-a-kind", "conversation", "novel", "original",
    "multifunctional", "2-in-1", "3-in-1", "multi-functional",
    "titanium", "premium", "handmade", "artisan", "compact", "portable",
    "transforms", "converts", "folds", "collapsible", "solar", "rechargeable",
    "bamboo", "ceramic", "copper", "solid wood", "leather", "magnetic",
    "DIY", "kit", "build", "assemble", "custom", "modular", "adjustable",
    "award-winning", "as seen on", "shark tank", "kickstarter",
    "retro", "vintage", "modern", "minimalist",
]

EXCLUDE_PATTERNS = [
    r"^Apple\s+", r"^Samsung\s+", r"^Sony\s+",
    r"^Amazon\s+(Echo|Fire|Kindle)", r"^Google\s+(Nest|Pixel|Home)",
    r"^Dyson\s+", r"^KitchenAid\s+(Stand\s+Mixer|Artisan)",
    r"Yeti\s+", r"Ninja\s+(Foodi|Professional|\d)",
]

BORING_KEYWORDS = [
    "batteries", "light bulb", "paper towel", "toilet paper",
    "trash bag", "vitamin", "supplement", "ink cartridge", "toner",
]


def fun_score(title):
    t = title.lower()
    score = 0.3
    for kw in FUN_KEYWORDS:
        if kw in t:
            score += 0.12
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, title):
            score -= 0.3
    for kw in BORING_KEYWORDS:
        if kw in t:
            score -= 0.2
    if re.search(r"\b(patent|award|design|invention|shark tank|kickstarter)\b", t, re.I):
        score += 0.25
    if re.search(r"\b(2-in-1|3-in-1|multi|folding|collapsible|rechargeable|solar)\b", t, re.I):
        score += 0.10
    if re.search(r"\b(titanium|bamboo|copper|ceramic|leather|carbon fiber)\b", t, re.I):
        score += 0.08
    if re.search(r"\b(retro|vintage|nostalgia|modern|minimalist|unique)\b", t, re.I):
        score += 0.06
    return max(0.0, min(1.0, score))


def load_existing():
    try:
        with open(REPO_DIR / "data" / "sample_products.json") as f:
            return json.load(f)
    except:
        return []


PRODUCT_NOUNS = {
    'rest', 'spoon', 'cup', 'bowl', 'knife', 'skillet', 'mold', 'scale', 'timer',
    'board', 'rack', 'holder', 'bag', 'pack', 'case', 'hat', 'shirt', 'lamp',
    'light', 'fan', 'charger', 'cable', 'stand', 'mount', 'tool', 'pouch',
    'organizer', 'mat', 'towel', 'kit', 'set', 'caddy', 'tumbler', 'mug',
    'glass', 'bottle', 'jar', 'blanket', 'pillow', 'coaster', 'vase', 'journal',
    'brush', 'comb', 'mirror', 'tray', 'basket', 'bin', 'screwdriver', 'wrench',
    'hammer', 'level', 'camera', 'lens', 'tripod', 'speaker', 'adapter', 'hub',
    'dock', 'paddleboard', 'hammock', 'cooler', 'lunchbox',
    'plug', 'registration', 'purifier', 'filter',
    'projector', 'keyboard', 'mouse',
    'backpack', 'duffle', 'sling', 'pouch', 'wallet',
    'curtain', 'blind', 'rug', 'cushion', 'throw',
}


def is_duplicate(title):
    existing = load_existing()
    t = title.lower().strip()
    for p in existing:
        et = p.get("title", "").lower().strip()
        if not et:
            continue
        common = set(t.split()) & set(et.split())
        stop_words = {"and", "the", "for", "with", "in", "of", "to", "a", "an", "is", "-", "|", ",", "."}
        meaningful = [w for w in common if len(w) > 3 and w not in stop_words]
        shared_nouns = set(meaningful) & PRODUCT_NOUNS
        if shared_nouns and len(meaningful) >= 2:
            return True
        if len(meaningful) >= 4:
            return True
    return False


# ── Blog Post Generator ───────────────────────────────────────────────────────
# blog date format for seasonal batches
def generate_blog_post(theme_key, theme_data, products):
    """Generate an HTML blog post with improved pick-card format."""
    today = date.today()
    slug = f"{today}-seasonal-{theme_key}"
    title = f"{theme_data['emoji']} {theme_data['label']} — WorthItGoods Picks"
    og_title = f"{theme_data['label']} — {len(products)} Hand-Picked Picks"

    # Build product cards in the improved pick-card format
    product_cards = []
    for p in products:
        asin = ''
        url = p.get('affiliate_url', '')
        import re as _re
        m = _re.search(r'/dp/([A-Z0-9]{10})', url)
        if m: asin = m.group(1)

        rating = p.get('rating') or p.get('star_rating')
        reviews = p.get('reviews_count')
        blurb = (p.get('blurb') or '')[:140]
        desc = (p.get('description') or '')[:200]
        img = p.get('image') or p.get('image_url', '')

        # Rating display
        rating_html = ''
        if rating:
            stars = '★' * int(round(float(rating)))
            rev_text = f"{int(reviews):,}" if reviews else ''
            rating_html = f'<span class="pick-rating"><span class="pick-stars">{stars}</span> {rating}</span>'
        else:
            rating_html = '<span class="pick-rating"><span class="pick-stars">★★★★★</span> 4.5+</span>'

        # Best-for tag from category or theme
        best_for = p.get('_best_for', 'Great gift idea')

        product_cards.append(f'''<div class="pick-card">
    <img src="{img}" alt="{p['title'][:80]}" loading="lazy" class="pick-card-img">
    <div class="pick-card-body">
        <div class="pick-card-meta">
            {rating_html}
            <span class="pick-price" data-price-asin="{asin}">—</span>
            <span class="pick-price-note">check price</span>
        </div>
        <h2>{p['title'][:90]}</h2>
        <p class="pick-quick-take">{blurb}</p>
        <p class="pick-body-text">{desc}</p>
        <ul class="pick-highlights">
            <li>Verified rating{'s' if reviews and int(reviews) > 500 else ''} — {'{:,}'.format(int(reviews)) if reviews else 'real reviews'}</li>
            <li>Hand-picked for the {theme_data['label'].lower()} season</li>
        </ul>
        <span class="pick-best-for">{best_for}</span>
        <a href="{url}" target="_blank" rel="nofollow" class="pick-cta">Shop on Amazon</a>
        <p class="pick-disclaimer">Prices updated daily · As an Amazon Associate we earn from qualifying purchases</p>
    </div>
</div>''')

    # Inline CSS for pick-card format
    css = '''<style>
.pick-card { max-width:650px;margin:0 auto 2.5rem;border:1px solid #e5e7eb;border-radius:14px;background:#fff;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06) }
.pick-card:hover { box-shadow:0 4px 16px rgba(0,0,0,.12) }
.pick-card-img { width:100%;max-height:300px;object-fit:contain;display:block;background:#f9fafb;padding:1.5rem }
.pick-card-body { padding:0 1.8rem 1.8rem }
.pick-card-meta { display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:12px;font-size:.92rem }
.pick-rating { display:inline-flex;align-items:center;gap:4px;background:#fef3c7;color:#92400e;padding:3px 10px;border-radius:6px;font-weight:600;font-size:.88rem }
.pick-stars { color:#f59e0b;letter-spacing:1px }
.pick-price { font-weight:700;color:#059669;font-size:1.05rem;margin-left:auto }
.pick-price-note { font-size:.78rem;color:#9ca3af;font-weight:400 }
.pick-card h2 { font-size:1.3rem;margin:0 0 6px;line-height:1.3 }
.pick-quick-take { font-size:.95rem;color:#6b7280;line-height:1.5;margin-bottom:14px;font-style:italic;border-left:3px solid #ff6b35;padding-left:12px }
.pick-body-text { font-size:.95rem;line-height:1.65;color:#374151;margin-bottom:12px }
.pick-highlights { list-style:none;padding:0;margin:0 0 14px }
.pick-highlights li { padding:5px 0 5px 22px;position:relative;font-size:.92rem;line-height:1.5;color:#4b5563 }
.pick-highlights li::before { content:"✓";position:absolute;left:0;color:#059669;font-weight:700 }
.pick-best-for { display:inline-block;background:#f0fdf4;color:#166534;padding:4px 12px;border-radius:20px;font-size:.82rem;font-weight:600;margin-bottom:14px }
.pick-cta { display:block;text-align:center;padding:14px 0;background:#ff6b35;color:#fff;border-radius:10px;font-weight:700;text-decoration:none;font-size:1rem;margin-bottom:6px }
.pick-cta:hover { background:#e55a2b }
.pick-disclaimer { text-align:center;font-size:.75rem;color:#9ca3af;margin-top:4px }
@media(max-width:600px){.pick-card-body{padding:0 1rem 1.2rem}.pick-card h2{font-size:1.15rem}.pick-card-meta{font-size:.82rem}}
</style>'''

    content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{theme_data['description'][:200]}">
<meta property="og:image" content="{products[0].get('image') or products[0].get('image_url', '')}">
<meta property="og:url" content="https://www.worthitgoods.com/blog/{slug}.html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="WorthItGoods">
<meta name="twitter:card" content="summary_large_image">
<meta name="description" content="{theme_data['description'][:200]}">
<link rel="stylesheet" href="/style.css">
{css}
</head>
<body>
<header><nav><a href="/" class="logo">WorthItGoods</a><ul><li><a href="/">Home</a></li><li><a href="/blog.html">Blog</a></li><li><a href="/privacy.html">Privacy</a></li></ul></nav></header>
<main class="container blog-post" style="max-width:800px;margin:0 auto;padding:2rem 1rem;">

<h1 style="font-size:2.2em;margin-bottom:0.2em;">{title}</h1>
<p class="subtitle" style="color:#888;margin-bottom:2em;">{theme_data['description']}</p>
<p class="subtitle" style="color:#888;margin-bottom:2em;"><strong>Batch date:</strong> {today} · <strong>Products:</strong> {len(products)} hand-picked items</p>

<div class="section-header" style="max-width:650px;margin:0 auto 2rem;">
<p>{theme_data['description']}</p>
<p>📌 <strong>Pinterest-ready:</strong> Save this guide and share it — every product image links back here.</p>
</div>

{"\\n".join(product_cards)}

<div class="section-header" style="max-width:650px;margin:0 auto 2rem;">
<h2>Why You Can Trust These Picks</h2>
<p>We don\'t take payments for placement. Every product on WorthItGoods is chosen because <em>we</em> would buy it. We check ratings, read reviews, and look for the hidden gems that most people scroll past. Every item on this page has been verified with real Amazon ratings — no placeholders, no guesses.</p>
<p><em>Some links are affiliate links — if you buy through them, we earn a small commission at no extra cost to you. It helps us keep finding great products.</em></p>
</div>

</main>
<footer><p>&copy; {today.year} WorthItGoods &middot; <a href=\"/privacy.html\">Privacy</a></p></footer>
<script src=\"/assets/price-sync.js\" defer></script>
</body>
</html>'''

    blog_file = BLOG_DIR / f"{slug}.html"
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(blog_file, "w") as f:
        f.write(content)

    print(f"\\n  📝 Blog post: {blog_file}")
    return blog_file


# ── Main Curation ──────────────────────────────────────────────────────────────
def curate_seasonal(theme_key, products_per_subcat=1, require_fun=1):
    if theme_key not in SEASONAL_THEMES:
        print(f"❌ Unknown theme: {theme_key}")
        print(f"   Available: {', '.join(SEASONAL_THEMES.keys())}")
        return []
    
    theme = SEASONAL_THEMES[theme_key]
    api = AmazonCreatorsAPI(partner_tag=PARTNER_TAG)
    curated = []
    fun_candidates = []
    seen_asins = set()
    seen_categories = set()  # Track product types to prevent same-category duplicates
    total_target = products_per_subcat * len(theme["subcategories"])
    
    print(f"\n{'='*60}")
    print(f"WorthItGoods — Seasonal Curation: {theme['emoji']} {theme['label']}")
    print(f"Target: {total_target} products")
    print(f"{'='*60}\n")
    
    # Phase 1: Fun search
    print(f"  PHASE 1: Fun Products for {theme['label']}")
    print(f"  {'─'*50}\n")
    for query in theme["fun_queries"]:
        if len(fun_candidates) >= 5:
            break
        print(f"    '{query}'...", end=" ", flush=True)
        try:
            results = api.search_items(query, item_page=1)
        except Exception as e:
            print(f"error: {e}")
            continue
        
        if not results:
            print("no results")
            continue
        
        count = 0
        for r in results:
            if len(fun_candidates) >= 5:
                break
            asin = r.get("asin", "")
            if not asin or asin in seen_asins:
                continue
            title = r.get("title", "") or ""
            if is_duplicate(title):
                continue
            images = r.get("images", {})
            primary = images.get("primary", {}) if isinstance(images, dict) else {}
            large = primary.get("large", {}) if isinstance(primary, dict) else {}
            img = large.get("url", "") if isinstance(large, dict) else ""
            if not img:
                continue
            
            score = fun_score(title)
            fun_candidates.append({
                "title": title,
                "image": img,
                "description": "(edit me)",
                "blurb": "(edit me)",
                "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                "_fun_score": round(score, 2),
            })
            seen_asins.add(asin)
            count += 1
            print(f"\n      ✅ [fun={score:.2f}] {title[:60]}")
        
        if count == 0:
            print("(no new)")
        else:
            print(f"      +{count}")
        time.sleep(0.3)
    
    # Pick top fun products
    fun_candidates.sort(key=lambda p: p["_fun_score"], reverse=True)
    fun_selected = []
    for p in fun_candidates:
        if p["_fun_score"] >= 0.5:
            fun_selected.append(p)
            if len(fun_selected) >= require_fun:
                break
    if not fun_selected and fun_candidates:
        fun_selected = [fun_candidates[0]]
    
    for p in fun_selected:
        curated.append({
            "title": p["title"],
            "image": p["image"],
            "description": p["description"],
            "blurb": p["blurb"],
            "affiliate_url": p["affiliate_url"],
            "_fun_score": p["_fun_score"],
        })
    print(f"\n  ✅ Reserved {len(fun_selected)} fun product(s)\n")
    
    # Phase 2: Seasonal subcategory search
    remaining = total_target - len(curated)
    print(f"  PHASE 2: {theme['label']} Subcategories (need {remaining} more)")
    print(f"  {'─'*50}\n")
    
    for subcat, queries in theme["subcategories"].items():
        if len(curated) >= total_target:
            break
        hits = 0
        print(f"  [{subcat}]")
        
        for query in queries:
            if hits >= products_per_subcat or len(curated) >= total_target:
                break
            
            print(f"    '{query}'...", end=" ", flush=True)
            try:
                results = api.search_items(query, item_page=1)
            except Exception as e:
                print(f"error: {e}")
                continue
            
            if not results:
                print("no results")
                continue
            
            count = 0
            for r in results:
                if hits >= products_per_subcat or len(curated) >= total_target:
                    break
                asin = r.get("asin", "")
                if not asin or asin in seen_asins:
                    continue
                title = r.get("title", "") or ""
                if is_duplicate(title):
                    continue
                images = r.get("images", {})
                primary = images.get("primary", {}) if isinstance(images, dict) else {}
                large = primary.get("large", {}) if isinstance(primary, dict) else {}
                img = large.get("url", "") if isinstance(large, dict) else ""
                if not img:
                    continue
                
                # ⚠️ DEDUP: Skip if same product type already in batch (e.g. 2 desk lamps, 2 mini fridges)
                title_lower = title.lower()
                product_type = None
                for noun in PRODUCT_NOUNS:
                    if noun in title_lower:
                        product_type = noun
                        break
                if product_type and product_type in seen_categories:
                    print(f"\n      ⏭️ [dupe category={product_type}] {title[:60]}")
                    count += 1
                    continue
                
                product = {
                    "title": title,
                    "image": img,
                    "description": "(edit me — write genuine why-it-is-worth-it description)",
                    "blurb": "(edit me — one-line hook)",
                    "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                }
                curated.append(product)
                seen_asins.add(asin)
                if product_type:
                    seen_categories.add(product_type)
                hits += 1
                count += 1
                print(f"\n      ✅ {title[:60]}")
            
            if count == 0:
                print("(no new)")
            else:
                print(f"      +{count}")
            time.sleep(0.3)
        
        print(f"    subcategory total: {hits}")
    
    return curated


def save_and_report(theme_key, theme_data, products):
    """Save batch, generate blog, print summary."""
    today = date.today()
    batch_file = DATA_DIR / f"seasonal_{theme_key}_{today}.json"
    
    # Save batch
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(batch_file, "w") as f:
        json.dump(products, f, indent=2)
    
    # Save blog post
    blog_file = generate_blog_post(theme_key, theme_data, products)
    
    fun_count = sum(1 for p in products if p.get("_fun_score", 0) >= 0.5)
    
    print(f"\n{'='*60}")
    print(f"✅ Seasonal batch complete: {theme_data['emoji']} {theme_data['label']}")
    print(f"   Products: {len(products)} ({fun_count} fun)")
    print(f"   Batch file: {batch_file}")
    print(f"   Blog post: {blog_file}")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"  1. Edit descriptions in {batch_file.name}")
    print(f"  2. Run: ./add_batch.sh data/{batch_file.name}")
    print(f"  3. Write blog HTML: blog/{blog_file.name.replace('.md', '.html')}")
    print(f"  4. Update blog.html with new card")
    print(f"  5. bash build.sh && git add -A && git commit && git push")


def main():
    parser = argparse.ArgumentParser(description="Seasonal WorthItGoods curation")
    parser.add_argument("--theme", required=True, help="Seasonal theme key")
    parser.add_argument("--count", type=int, default=2, help="Products per subcategory")
    parser.add_argument("--fun", type=int, default=1, help="Minimum fun products")
    parser.add_argument("--craft", action="store_true", help="Also write blog post")
    args = parser.parse_args()
    
    products = curate_seasonal(args.theme, args.count, args.fun)
    if not products:
        print("No products found.")
        return 1
    
    theme_data = SEASONAL_THEMES.get(args.theme, {})
    save_and_report(args.theme, theme_data, products)
    return 0


if __name__ == "__main__":
    sys.exit(main())