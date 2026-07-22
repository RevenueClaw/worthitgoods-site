#!/usr/bin/env python3
"""Add product images from Amazon to all comparison articles on worthitgoods.com"""

import re
import sys
import json
import subprocess
import os

# Find shared lib
_LIB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
if os.path.isdir(_LIB_PATH):
    sys.path.insert(0, os.path.dirname(_LIB_PATH))

# ── Master ASIN→Article mapping ──
# Each entry: (filename, [(product_card_index, asin, label), ...])
# product_card_index: 0-based index of .article-product-card divs in the file

ARTICLES = {
    "comparisons/100w-gan-vs-30w-charger.html": [
        (0, "B0CB1D82NB", "INIU 100W GaN Charger"),
        (1, "B0BZHZ56M9", "UGREEN Uno 30W Charger"),
    ],
    "comparisons/addtam-vs-belkin-surge-protector.html": [
        (0, "B09XMMZSWW", "Addtam Surge Protector"),
        (1, "B08GHXK2B3", "Belkin Surge Protector"),
    ],
    "comparisons/camping-lantern-vs-neck-light-vs-spotlight.html": [
        (0, "B09M68SFL9", "FLY2SKY Camping Lantern"),
        (1, "B07WNRN9WQ", "Glocusent Neck Light"),
        (2, "B0CL465G9L", "YIERBLUE Spotlight"),
    ],
    "comparisons/chemical-guys-vs-mothers-clay-bar.html": [
        (0, "B004GF1OVY", "Chemical Guys Clay Bar"),
        (1, "B0002U2V1Y", "Mothers Clay Bar"),
    ],
    "comparisons/goveelife-vs-levoit-mini-air-purifier.html": [
        (0, "B0C3QQMMRJ", "GoveeLife Air Purifier"),
        (1, "B07R8WZGYP", "LEVOIT Air Purifier"),
    ],
    "comparisons/handheld-turbo-fan-vs-jisulife.html": [
        (0, "B0GD7FZTC2", "Diveblues Turbo Fan"),
        (1, "B0CR3JJJTS", "JISULIFE Life9 Fan"),
    ],
    "comparisons/hompow-vs-wimius-mini-projector.html": [
        (0, "B0F43Q5B9K", "HOMPOW Mini Projector"),
        (1, "B08TMFRLH4", "WiMiUS Mini Projector"),
    ],
    "comparisons/kitchen-tools-under-11.html": [
        (0, "B07H7ZDBV4", "Splatypus Jar Spatula"),
        (1, "B09P6HFCSP", "Magnetic Measuring Spoons"),
        (2, "B0738C7RXF", "Deiss PRO Zester"),
        (3, "B07VLBVQBP", "Red the Crab Utensil Rest"),
    ],
    "comparisons/sawyer-permethrin-vs-bens-clothing-gear.html": [
        (0, "B001ANQVYU", "Sawyer Permethrin"),
        (1, "B06X9Q2HJ2", "Ben's Clothing & Gear"),
    ],
    "comparisons/victorinox-vs-leatherman-rev-multitool.html": [
        (0, "B0007QCOC4", "Victorinox Tinker"),
        (1, "B07Z8WHZWV", "14-in-1 Survival Kit"),
    ],
    "comparisons/tens-7000-vs-auvon.html": [
        (0, "B00NCRE4GO", "TENS 7000"),
        (1, "B085TL8TPJ", "AUVON TENS Unit"),
    ],
    "comparisons/tens-unit-vs-muscle-roller.html": [
        (0, "B00NCRE4GO", "TENS 7000"),
        (1, "B0836Y45HD", "Muscle Roller"),
    ],
}

WORTHIT_REPO = "/home/rock/.openclaw/workspace/worthitgoods-repo"


def get_image_via_paapi(asins):
    """Try PAAPI via shared workspace lib"""
    print(f"  PAAPI lookup for {len(asins)} ASINs...")
    try:
        from lib.amazon_paapi import AmazonCreatorsAPI
        api = AmazonCreatorsAPI()
        results = api.get_items(asins)
        images = {}
        for asin in asins:
            if asin in results:
                item = results[asin]
                try:
                    url = item["images"]["primary"]["large"]["url"]
                    images[asin] = url
                    print(f"    ✓ {asin}: {url}")
                except (KeyError, TypeError):
                    print(f"    ✗ {asin}: no image in PAAPI response")
            else:
                print(f"    ✗ {asin}: not found in PAAPI response")
        return images
    except Exception as e:
        print(f"  PAAPI failed: {e}")
        return {}


def get_image_via_curl(asin):
    """Fallback: scrape Amazon product page for image URL"""
    import urllib.request
    url = f"https://www.amazon.com/dp/{asin}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # Try to find image URL in the page
        # Look for the main product image in JSON-LD or og:image
        match = re.search(r'"image"\s*:\s*"([^"]+)"', html)
        if match:
            return match.group(1)
        match = re.search(r'property="og:image"\s+content="([^"]+)"', html)
        if match:
            return match.group(1)
        # Try the colorImages JSON
        match = re.search(r'"hiRes"\s*:\s*"([^"]+)"', html)
        if match:
            return match.group(1).replace("\\u0026", "&")
        return None
    except Exception as e:
        print(f"    ✗ curl failed for {asin}: {e}")
        return None


def fetch_all_images(all_asins):
    """Fetch images for all unique ASINs, trying PAAPI first then curl fallback"""
    unique_asins = list(set(all_asins))
    images = {}
    
    # Try PAAPI first
    print("\n📡 Trying PAAPI...")
    paapi_images = get_image_via_paapi(unique_asins)
    images.update(paapi_images)
    
    # Fallback to curl for missing
    missing = [a for a in unique_asins if a not in images]
    if missing:
        print(f"\n🔄 Falling back to curl for {len(missing)} ASINs...")
        for asin in missing:
            img = get_image_via_curl(asin)
            if img:
                images[asin] = img
                print(f"    ✓ {asin}: {img}")
            else:
                print(f"    ✗ {asin}: no image found")
                # Use a placeholder
                images[asin] = f"https://m.media-amazon.com/images/I/PLACEHOLDER_{asin}._SL500_.jpg"
    
    return images


def inject_image_into_product_card(html, card_idx, image_url):
    """Inject an <img> tag into the specified .article-product-card div"""
    # Find all product cards
    pattern = r'(<div class="article-product-card[^"]*"[^>]*>)'
    
    matches = list(re.finditer(pattern, html))
    if card_idx >= len(matches):
        print(f"    ✗ Card index {card_idx} not found (only {len(matches)} cards)")
        return html
    
    match = matches[card_idx]
    card_open = match.group(1)
    
    # Find where the content starts (after the opening div tag)
    pos = match.end()
    
    # Find the first heading (h3) in this card
    heading_match = re.search(r'<h3>', html[pos:])
    if not heading_match:
        print(f"    ✗ No h3 found in card {card_idx}")
        return html
    
    insert_pos = pos + heading_match.start()
    
    # Build image HTML
    img_html = f'\n  <div class="product-image-wrapper">\n    <img src="{image_url}" alt="{card_open}" class="product-img" loading="lazy">\n  </div>\n  '
    
    before = html[:insert_pos]
    after = html[insert_pos:]
    return before + img_html + after


def add_image_css(html):
    """Add CSS for product images if not already present"""
    if ".product-img" in html:
        return html
    
    css_block = """
  .product-img { width: 100%; max-width: 300px; border-radius: 8px; margin-bottom: 16px; display: block; }
  .product-image-wrapper { text-align: center; margin-bottom: 8px; }
"""
    
    # Insert after opening <style> tag or before </style>
    style_end = html.find("</style>")
    if style_end != -1:
        return html[:style_end] + css_block + html[style_end:]
    
    # No style block found, insert before </head>
    head_end = html.find("</head>")
    if head_end != -1:
        style_tag = f"<style>{css_block}</style>\n"
        return html[:head_end] + style_tag + html[head_end:]
    
    return html


def process_articles(images):
    """Process all articles, injecting images into product cards"""
    
    for rel_path, cards in ARTICLES.items():
        abs_path = os.path.join(WORTHIT_REPO, rel_path)
        
        if not os.path.exists(abs_path):
            print(f"\n❌ {rel_path}: file not found")
            continue
        
        print(f"\n📄 {rel_path}:")
        
        with open(abs_path, "r") as f:
            html = f.read()
        
        # Add CSS first
        html = add_image_css(html)
        
        # Inject images for each card (process in reverse order to preserve indices)
        for card_idx, asin, label in sorted(cards, key=lambda x: -x[0]):
            img_url = images.get(asin)
            if not img_url:
                print(f"  ⚠️ No image for {asin} ({label}), skipping")
                continue
            print(f"  🖼️ Card {card_idx}: {label} ({asin})")
            html = inject_image_into_product_card(html, card_idx, img_url)
        
        # Write back
        with open(abs_path, "w") as f:
            f.write(html)
        
        print(f"  ✅ Updated {rel_path}")


def main():
    print("=" * 60)
    print("📸 WorthItGoods — Product Image Inserter")
    print("=" * 60)
    
    os.chdir(WORTHIT_REPO)
    
    # Collect all ASINs
    all_asins = []
    for cards in ARTICLES.values():
        for _, asin, _ in cards:
            all_asins.append(asin)
    
    print(f"\n📦 Articles: {len(ARTICLES)}")
    print(f"🔢 ASINs: {len(set(all_asins))} unique out of {len(all_asins)} total")
    print(f"   ASINs: {', '.join(sorted(set(all_asins)))}")
    
    # Fetch images
    images = fetch_all_images(all_asins)
    
    print(f"\n📊 Results: {len(images)}/{len(set(all_asins))} images fetched")
    
    # Process articles
    process_articles(images)
    
    print(f"\n{'=' * 60}")
    print("✅ Done! All articles updated.")
    print("=" * 60)
    
    # Save image map for reference
    with open("scripts/.product_images.json", "w") as f:
        json.dump(images, f, indent=2)
    print("📝 Image map saved to scripts/.product_images.json")


if __name__ == "__main__":
    main()
