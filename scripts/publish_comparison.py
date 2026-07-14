#!/usr/bin/env python3
"""
Publish a scheduled comparison article.
Usage: python3 publish_comparison.py <slug> <date_str> <title> <desc> <image_url>

Example: python3 publish_comparison.py swiss-army-knife-vs-survival-kit "July 22, 2026" "Victorinox Swiss Army Knife vs 14-in-1 Survival Kit — Everyday Carry Showdown" "Two pocket-sized tool kits at almost the same price..." "https://m.media-amazon.com/images/I/41sdKgclicL._SL500_.jpg"

This script:
1. Inserts a blog card at the top of the blog.html grid
2. Copies the comparison HTML to _site/comparisons/
3. Rebuilds and pushes to git
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent

def main():
    if len(sys.argv) < 6:
        print("Usage: publish_comparison.py <slug> <date_str> <title> <desc> <image_url>")
        sys.exit(1)
    
    slug = sys.argv[1]
    date_str = sys.argv[2]
    title = sys.argv[3]
    short_desc = sys.argv[4]
    image_url = sys.argv[5]
    
    blog_path = REPO_ROOT / "blog.html"
    article_path = REPO_ROOT / "comparisons" / f"{slug}.html"
    
    if not article_path.exists():
        print(f"ERROR: Article not found at {article_path}")
        sys.exit(1)
    
    # Read blog.html
    with open(blog_path) as f:
        html = f.read()
    
    # Build the blog card HTML
    card = f"""<div class="product-card blog-card">
                <div class="image-wrapper">
                    <img src="{image_url}" alt="{title}" loading="lazy">
                </div>
                <div class="content">
                    <h3><a href="comparisons/{slug}.html" style="text-decoration: none; color: inherit;">{title}</a></h3>
                    <p style="color: #666; font-size: 0.95rem; margin-bottom: 1rem;">{date_str} · Comparison</p>
                    <p class="short-desc">{short_desc}</p>
                    <a href="comparisons/{slug}.html" class="cta" style="margin-top: auto;">Read Comparison →</a>
                </div>
            </div>

"""
    
    # Insert after the <div class="product-grid"> tag (at the top)
    insert_marker = '<div class="product-grid">\n\n'
    if insert_marker not in html:
        # Try without the extra newline
        insert_marker = '<div class="product-grid">\n'
        if insert_marker not in html:
            print("ERROR: Could not find product-grid tag in blog.html")
            sys.exit(1)
    
    html = html.replace(insert_marker, insert_marker + card, 1)
    
    with open(blog_path, 'w') as f:
        f.write(html)
    
    print(f"✅ Updated blog.html with new card for '{title}'")
    
    # Build the site
    os.chdir(str(REPO_ROOT))
    ret = os.system("bash build.sh")
    if ret != 0:
        print(f"WARNING: Build returned {ret}")
    
    # Git operations
    os.system("git add -A")
    os.system(f'git commit -m "publish: {slug}"')
    ret = os.system("git push origin master")
    if ret != 0:
        # Try main branch
        os.system("git push origin main")
    
    print(f"✅ Published: https://www.worthitgoods.com/comparisons/{slug}.html")

if __name__ == "__main__":
    main()
