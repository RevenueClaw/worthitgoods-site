#!/usr/bin/env python3
"""AMZ compliance scrubber (2026-11-20).

Amazon Associates Operating Agreement: pricing content from the Program APIs may
be stored/cached for AT MOST 24 hours. Our static comparison pages baked in
PAAPI-era prices ("$32.99", "(as of November 05, 2026)", Price table rows, CTA
"Buy X — $40.00", JSON-LD Offer price fields) that are now months old — the
exact violation flagged in the Nov 5 Amazon notice (master storeID
vhicklegar011-20, covers worthitgoods-20 tracking ID).

This script strips stored PRICE content while keeping the page useful: links,
feature tables, verdicts and CTAs stay; price values become "Check current
price". Idempotent; editorial prose about non-Amazon facts is untouched.

Usage:
  python3 scripts/amz_price_scrub.py DIR [DIR...] [--dry]
Exit code: 0 = clean (or scrubbed ok), 1 = leftovers remain.
"""
import glob
import json
import os
import re
import sys

DOLLAR = r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?"

PATTERNS = [
    # (name, regex, replacement, flags)
    ("as-of stamp", re.compile(r"\(\s*(?:price\s+)?as of [A-Za-z]+ \d{1,2}, \d{4}\s*\)"), "", 0),
    ("as-of span", re.compile(r'\s*<span class="price-as-of"[^>]*>.*?</span>', re.S), "", 0),
    ("as-of inline span",
     re.compile(r'\s*<span[^>]*>\s*\((?:price\s+)?as of [A-Za-z]+ \d{1,2}, \d{4}\s*\)\s*</span>'), "", 0),
    # sentence form baked by older comparison templates:
    # "Prices shown are as of July 19, 2026. Amazon prices change frequently — ..."
    ("as-of sentence",
     re.compile(r'Prices shown are as of [A-Za-z]+ \d{1,2}, \d{4}\.\s*'), "", 0),
    # literal two-char "backslash-n" sequences a bad template left in prose
    ("literal-newline before tag", re.compile(r'\\n(?=</?(?:p|div|ul|h[1-4])\b)'), "\n", 0),
    # literal "\n" escape sequences left in rendered footers by a bad insert
    ("literal-newline before CTA para", re.compile(r'purchases\. \\n<p>'), 'purchases. <p>', 0),
    ("literal-newline after para", re.compile(r'</p>\\n(Amazon pricing)'), r'</p><p>\1', 0),
    ("price-tag value",
     re.compile(r'(<span class="price-tag"[^>]*>)\s*' + DOLLAR + r'(?:\s*(?:-|to|&ndash;|–)\s*' + DOLLAR + r')?\s*(</span>)', re.S),
     r"\1Check current price\2", 0),
    ("CTA price suffix",
     re.compile(r'(>[^<>]{0,160}?)\s*(?:&mdash;|—|–|-)\s*' + DOLLAR + r'(?:\s*(?:&ndash;|–|-)\s*' + DOLLAR + r')?\s*(?=</a>)'),
     r"\1", 0),
]

# Price rows: replace dollar cells inside a row whose label is "Price"
PRICE_ROW = re.compile(r'(<td class="label">\s*Price\s*</td>)(.*?)(</tr>)', re.S)
TD_DOLLAR = re.compile(r'(<td>\s*(?:<strong>)?\s*)' + DOLLAR + r'(\s*(?:</strong>)?\s*</td>)', re.S)
# Any other plain <td>$X</td> (comparison grids)
LONE_TD = re.compile(r'(<td>(?:<strong>)?)\s*' + DOLLAR + r'\s*(</strong></td>|</td>)')

LD_BLOCK = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
LD_PRICE_KEY = re.compile(r'"(?:price|priceCurrency|priceRange|priceValidUntil)"\s*:\s*"?[\d.,A-Z]+"?\s*,?')


def scrub_ld(match):
    head, body, tail = match.groups()
    if '"price' not in body:
        return match.group(0)
    new = LD_PRICE_KEY.sub("", body)
    # fix dangling commas introduced by removals
    new = re.sub(r",\s*([}\]])", r"\1", new)
    new = re.sub(r'("offers"\s*:\s*\{)\s*(\})', r"\1\2", new)
    try:
        json.loads(new)
    except Exception:
        # last resort: drop whole offers objects that lost their price data
        new = re.sub(r'"offers"\s*:\s*\{(?:[^{}]|\{[^{}]*\})*\},?', "", new)
        new = re.sub(r",\s*([}\]])", r"\1", new)
        try:
            json.loads(new)
        except Exception:
            return head + '{"@context":"https://schema.org","@type":"WebPage"}' + tail
    return head + new + tail


CELL_MONEY = re.compile(r"[~\u2248]?\s*\$\d[\d,]*(?:\.\d+)?(?:\s*(?:-|\u2013|\u2014|to|&ndash;)\s*[~\u2248]?\s*\$\d[\d,]*(?:\.\d+)?)?")
CTA_ANCHOR = re.compile(r'(<a [^>]*class="article-cta"[^>]*>)([^<]*)</a>')


def _row_cells(m):
    inner = CELL_MONEY.sub("Check current price", m.group(2))
    inner = re.sub(r"\s{2,}(?=</)", " ", inner)
    return m.group(1) + inner + m.group(3)


def _cta_text(m):
    txt = CELL_MONEY.sub("", m.group(2))
    txt = re.sub(r"[,\u2014\u2013(-]\s*$", "", txt).strip()
    txt = re.sub(r"\s{2,}", " ", txt)
    return m.group(1) + txt + "</a>"


def scrub_text(h: str) -> str:
    h = LD_BLOCK.sub(scrub_ld, h)
    h = PRICE_ROW.sub(_row_cells, h)
    for name, rx, repl, _f in PATTERNS:
        h = rx.sub(repl, h)
    h = LONE_TD.sub(lambda m: m.group(1) + "Check current price" + m.group(2), h)
    h = CTA_ANCHOR.sub(_cta_text, h)
    return h


def remaining(h: str):
    """Strict leftovers check: dollars ONLY inside known price constructs."""
    hits = []
    if re.search(r'<span class="price-tag"[^>]*>[^<]*\$', h) or \
       re.search(r'<span class="price-tag"[^>]*>\s*<a[^>]*>[^<]*\$', h):
        hits.append("price-tag")
    if re.search(r'price-as-of|\((?:price\s+)?as of [A-Za-z]+ \d{1,2}, \d{4}\)|Prices shown are as of [A-Za-z]+ \d{1,2},', h):
        hits.append("as-of")
    for m in LD_BLOCK.finditer(h):
        if re.search(r'"(?:price|priceRange)"\s*:', m.group(2)):
            hits.append("jsonld")
            break
    for m in PRICE_ROW.finditer(h):
        if re.search(r"[~\u2248]?\s*\$\d", m.group(2)):
            hits.append("price-row")
            break
    for m in CTA_ANCHOR.finditer(h):
        if re.search(r"\$\d", m.group(2)):
            hits.append("cta-price")
            break
    return hits


def main():
    args = [a for a in sys.argv[1:] if a != "--dry"]
    dry = "--dry" in sys.argv
    dirs = [a for a in args if os.path.isdir(a)]
    if not dirs:
        sys.exit("usage: amz_price_scrub.py DIR [DIR...] [--dry]")
    changed = total = problems = 0
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "**", "*.html"), recursive=True)):
            total += 1
            src = open(f, encoding="utf-8", errors="ignore").read()
            if ("price-tag" not in src and "price-as-of" not in src and '"price' not in src
                    and "Prices shown are as of" not in src
                    and DOLLAR.replace("\\", "") not in src):
                continue
            out = scrub_text(src)
            if out != src:
                changed += 1
                if not dry:
                    open(f, "w", encoding="utf-8").write(out)
                    left = remaining(out)
                    if left:
                        problems += 1
                        print(f"LEFTOVER {os.path.basename(f)}: {set(left)}")
            else:
                left = remaining(src)
                if left:
                    problems += 1
                    print(f"UNMATCHED {os.path.basename(f)}: {set(left)}")
    print(f"{'DRY ' if dry else ''}scanned={total} changed={changed} files_with_leftovers={problems}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
