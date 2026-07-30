#!/usr/bin/env python3
"""
Generate Google Shopping XML product feed from WorthItGoods products.

Output: ../google_shopping_products.xml
Submits to Google Merchant Center (feed URL) when deployed.

Google Shopping feed format: https://support.google.com/merchants/answer/7052112
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

BASE_DIR = Path(__file__).parent.parent
PRODUCTS_FILE = BASE_DIR / "worthitgoods_products.json"
OUTPUT_FILE = BASE_DIR / "google_shopping_products.xml"
SITE_URL = "https://www.worthitgoods.com"

# ─── FEED CONFIG ────────────────────────────────────────────────
FEED_TITLE = "WorthIt Goods — Product Feed"
FEED_LINK = SITE_URL
FEED_DESCRIPTION = "Curated products worth buying — hand-picked deals and comparisons"
# ────────────────────────────────────────────────────────────────


def load_products():
    with open(PRODUCTS_FILE) as f:
        return json.load(f)


def extract_brand(title: str) -> str:
    """Extract likely brand from product title (first word before common delimiters)."""
    common_brands = {
        "HOTLIGH", "XXXFLOWER", "Gerber", "OLIGHT", "Rerdeim", "Surviveware",
        "Govee", "GoveeLife", "Anker", "Belkin", "Coleman", "Carhartt",
        "Chemical Guys", "Mothers", "Cliganic", "Victrola", "Dosmix",
        "Klein Tools", "Megapro", "Huepar", "Noco", "Nintendo", "Amazon Basics",
        "Kasa", "Philips", "LEVOIT", "Biolite", "Luci", "Tomtoc", "Matein",
        "Lovevook", "Wimius", "Hompow", "BAND-AID", "Surviveware", "Hotor",
        "Fortem", "Depstech", "Lint Lizard", "Petode", "Deyace", "Ninja",
        "Homintell", "Angry Mama", "Impresa", "Spring Chef", "Mueller",
        "Addtam", "Mueller", "Victrola", "Jisulife", "Fly2Sky", "AZIO",
        "Klein Tools", "Dioche", "Snow Deer", "Lorell", "WALFOS", "Souper Cubes"
    }

    for brand in sorted(common_brands, key=len, reverse=True):
        if brand.lower() in title.lower():
            return brand

    # Fallback: grab first word (usually the brand)
    first_word = title.split()[0]
    # Remove common non-brand prefixes
    first_word = first_word.strip("[](){}").strip(",").strip(":")
    if first_word and len(first_word) > 1 and first_word.isascii():
        return first_word
    return "Generic"


def generate_feed(products):
    """Generate Google Shopping XML product feed."""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = []
    lines.append('<?xml version="1.0"?>')
    lines.append('<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">')
    lines.append("  <channel>")
    lines.append(f"    <title>{xml_escape(FEED_TITLE)}</title>")
    lines.append(f"    <link>{xml_escape(FEED_LINK)}</link>")
    lines.append(f"    <description>{xml_escape(FEED_DESCRIPTION)}</description>")
    lines.append(f"    <lastBuildDate>{now}</lastBuildDate>")

    item_count = 0
    for product in products:
        asin = product.get("asin")
        title = product.get("title", "")
        description = product.get("description", "")
        price = product.get("price")
        image = product.get("image", "")
        url = product.get("url", "")
        availability = product.get("availability", "IN_STOCK")
        currency = product.get("currency", "USD")

        if not asin or not title or not price:
            continue

        # Skip products without reasonable prices
        try:
            price_val = float(price)
        except (ValueError, TypeError):
            continue
        if price_val < 2.0 or price_val > 9999:
            continue

        brand = extract_brand(title)
        # Truncate description for feed (max 5000 chars)
        desc_clean = description.strip()[:2000]
        if not desc_clean:
            desc_clean = f"Check price on Amazon for {title}"

        # Build unique ID - use ASIN
        item_id = asin

        # Availability mapping
        g_avail = "in_stock" if availability in ("IN_STOCK", True) else "out_of_stock"

        # Price format: "22.08 USD"
        price_str = f"{price_val:.2f} {currency}"

        # Product page URL (worthitgoods page with affiliate link)
        # Use the Amazon affiliate URL directly since we don't have per-product pages
        product_url = url or f"https://www.amazon.com/dp/{asin}?tag=worthitgoods-20"

        # Image fallback
        if not image:
            image = f"https://m.media-amazon.com/images/P/{asin}._SL500_.jpg"

        lines.append("    <item>")
        lines.append(f"      <g:id>{xml_escape(item_id)}</g:id>")
        lines.append(f"      <g:title>{xml_escape(title[:150])}</g:title>")
        lines.append(f"      <g:description>{xml_escape(desc_clean[:5000])}</g:description>")
        lines.append(f"      <g:link>{xml_escape(product_url)}</g:link>")
        lines.append(f"      <g:image_link>{xml_escape(image)}</g:image_link>")
        lines.append(f"      <g:price>{xml_escape(price_str)}</g:price>")
        lines.append(f"      <g:availability>{g_avail}</g:availability>")
        lines.append(f"      <g:brand>{xml_escape(brand[:70])}</g:brand>")
        lines.append(f"      <g:condition>new</g:condition>")
        lines.append(f"      <g:mpn>{xml_escape(asin)}</g:mpn>")
        lines.append(f"      <g:adult>no</g:adult>")
        # Custom label for categories
        lines.append(f"      <g:product_type>{xml_escape('Home & Kitchen')}</g:product_type>")
        lines.append(f"      <g:google_product_category>Home &amp; Garden</g:google_product_category>")
        lines.append("    </item>")
        item_count += 1

    lines.append("  </channel>")
    lines.append("</rss>")

    return "\n".join(lines), item_count


def main():
    print("=== Google Shopping Feed Generator ===")

    # Load products
    if not PRODUCTS_FILE.exists():
        print(f"ERROR: Products file not found: {PRODUCTS_FILE}")
        sys.exit(1)

    products = load_products()
    print(f"Loaded {len(products)} products")

    # Generate feed
    feed_xml, count = generate_feed(products)
    print(f"Generated feed with {count} products")

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        f.write(feed_xml)

    file_size = OUTPUT_FILE.stat().st_size
    print(f"Written to: {OUTPUT_FILE} ({file_size:,} bytes)")

    print(f"\nFeed URL when deployed: https://www.worthitgoods.com/google_shopping_products.xml")
    print("\n=== Done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())