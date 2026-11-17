#!/usr/bin/env python3
"""Shared WorthItGoods taste policy (2026-11-17, v2 — after the owner flagged
tongue-shape phone / CR2032 batteries / label refills / iPhone gift-case /
off-theme digital frame shipping in a Thanksgiving batch).

Three layers, used by BOTH weekly (curate_products.py) and seasonal
(curate_seasonal.py) pipelines plus the catalog retro-sweep:

  1. HARD_RESTOCK regex block — consumables, restocks, replacement parts, and
     generic device accessories (cases/screen protectors) are banned outright.

  2. LLM browse-appeal review (OpenRouter flash, cheap model per swarm policy):
     s = 1-10 "would a visitor stop, browse, gift this?"

  3. Optional THEME-FIT review (t = 1-10): when a batch/catalog section belongs
     to a seasonal collection, an item can score well on browse and still be
     WRONG for the shelf (digital frame in a Thanksgiving hosting set).

Pipelines: fun_gate() drops s<5, and with theme context also drops t<5 (an
off-theme product should not enter a themed batch at all).
Retro-sweep: sweep() DELETES products failing browse (s<5) but merely UNTAGS
(theme-stripped, kept in evergreen catalog) products that fail only fit (t<5).

Network failures never block a deploy: hard-block always applies; if the LLM
fails twice the batch proceeds with a warning.
"""
import json
import os
import re
import sys
from pathlib import Path

GATE_LOG = Path("logs/fun_gate_rejects.log")

HARD_RESTOCK = [re.compile(p, re.I) for p in (
    # batteries-as-the-PRODUCT only (cell codes near the word) — not power banks,
    # speakers or lights that merely mention a built-in battery
    r"\b(AA|AAA|CR\d{3,4}|18650|9V|button ?cell)\b.{0,40}\bbatter(y|ies)\b",
    r"\bbatter(y|ies)\b.{0,40}\b(AA|AAA|CR\d{3,4}|18650|button ?cell|alkaline|lithium ?ion)\b",
    # refills-as-the-PRODUCT only — not pens/styluses that use a refill
    r"\b(tape|label|printer|ink|toner|filter|water|lighter|cartridge|soap) refills?\b",
    r"\brefills?\b\s*(pack|compatible|replacement)",
    r"\breplacement (filters?|blades?|pads?|cartridges?|heads?|rolls?)\b",
    r"\btoner\b",
    r"\bink cartridges?\b",
    r"\blight ?bulbs?\b",
    r"\bscreen ?protectors?\b",
    # cases/covers FOR a device (adjacent phrasing) — not random titles containing both words
    r"\b(case|cover)\b.{0,20}\b(iphone|ipad|airpods?|galaxy|samsung|pixel|kindle)\b",
    r"\b(laundry|dish) (pods|sheets)\b",
    r"\bvacuum bags\b",
    r"\b(coffee pods|k-cups)\b",
    r"\bpet pads?\b",
    r"\bdisposable (bags|gloves)\b",
    r"\b(trash bags?|paper towels?|toilet paper)\b",
)]

_MIN_SCORE = 5
_MODEL = os.environ.get("WIG_TASTE_MODEL", "qwen/qwen3.8-flash")

_PROMPT = """You are the taste gate for WorthItGoods.com, a curated shop of interesting, gift-worthy finds. Score each product's browse-and-gift appeal 1-10.

Rubric (follow exactly):
- Consumable / restock / refill / replacement part (batteries, tape refills, filters) = 1-2
- Shock-value gag that isn't genuinely fun to own (tongue-shape telephone, vomit-shaped gadget) = 2-3. WEIRD IS NOT INTERESTING.
- Boring utility commodity or generic phone accessory (plain organizer, plain tape, case, protector) = 3-4
- Useful with a clever angle or good design (motion-activated light, gooseneck mount, vacuum food container) = 5-7
- Genuine hidden gem / conversation starter / premium gift = 8-10

Quality is already gated elsewhere (ratings/reviews) — judge ONLY browse-and-gift appeal.
"""

_THEME_BLOCK = """THEME CONTEXT: this set belongs to "{theme}".
Also score theme-fit t: 1-10 (10 = perfect fit for this occasion's shelf; roasting pan in Thanksgiving hosting = 9-10; digital photo frame in Thanksgiving hosting = 3-4 (fine gift, WRONG shelf); phone accessory = 1-2). An item that is generally interesting but off-theme still gets low t.
Return ONLY a JSON array: [{{"i": <index>, "s": <1-10>, "t": <1-10>, "w": "<max 8 words>"}}]
"""

_PLAIN_BLOCK = """Return ONLY a JSON array: [{"i": <index>, "s": <1-10>, "t": null, "w": "<max 8 words>"}]
"""


def _log_drop(p, why, how):
    try:
        import datetime
        GATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "t": str(datetime.date.today()),
            "how": how,
            "title": str(p.get("title", "?"))[:80],
            "price": p.get("price"),
            "theme": p.get("theme"),
            "why": why,
        }
        with open(GATE_LOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _hard_pass(products):
    kept = []
    for p in products:
        title = str(p.get("title", ""))
        hit = next((r.pattern for r in HARD_RESTOCK if r.search(title)), None)
        if hit:
            _log_drop(p, f"hard-block: /{hit}/", "hard")
            print(f"    HARD-BLOCK: {title[:60]}")
        else:
            kept.append(p)
    return kept


def _review(products, theme=None):
    """LLM review -> {index: (browse_s, fit_t, why)} or None on failure."""
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("LLM_API_KEY") or ""
    if not key or not products:
        print("  fun-gate: no API key — LLM taste pass skipped (hard-block only)")
        return None
    import urllib.request
    rubric = _PROMPT + (_THEME_BLOCK.format(theme=theme) if theme else _PLAIN_BLOCK)
    lines = []
    for i, p in enumerate(products):
        blurb = str(p.get("blurb") or "")[:70]
        lines.append(f"{i}: {str(p.get('title',''))[:90]} | ${p.get('price','?')} | {blurb}")
    base = {
        "messages": [{"role": "user", "content": rubric + "\n".join(lines)}],
        "temperature": 0,
        "max_tokens": min(120 * len(products), 6000),
        # flash models here are reasoning-by-default; hidden tokens ate the budget
        # and left content empty (finish_reason=length). Explicitly disable thinking.
        "reasoning": {"effort": "none"},
    }
    models = [_MODEL]
    if _MODEL != "deepseek/deepseek-v4.1-flash":
        models.append("deepseek/deepseek-v4.1-flash")
    for model in models:
      try:
        body2 = json.dumps(dict(base, model=model)).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", data=body2, method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        choice = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]
        txt = ((choice.get("message") or {}).get("content") or "").strip()
        if not isinstance(txt, str) or not txt:
            print(f"  fun-gate: model {model} returned empty content ({choice.get('finish_reason')}) — trying next")
            continue
        m = re.search(r"\[.*\]", txt, re.S)
        out = {}
        for row in json.loads(m.group(0)):
            if not isinstance(row.get("i"), int):
                continue
            s = row.get("s")
            tv = row.get("t")
            out[row["i"]] = (
                float(s) if isinstance(s, (int, float)) else _MIN_SCORE,
                float(tv) if isinstance(tv, (int, float)) else None,
                str(row.get("w", ""))[:60],
            )
        if len(out) >= len(products) * 0.7:
            return out
        print(f"  fun-gate {model}: parsed only {len(out)}/{len(products)}, trying next")
      except Exception as e:
        print(f"  fun-gate {model} failed: {e}")
    return None


def fun_gate(products, min_score=_MIN_SCORE, theme=None):
    """Pipeline filter: keep only products clearing browse (and fit, when theme
    context given). Returns kept list; never empty-blocks on LLM outage."""
    if not products:
        return products
    products = _hard_pass(products)
    if not products:
        print("  fun-gate: all products hard-blocked")
        return products
    scores = _review(products, theme=theme)
    if scores is None:
        print("  fun-gate WARNING: LLM unavailable — batch proceeds on hard-block only")
        return products
    kept, dropped = [], 0
    for i, p in enumerate(products):
        s, t, why = scores.get(i, (min_score, min_score, "unscored->keep"))
        if s < min_score or (theme and t is not None and t < min_score):
            dropped += 1
            _log_drop(p, f"browse {s}/10 fit {t}/10: {why}", "llm")
            print(f"    TASTE-DROP (s={s} t={t} {why}): {str(p.get('title',''))[:52]}")
        else:
            kept.append(p)
    print(f"  fun-gate: kept {len(kept)}, taste-dropped {dropped}")
    return kept


def sweep(products, min_score=_MIN_SCORE, chunk=40):
    """Full-catalog audit. Returns (keep, untag, drop) lists.
    Items failing theme-fit only are kept but stripped of their theme tag
    (they return to the evergreen catalog instead of the seasonal shelf)."""
    survivors = _hard_pass(products)
    drop = [p for p in products if p not in survivors]
    by_theme = {}
    for p in survivors:
        by_theme.setdefault(p.get("theme"), []).append(p)
    keep, untag = [], []
    for theme, items in by_theme.items():
        ctx = None
        if theme:
            ctx = f"{theme.replace('_',' ').title()} seasonal collection"
        for i in range(0, len(items), chunk):
            part = items[i:i + chunk]
            scores = _review(part, theme=ctx)
            if scores is None:
                keep += part  # LLM down: keep (hard-block already applied)
                continue
            for j, p in enumerate(part):
                s, t, why = scores.get(j, (min_score, min_score, "unscored->keep"))
                if s < min_score:
                    _log_drop(p, f"sweep browse {s}/10: {why}", "sweep")
                    drop.append(p)
                elif t is not None and t < min_score:
                    _log_drop(p, f"sweep fit {t}/10 (browse {s}): {why}", "untag")
                    q = dict(p)
                    q.pop("theme", None)
                    untag.append(q)
                else:
                    keep.append(p)
    return keep, untag, drop


if __name__ == "__main__":
    tests = {
        "[2-PACK] CR2032 Digital Meat Thermometer Battery Compatible with Kizen": True,
        "Label Maker Tape Refills, 3 Rolls": True,
        "Decant It Properly Wine Decanter Lover Gift Case for iPhone 15": True,
        "CHULEAG Charging Case Cover for Apple Airpods Pro 3": True,
        "TACRAY Mini Titanium Stylus Pen with Bolt-Action Mechanism, Smooth Writing with Lamy Refill": False,
        "INIU 45W Fast Charging Portable Charger, External Phone Battery Pack for Business": False,
        "JBL Go 4 Bluetooth Speaker, 7-Hour Built-in Battery": False,
        "Bright Basics Motion Activated LED Light, Battery Powered": False,
        "NOCO GENIUS5 Smart Battery Charger": False,
        "Fisher Space Pen Bullet Pen": False,
        "32GB FRAMEO 10.1 Inch WiFi Digital Picture Frame": False,
    }
    bad = 0
    for title, want_block in tests.items():
        blocked = any(r.search(title) for r in HARD_RESTOCK)
        if blocked != want_block:
            print(f"SELFTEST FAIL: {title} -> blocked={blocked} want={want_block}")
            bad += 1
    print("hard-pass self-test:", "OK" if not bad else f"{bad} FAILURES")
    sys.exit(1 if bad else 0)
