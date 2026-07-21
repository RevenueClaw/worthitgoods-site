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

CARD_PATTERN = r'<div class="product-card blog-card">.*?</div>\s*</div>'
NL_MARKER = '<!-- NEWSLETTER SIGNUP'
TARGET_CARDS = 9


def enforce_9_cards_before_nl(html: str) -> str:
    """
    Ensure exactly TARGET_CARDS (9) blog cards appear before the newsletter section.
    Overflow cards are moved below the newsletter section.
    Works correctly even if multiple cards need to be moved.
    """
    nl_pos = html.find(NL_MARKER)
    if nl_pos <= 0:
        return html  # No newsletter section found, skip

    before_nl = html[:nl_pos]
    after_nl = html[nl_pos:]

    cards_before = list(re.finditer(CARD_PATTERN, before_nl, re.S))

    if len(cards_before) <= TARGET_CARDS:
        return html  # Already correct

    # Move all overflow cards (oldest ones) below newsletter
    overflow_count = len(cards_before) - TARGET_CARDS
    overflow_cards = []

    for i in range(overflow_count):
        c = cards_before[TARGET_CARDS]  # Always the (TARGET_CARDS+1)th card after each removal
        overflow_cards.append(c.group())
        before_nl = before_nl[:c.start()] + before_nl[c.end():]
        # Re-scan for remaining cards
        cards_before = list(re.finditer(CARD_PATTERN, before_nl, re.S))

    # Insert all overflow cards after the newsletter section </section>
    overflow_html = '\n\n'.join(overflow_cards) + '\n'
    after_nl = after_nl.replace('</section>', '</section>\n\n' + overflow_html, 1)

    return before_nl + after_nl


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

        # Count cards
        nl_pos = html.find(NL_MARKER)
        before = html[:nl_pos]
        after = html[nl_pos:]
        before_count = len(list(re.finditer(CARD_PATTERN, before, re.S)))
        after_count = len(list(re.finditer(CARD_PATTERN, after, re.S)))

        print(f"✅ Enforced {TARGET_CARDS}-card limit: {before_count} before nl, {after_count} after nl")
    else:
        print(f"✅ Already at {TARGET_CARDS} cards before newsletter — no changes needed")


if __name__ == "__main__":
    main()