#!/usr/bin/env python3
"""
WorthItGoods product-record validator.

Fails closed when:
  (a) title keywords have zero meaningful overlap with description, OR
  (b) raw template placeholders / double-spaces / undefined / TODO appear.

Usage as a module:
    from scripts.validate_product_record import validate_record, validator_summary
    ok, reasons = validate_record(record)

CLI:
    python3 scripts/validate_product_record.py path/to/products.json
"""
import json
import re
import string
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "validation_rejects.log"

_PLACEHOLDER_PATTERNS = [
    re.compile(r"at the current price on Amazon", re.I),
    re.compile(r"\[product\]"),
    re.compile(r"\{[^}]+\}"),
    re.compile(r"\bundefined\b", re.I),
    re.compile(r"\bTODO\b", re.I),
    re.compile(r"\bedit me\b", re.I),
    re.compile(r"\(fill.*\)|\(insert.*\)|\(your .* here\)", re.I),
]

_TITLE_STOP = {
    "the", "and", "for", "with", "from", "that", "this", "into", "they", "their",
    "will", "would", "there", "where", "when", "what", "how", "you", "your", "our",
    "its", "have", "been", "one", "all", "are", "was", "but", "not", "can", "like",
    "than", "only", "just", "about", "over", "such", "each", "these", "those", "has",
    "had", "more", "most", "other", "some", "time", "way", "may", "say", "which",
    "his", "her", "out", "after", "used", "buy", "get", "use", "make", "made", "set",
    "piece", "pieces", "pack", "pcs", "with", "without", "for", "inch", "inches",
}


def _normalize_token(w):
    """Aggressive normalize: lower, drop non-alnum, strip trailing 's/es', eg rgbicww -> rgbic."""
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    if len(w) <= 3:
        return w
    # strip trailing plural-ish s
    if w.endswith("es"):
        w = w[:-2]
    elif w.endswith("s"):
        w = w[:-1]
    return w


def _tokens(text):
    raw = [w for w in re.sub(r"[^a-zA-Z0-9 ]+", " ", text).split() if len(w) >= 3]
    return {_normalize_token(w) for w in raw if _normalize_token(w) and _normalize_token(w) not in _TITLE_STOP}


def _meaningful_overlap(title, description, min_common=1):
    """Return (overlap_count, common_words)."""
    t = _tokens(title)
    d = _tokens(description)
    if not t or not d:
        return 0, set()
    common = t & d
    return len(common), common


def validate_record(record, fail_on_zero_overlap=True):
    """Validate a single record.

    Returns: (passed: bool, reasons: list[str])
    """
    reasons = []
    title = str(record.get("title") or "").strip()
    description = str(record.get("description") or "").strip()

    if not title:
        reasons.append("missing title")
    if not description:
        reasons.append("missing description")

    # Title/Description overlap
    if fail_on_zero_overlap and title and description:
        overlap, words = _meaningful_overlap(title, description)
        if overlap < 1:
            reasons.append(f"title/description overlap=0 (title tokens={_tokens(title)}, desc tokens={_tokens(description)})")

    # Placeholders / template artifacts
    if description:
        for pat in _PLACEHOLDER_PATTERNS:
            if pat.search(description):
                reasons.append(f"placeholder/artifact: {pat.pattern!r}")
        if "  " in description:
            reasons.append("double-space artifact")

    # ASIN/URL consistency
    asin = str(record.get("asin") or "").strip()
    url = str(record.get("url") or record.get("affiliate_url") or "").strip()
    if asin and url:
        m = re.search(r"/dp/([A-Z0-9]{10})(?:\?|$)", url)
        if m and m.group(1) != asin:
            reasons.append(f"ASIN/URL mismatch: field={asin}, url={m.group(1)}")

    return (len(reasons) == 0), reasons


def validate_products(products, rejects_log=None):
    """Validate a list of product dicts.

    Returns {"valid": [...], "invalid": [(record, reasons), ...], "summary": str}
    """
    valid, invalid = [], []
    for rec in products:
        ok, reasons = validate_record(rec)
        if ok:
            valid.append(rec)
        else:
            invalid.append((rec, reasons))

    if rejects_log is not None and invalid:
        rejects_log.parent.mkdir(parents=True, exist_ok=True)
        with open(rejects_log, "a", encoding="utf-8") as f:
            for rec, reasons in invalid:
                title = rec.get("title") or "(no title)"
                asin = rec.get("asin") or asin_from_url(rec.get("url") or rec.get("affiliate_url", "")) or "(no asin)"
                line = f"{Path(__file__).name}: REJECT [{asin}] {title}: {'; '.join(reasons)}\n"
                f.write(line)

    return {
        "valid": valid,
        "invalid": invalid,
        "summary": f"validated {len(products)} records: {len(valid)} passed, {len(invalid)} rejected",
    }


def asin_from_url(url):
    if not url:
        return ""
    m = re.search(r"/dp/([A-Z0-9]{10})(?:\?|$)", url)
    return m.group(1) if m else ""


def main():
    paths = sys.argv[1:] or ["worthitgoods_products.json"]
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"FATAL: file not found: {path}")
            sys.exit(1)
        products = json.loads(path.read_text())
        result = validate_products(products, rejects_log=LOG_FILE)
        print(f"\n{path}")
        print(result["summary"])
        for rec, reasons in result["invalid"]:
            print(f"  REJECT: {rec.get('title','(no title)')}: {'; '.join(reasons)}")
        if result["invalid"]:
            print(f"Rejects logged to {LOG_FILE}")


if __name__ == "__main__":
    main()
