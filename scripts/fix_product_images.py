#!/usr/bin/env python3
"""Replace placeholder product images with real ones from PAAPI"""

import json
import os
import re

WORTHIT_REPO = "/home/rock/.openclaw/workspace/worthitgoods-repo"

# Load image map
with open(os.path.join(WORTHIT_REPO, "scripts", ".product_images.json")) as f:
    images = json.load(f)

# Handle corrected ASINs for Belkin and LEVOIT
# The articles link to B08GHXK2B3 (Belkin) and B07R8WZGYP (LEVOIT)
# Their images come from corrected ASINs
images["B08GHXK2B3"] = images["B000JJI6XA"]
images["B07R8WZGYP"] = images["B09GTRVJQM"]

# All article files in comparisons/
articles_dir = os.path.join(WORTHIT_REPO, "comparisons")
article_files = sorted([f for f in os.listdir(articles_dir) if f.endswith(".html")])

print(f"Found {len(article_files)} article files")

total_replaced = 0

for filename in article_files:
    filepath = os.path.join(articles_dir, filename)
    with open(filepath, "r") as f:
        content = f.read()
    
    original = content
    
    # Find ALL placeholder images: https://m.media-amazon.com/images/I/PLACEHOLDER_<ASIN>._SL500_.jpg
    placeholders = re.findall(r'https://m\.media-amazon\.com/images/I/PLACEHOLDER_([A-Z0-9]+)\._SL\d+_\.jpg', content)
    
    if not placeholders:
        # Check if there are any product image wrappers at all
        if 'product-image-wrapper' in content:
            print(f"  {filename}: no placeholders found (already has real images)")
        else:
            print(f"  {filename}: no images found")
        continue
    
    # Replace each placeholder with the correct image
    for asin in placeholders:
        correct_url = images.get(asin)
        if correct_url:
            placeholder_pattern = f'https://m\\.media-amazon\\.com/images/I/PLACEHOLDER_{asin}\\._SL\\d+_\\.jpg'
            count = len(re.findall(placeholder_pattern, content))
            content = re.sub(placeholder_pattern, correct_url, content)
            total_replaced += count
            print(f"  {filename}: replaced {count}x PLACEHOLDER_{asin} → {os.path.basename(correct_url)}")
        else:
            print(f"  {filename}: ⚠️ no image found for {asin}")
    
    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"  ✅ {filename}: saved")

print(f"\nTotal replacements: {total_replaced}")
