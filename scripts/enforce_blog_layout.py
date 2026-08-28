#!/usr/bin/env python3
"""
Enforce exactly 9 blog cards before the newsletter section.
Call this from any script that modifies blog.html.

Usage:
    from enforce_blog_layout import enforce_9_cards_before_nl
    html = enforce_9_cards_before_nl(html)
    # or standalone:
    # python3 scripts/enforce_blog_layout.py blog.html
"""

import re
import sys
from pathlib import Path

NL_MARKER = '<!-- NEWSLETTER SIGNUP'
TARGET_CARDS = 9


def extract_cards(html, start_pos=0):
    """
    Extract full blog cards by properly handling nested divs.
    Returns list of (start, end, content) tuples.
    """
    cards = []
    pos = start_pos
    while True:
        start = html.find('<div class="product-card blog-card">', pos)
        if start == -1:
            break
        # Walk through to find matching closing divs
        # Card structure: <div class="product-card blog-card">...<inner div>...</div>...</div>
        # We need to find the second </div> after the opening tag
        scan = start + len('<div class="product-card blog-card">')
        close_count = 0
        while scan < len(html) and close_count < 2:
            if html[scan:scan+6] == '</div>':
                close_count += 1
                scan += 6
            else:
                scan += 1
        card = html[start:scan]
        cards.append((start, scan, card))
        pos = scan
    return cards


def deduplicate_cards(html):
    """
    Remove duplicate blog cards (same href slug appearing more than once).
    Keeps the FIRST occurrence (which is highest/newest), removes later duplicates.
    """
    cards = extract_cards(html)
    seen_slugs = set()
    remove_ranges = []
    
    for start, end, card in cards:
        slug_match = re.search(r'href="blog/([^"]+)"', card)
        if slug_match:
            slug = slug_match.group(1)
            if slug in seen_slugs:
                remove_ranges.append((start, end))
            else:
                seen_slugs.add(slug)
    
    # Remove duplicates from bottom to top to preserve offsets
    for start, end in sorted(remove_ranges, reverse=True):
        html = html[:start] + html[end:]
    
    return html, len(remove_ranges)


def enforce_9_cards_before_nl(html: str) -> str:
    """
    Step 1: Deduplicate cards (remove duplicate hrefs)
    Step 2: Ensure exactly TARGET_CARDS (9) blog cards before newsletter.
    """
    # Step 1: Deduplicate
    html, removed = deduplicate_cards(html)
    if removed:
        print(f"  Removed {removed} duplicate card(s)")
    
    # Step 2: Enforce 9-card limit
    nl_pos = html.find(NL_MARKER)
    if nl_pos <= 0:
        return html  # No newsletter section found
    
    before_nl = html[:nl_pos]
    after_nl = html[nl_pos:]
    
    cards_before = extract_cards(before_nl)
    
    if len(cards_before) <= TARGET_CARDS:
        return html  # Already correct
    
    # Move overflow cards below newsletter
    overflow_count = len(cards_before) - TARGET_CARDS
    
    # Find the position of the TARGET_CARDS-th card's end
    # The first TARGET_CARDS cards stay; the rest go below newsletter
    split_pos = cards_before[TARGET_CARDS - 1][1]  # end of the TARGET_CARDS-th card
    
    # Everything after the last kept card but before newsletter goes below
    overflow_html = before_nl[split_pos:].strip()
    kept_before = before_nl[:split_pos]
    
    # Insert overflow after newsletter section close
    after_nl = after_nl.replace('</section>', '</section>\n\n' + overflow_html + '\n', 1)
    
    return kept_before + after_nl


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 enforce_blog_layout.py <blog.html>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    html = path.read_text()
    original = html
    html = enforce_9_cards_before_nl(html)

    if html != original:
        path.write_text(html)
        before_count = len(extract_cards(html[:html.find(NL_MARKER)])) if NL_MARKER in html else 0
        print(f"✅ Blog layout enforced: {before_count} cards before newsletter")
    else:
        print(f"✅ No changes needed")


if __name__ == "__main__":
    main()