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
    Ensure exactly TARGET_CARDS (9) blog cards before newsletter section,
    WITHOUT breaking the .product-grid container structure.
    Cards are extracted from WITHIN the grid, keeping the grid intact.
    """
    card_tag = '<div class="product-card blog-card">'
    nl_marker = '<!-- NEWSLETTER SIGNUP'
    
    # Step 1: Deduplicate
    html, removed = deduplicate_cards(html)
    if removed:
        print(f"  Removed {removed} duplicate card(s)")
    
    # Step 2: Find the product-grid container
    grid_open = html.find('<div class="product-grid">')
    if grid_open == -1:
        return html
    
    grid_start = grid_open + len('<div class="product-grid">')
    
    # Find grid close by matching depth
    # Count depth from grid_start, find the matching </div>
    depth = 1
    grid_end = grid_start
    while depth > 0 and grid_end < len(html):
        if html[grid_end:grid_end+6] == '</div>':
            depth -= 1
            if depth == 0:
                break
            grid_end += 6
        elif html[grid_end:grid_end+5] == '<div ' or html[grid_end:grid_end+5] == '<div>':
            depth += 1
            grid_end += 1
        else:
            grid_end += 1
    
    if depth > 0:
        return html  # Can't find grid close
    
    grid_end += 6
    grid_content = html[grid_start:grid_end - 6]
    
    # Step 3: Find newsletter section within grid content
    nl_pos = grid_content.find(nl_marker)
    if nl_pos == -1:
        # Try finding the section tag
        nl_pos = grid_content.find('<section id="newsletter"')
    if nl_pos == -1:
        return html  # No newsletter in grid
    
    before_nl = grid_content[:nl_pos]
    after_nl_marker = grid_content[nl_pos:]
    
    # Extract cards from before_nl
    cards_before = []
    pos = 0
    while True:
        start = before_nl.find(card_tag, pos)
        if start == -1:
            break
        scan = start + len(card_tag)
        close_count = 0
        while scan < len(before_nl) and close_count < 2:
            if before_nl[scan:scan+6] == '</div>':
                close_count += 1
                scan += 6
            else:
                scan += 1
        cards_before.append(before_nl[start:scan])
        pos = scan
    
    if len(cards_before) <= TARGET_CARDS:
        return html  # Already correct
    
    # Overflow cards go below newsletter
    cards_to_keep = cards_before[:TARGET_CARDS]
    overflow_cards = cards_before[TARGET_CARDS:]
    
    # Find where the TARGET_CARDS-th card ends in the original content
    kept_cards_html = ''.join(cards_to_keep)
    overflow_cards_html = ''.join(overflow_cards)
    
    # Rebuild grid content: kept cards + newsletter marker + overflow cards
    # The overflow_cards_html goes after the newsletter section
    # Find where newsletter section closes
    nl_section_end = after_nl_marker.find('</section>')
    if nl_section_end >= 0:
        after_nl_rebuilt = (after_nl_marker[:nl_section_end + len('</section>')] +
                          '\n' + overflow_cards_html +
                          after_nl_marker[nl_section_end + len('</section>'):])
    else:
        after_nl_rebuilt = after_nl_marker + '\n' + overflow_cards_html
    
    new_grid_content = kept_cards_html + '\n' + after_nl_rebuilt
    
    # Rebuild the full html
    return html[:grid_start] + new_grid_content + html[grid_end:]
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