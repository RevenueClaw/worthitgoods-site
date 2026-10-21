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
CARD_TAG = '<div class="product-card blog-card">'
TARGET_CARDS = 9


def extract_cards(html, start_pos=0):
    """
    Extract full blog cards, INCLUDING each card's own outer closing </div>,
    by depth-matching nested <div> elements.

    (A card looks like:
        <div class="product-card blog-card">
            <div class="image-wrapper">...</div>
            <div class="content">...</div>
        </div>
     i.e. three closing </div>s. Counting only two drops the card wrapper and
     makes the next card nest inside this one — that is what corrupted the grid.)

    Returns list of (start, end, content) tuples.
    """
    cards = []
    pos = start_pos
    while True:
        start = html.find(CARD_TAG, pos)
        if start == -1:
            break
        i = start + len(CARD_TAG)
        depth = 1
        while i < len(html) and depth > 0:
            if html[i:i + 6] == '</div>':
                depth -= 1
                i += 6
            elif html[i:i + 5] == '<div ' or html[i:i + 5] == '<div>':
                depth += 1
                i += 1
            else:
                i += 1
        cards.append((start, i, html[start:i]))
        pos = i
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
    depth = 1
    grid_end = grid_start
    while depth > 0 and grid_end < len(html):
        if html[grid_end:grid_end + 6] == '</div>':
            depth -= 1
            if depth == 0:
                break
            grid_end += 6
        elif html[grid_end:grid_end + 5] == '<div ' or html[grid_end:grid_end + 5] == '<div>':
            depth += 1
            grid_end += 1
        else:
            grid_end += 1

    if depth > 0:
        return html  # Can't find grid close

    # grid_end now points at the grid's own closing </div>; keep it in the output
    grid_content = html[grid_start:grid_end]

    # Step 3: Find newsletter section within grid content
    nl_pos = grid_content.find(NL_MARKER)
    if nl_pos == -1:
        # Try finding the section tag
        nl_pos = grid_content.find('<section id="newsletter"')
    if nl_pos == -1:
        return html  # No newsletter in grid

    before_nl = grid_content[:nl_pos]
    after_nl_marker = grid_content[nl_pos:]

    # Extract COMPLETE cards from before_nl
    cards_before = [card for _, _, card in extract_cards(before_nl)]

    if len(cards_before) <= TARGET_CARDS:
        return html  # Already correct

    # Overflow cards go below newsletter
    cards_to_keep = cards_before[:TARGET_CARDS]
    overflow_cards = cards_before[TARGET_CARDS:]

    kept_cards_html = '\n'.join(cards_to_keep)
    overflow_cards_html = '\n'.join(overflow_cards)

    # Rebuild grid content: kept cards + newsletter marker + overflow cards
    # The overflow_cards_html goes right after the newsletter section.
    nl_section_end = after_nl_marker.find('</section>')
    if nl_section_end >= 0:
        after_nl_rebuilt = (after_nl_marker[:nl_section_end + len('</section>')] +
                            '\n' + overflow_cards_html +
                            after_nl_marker[nl_section_end + len('</section>'):])
    else:
        after_nl_rebuilt = after_nl_marker + '\n' + overflow_cards_html

    new_grid_content = '\n' + kept_cards_html + '\n' + after_nl_rebuilt

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