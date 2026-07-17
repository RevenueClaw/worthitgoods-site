#!/usr/bin/env python3
"""
WorthIt Goods — automated bi-weekly blog post generator.

Usage:
    python3 generate-blog-post.py [--dry-run]

Picks a theme, selects 5-6 matching products, uses LLM to write intro/conclusion
in an honest, non-slop voice, and outputs a complete blog post + updates blog.html.

Requires LLM_API_KEY env var or uses fallback gateway @ 192.168.4.131:18792.
"""

import os, sys, re, json, html as htmlmod, random, datetime, urllib.request, urllib.error
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "sample_products.json"
BLOG_DIR = BASE / "blog"
BLOG_INDEX = BASE / "blog.html"

THEMES = {
    "kitchen-essentials": {
        "title": "Kitchen Essentials That Earn Their Drawer Space",
        "desc": "Real tools that make cooking less frustrating. No unitaskers, no gimmicks.",
        "slug_prefix": "kitchen-essentials",
        "match": lambda t, b, d: bool(re.search(r'(measur|spatula|grater|zest|kitchen|cook|chef|bake|knife|peeler|cutter|strainer|whisk|bowl|spoon|towel|soap|clean|scrub|squeeze|stor(?:age|e)|organiz|pantry|counter|dish)', (t+' '+b+' '+d).lower())) and not re.search(r'(watch|phone|cable|backpack|survival|flashlight|multitool|cocktail|smoker|wine|beer|drinkware|flask|barware|can.?holder)', (t+' '+b+' '+d).lower())
    },
    "edc-pocket-gear": {
        "title": "Everyday Carry: Gear You'll Actually Use",
        "desc": "Pocket-sized tools that earn their spot in your bag or pocket.",
        "slug_prefix": "edc-pocket-gear",
        "match": lambda t, b, d: bool(re.search(r'(multitool|knife|flashlight|wallet|keychain|pocket|edc|survival|tinker|swiss.+army)', (t+' '+b+' '+d).lower()))
    },
    "home-office": {
        "title": "Home & Desk Upgrades That Make a Difference",
        "desc": "Small improvements for where you spend most of your time.",
        "slug_prefix": "home-office",
        "match": lambda t, b, d: bool(re.search(r'(lamp|desk|organiz|charger|cable|dock|stand|monitor|mouse|keyboard|mat|hub|pi\s*case|ethernet|router)', (t+' '+b+' '+d).lower()))
    },
    "gadgets-geekery": {
        "title": "Gadgets & Geekery Worth Your Money",
        "desc": "From retro Pi cases to smart lamps — tech that's actually fun to use.",
        "slug_prefix": "gadgets-geekery",
        "match": lambda t, b, d: bool(re.search(r'(pi\s*case|govee|smart|led|rgb|light|neon|drone|robot|sensor|camera|borescope|tech|gadget|raspberry|geek|nerd|star.?wars|darth|vader|retro|game|controller|console)', (t+' '+b+' '+d).lower()))
    },
    "gift-ideas": {
        "title": "Gift Ideas That Don't Feel Like a Gift Card",
        "desc": "Thoughtful presents that show you paid attention. No clutter, no junk.",
        "slug_prefix": "gift-ideas",
        "match": lambda t, b, d: bool(re.search(r'(gift|present|decor|vase|coaster|mug|glass|watch|sunglass|plush|stuffed|toy|game|puzzle|blanket|candle)', (t+' '+b+' '+d).lower()))
    },
    "outdoor-trail": {
        "title": "Outdoor & Trail Gear That Holds Up",
        "desc": "Camping, hiking, and survival gear that won't let you down when it matters.",
        "slug_prefix": "outdoor-trail",
        "match": lambda t, b, d: bool(re.search(r'(cooler|camp|hike|trail|outdoor|survival|flashlight|spotlight|multitool|emergency|knife|backpack|travel|collapsible|gear)', (t+' '+b+' '+d).lower()))
    },
}

def load_products():
    with open(DATA_FILE) as f:
        return json.load(f)

def pick_products(match_fn, products, count=6):
    matched = [p for p in products if match_fn(p.get("title",""), p.get("blurb",""), p.get("description",""))]
    matched = [p for p in matched if products.index(p) >= 38]
    random.shuffle(matched)
    if len(matched) >= count:
        return matched[:count]
    others = [p for p in products if p not in matched and products.index(p) >= 38]
    random.shuffle(others)
    return matched + others[:count - len(matched)]

def call_llm(prompt, max_tokens=500):
    api_key = os.environ.get("LLM_API_KEY") or ""
    data = json.dumps({
        "model": "openrouter/deepseek/deepseek-v4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }).encode()
    if api_key:
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")
    else:
        req = urllib.request.Request("http://192.168.4.131:18792/infer", data=data,
            headers={"Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"LLM call failed: {e}", file=sys.stderr)
        return None

def get_existing_slugs():
    return set(re.findall(r'href="blog/([^"]+)"', BLOG_INDEX.read_text()))

def gen_card(slug, title, desc, image, date_str):
    return f'\n<div class="product-card blog-card">\n    <div class="image-wrapper">\n        <img src="{image}" alt="{htmlmod.escape(title)}" loading="lazy">\n    </div>\n    <div class="content">\n        <h3><a href="blog/{slug}" style="text-decoration: none; color: inherit;">{htmlmod.escape(title)}</a></h3>\n        <p style="color: #666; font-size: 0.95rem; margin-bottom: 1rem;">{date_str}</p>\n        <p class="short-desc">{desc}</p>\n        <a href="blog/{slug}" class="cta" style="margin-top: auto;">Read More →</a>\n    </div>\n</div>'

def gen_post_html(theme, products, intro_html, conclusion_html):
    slug = f"{datetime.date.today().strftime('%Y-%m-%d')}-{theme['slug_prefix']}"
    today_s = datetime.date.today().strftime("%B %d, %Y")
    first_img = products[0].get('image', '') if products else ''
    prod_sections = ""
    for p in products:
        t = p.get("title", "Product"); img = p.get("image", "")
        blurb = p.get("blurb", ""); desc = p.get("description", ""); aff = p.get("affiliate_url", "/#products")
        why = ""; pros = ""; cons = ""; best = ""
        m = re.search(r"Why It'?s Worth It:?\s*(.*?)(?=Pros:|Cons:|Best for|$)", desc, re.I|re.S)
        if m: why = m.group(1).strip().rstrip('.')
        m = re.search(r"Pros:?\s*(.*?)(?=Cons:|Best for|\[Blurb|$)", desc, re.I|re.S)
        if m: pros = m.group(1).strip().rstrip('.')
        m = re.search(r"Cons:?\s*(.*?)(?=Best for|\[Blurb|$)", desc, re.I|re.S)
        if m: cons = m.group(1).strip().rstrip('.')
        m = re.search(r"Best for:?\s*(.*?)(?=\.|\[Blurb|$)", desc, re.I|re.S)
        if m: best = m.group(1).strip().rstrip('.')
        shy = blurb or desc[:120] + ("..." if len(desc) > 120 else "")
        pros_block = f'<div><h4 style="color:#28a745;">Pros</h4><p>{pros}</p></div>' if pros else ''
        cons_block = f'<div><h4 style="color:#dc3545;">Cons</h4><p>{cons}</p></div>' if cons else ''
        pros_cons = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;margin-bottom:1rem;">{pros_block}{cons_block}</div>' if (pros and cons) else ''
        best_block = f'<h4>Best For</h4><p style="font-weight:500;margin-bottom:1rem;">{best}</p>' if best else ''
        prod_sections += f'\n<section class="product-highlight" style="max-width:650px;margin:0 auto 2.5rem;padding:1.5rem;border:1px solid #ddd;border-radius:12px;background:#fafafa;box-shadow:0 4px 12px rgba(0,0,0,.05);">' + (f'\n    <img src="{img}" alt="{htmlmod.escape(t)}" loading="lazy" style="max-width:100%;max-height:280px;height:auto;object-fit:contain;display:block;margin:0 auto 1.5rem;border-radius:8px;box-shadow:0 4px 8px rgba(0,0,0,.1);">' if img else '') + f'\n    <h2>{htmlmod.escape(t)}</h2>\n    <p style="font-size:1.1em;font-style:italic;color:#555;margin-bottom:1.5rem;">{htmlmod.escape(shy)}</p>\n    <h3 style="color:#ff6b35;">Why It\'s Worth It</h3>\n    <p style="line-height:1.6;margin-bottom:1.5rem;">{why}</p>{pros_cons}{best_block}\n    <a href="{aff}" target="_blank" class="cta" style="display:inline-block;padding:1rem 2rem;background:#ff6b35;color:white;border-radius:8px;font-weight:bold;margin-top:1rem;">Shop on Amazon →</a>\n</section>'
    
    return slug, f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{theme['title']} - WorthIt Goods</title>
<meta property="og:title" content="{theme['title']}">
<meta property="og:description" content="{theme['desc']}">
<meta property="og:image" content="{first_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="https://www.worthitgoods.com/blog/{slug}.html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="WorthItGoods">
<meta name="twitter:card" content="summary_large_image">
<meta name="description" content="{theme['desc']}">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header><nav><a href="/" class="logo">WorthItGoods</a><ul><li><a href="/">Home</a></li><li><a href="/blog.html">Blog</a></li><li><a href="/privacy.html">Privacy</a></li></ul></nav></header>
<div class="hero" style="min-height:300px;"><div class="hero-content"><h1>{theme['title']}</h1><p style="font-size:1.1em;opacity:0.9;margin-top:0.5rem;">{today_s}</p></div></div>
<article class="products-section">
<div class="section-header" style="max-width:650px;margin:0 auto 2rem;"><h2>Introduction</h2>{intro_html}</div>
<h2 style="max-width:650px;margin:2rem auto 1rem;">The Picks</h2>{prod_sections}
<div class="section-header" style="max-width:650px;margin:3rem auto 0;padding:1.5rem;background:#f8f9fa;border-radius:12px;">
<h2>Wrapping It Up</h2><p style="line-height:1.6;font-size:1.1em;">{conclusion_html}</p>
<a href="/#products" style="display:inline-block;margin-top:1rem;font-weight:bold;color:#ff6b35;">Browse the full collection →</a></div>
<p style="text-align:center;margin:3rem 0;"><a href="/blog.html" class="cta-button" style="display:inline-block;padding:1rem 2rem;background:linear-gradient(135deg,#ff9a56,#ff6b6b);color:white;text-decoration:none;border-radius:8px;font-weight:bold;">More Posts</a></p>
</article>
<footer><div style="margin-bottom:18px;">
<a href="/" style="color:#ff9a56;text-decoration:none;margin:0 10px;">Home</a>
<a href="/blog.html" style="color:#ff9a56;text-decoration:none;margin:0 10px;">Blog</a>
<a href="/#products" style="color:#ff9a56;text-decoration:none;margin:0 10px;">All Products</a>
<a href="/privacy.html" style="color:#ff9a56;text-decoration:none;margin:0 10px;">Privacy</a>
</div><p>© 2026 WorthIt Goods.</p><p>As an Amazon Associate, we earn from qualifying purchases.</p></footer>
</body>
</html>"""

def update_index(slug, title, desc, image, date_str):
    content = BLOG_INDEX.read_text()
    card = gen_card(slug, title, desc, image, date_str)
    new = re.sub(r'(<div class="product-grid">\s*\n)', r'\1' + card + '\n', content, count=1)
    if new != content:
        BLOG_INDEX.write_text(new); return True
    return False

def add_custom_to_build(slug):
    text = (BASE / "build.sh").read_text()
    line = f"cp blog/custom-{slug}.html _site/blog/{slug}.html"
    if line in text: return True
    text = text.replace("# Copy privacy page", f"# Blog overlay: {slug}\n{line}\n\n# Copy privacy page")
    (BASE / "build.sh").write_text(text)
    return True

def check_cadence():
    """Check if it's been >10 days since last blog post (bi-weekly guard)."""
    existing = get_existing_slugs()
    dates_found = []
    for slug in existing:
        m = re.search(r'(\d{4}-\d{2}-\d{2})', slug)
        if m:
            try: dates_found.append(datetime.datetime.strptime(m.group(1), '%Y-%m-%d').date())
            except: pass
        # Also check custom files
    for f in os.listdir(BLOG_DIR):
        m = re.search(r'(\d{4}-\d{2}-\d{2})', f)
        if m:
            try: dates_found.append(datetime.datetime.strptime(m.group(1), '%Y-%m-%d').date())
            except: pass
    if dates_found:
        latest = max(dates_found)
        days_since = (date.today() - latest).days
        if days_since < 10:
            print(f"Skipping: last blog was {days_since} days ago (need >10 for bi-weekly)")
            return False
    return True

def choose_theme(products):
    existing = get_existing_slugs()
    scores = {}
    for key, theme in THEMES.items():
        if sum(1 for p in products if theme["match"](p.get("title",""), p.get("blurb",""), p.get("description",""))) >= 4:
            scores[key] = sum(1 for p in products if theme["match"](p.get("title",""), p.get("blurb",""), p.get("description","")))
    if not scores: return "home-office"
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    for key, _ in ranked:
        if THEMES[key]["slug_prefix"] not in " ".join(existing):
            return key
    return ranked[0][0]

def main():
    dry = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    
    if not check_cadence() and not dry and not force:
        print("Use --force to override or wait until >10 days since last post.")
        return
    
    products = load_products()
    tk = choose_theme(products)
    theme = THEMES[tk]
    print(f"Theme: {theme['title']}")
    selected = pick_products(theme["match"], products, 6)
    for p in selected: print(f"  • {p.get('title','?')}")
    
    pl = "\n".join(f"- {p['title']}: {p.get('blurb',p.get('description','')[:150])}" for p in selected)
    prompt = f"Write a blog intro (2-3 paras) and conclusion for a no-nonsense product site.\n\nTheme: {theme['title']}\nProducts:\n{pl}\n\nVoice: honest, direct, slightly irreverent. No 'in today's world' or 'game-changing'. Use contractions. Under 150 words.\n\nINTRO:\n\nCONCLUSION:\n"
    result = call_llm(prompt)
    
    if result:
        im = re.search(r'INTRO:\n(.*?)(?=CONCLUSION:)', result, re.S)
        cm = re.search(r'CONCLUSION:\n(.*)', result, re.S)
        ih = '\n'.join(f'<p>{p.strip()}</p>' for p in re.split(r'\n\n+', im.group(1) if im and im.group(1) else "Here are {len(selected)} products that earn their stay.") if p.strip())
        ch = '\n'.join(f'<p>{p.strip()}</p>' for p in re.split(r'\n\n+', cm.group(1) if cm and cm.group(1) else "They deliver.") if p.strip())
    else:
        ih = f"<p>Here are {len(selected)} products that earn their stay.</p>"
        ch = f"<p>Those are {len(selected)} products that actually deliver. Life's too short for tools that frustrate you.</p>"
    
    slug, html = gen_post_html(theme, selected, ih, ch)
    img = selected[0].get("image","") if selected else ""
    ds = datetime.date.today().strftime("%A, %B %d, %Y")
    
    if dry:
        print(f"\n=== DRY RUN ===\nSlug: {slug}.html\n")
        print(gen_card(slug + ".html", theme['title'], theme['desc'], img, ds))
        return
    
    BLOG_DIR.mkdir(exist_ok=True)
    (BLOG_DIR / f"{slug}.html").write_text(html)
    (BASE / "blog" / f"custom-{slug}.html").write_text(html)
    print(f"Blog: {slug}.html + custom overlay")
    if update_index(slug + ".html", theme['title'], theme['desc'], img, ds):
        print("blog.html updated")
    add_custom_to_build(slug)
    print("build.sh updated")
    print(f"\nNext: bash build.sh && git add -A && git commit -m 'blog: {slug}' && git push origin main")

if __name__ == "__main__":
    main()