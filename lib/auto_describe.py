#!/usr/bin/env python3
"""
Auto-generate blurbs and descriptions for curated batch products using LLM.
Called as part of the curation pipeline — no separate agent step needed.

Usage:
    python3 lib/auto_describe.py <batch_file>
    python3 lib/auto_describe.py data/curated_batch_2026-08-17.json
"""

import json, os, sys, re, urllib.request, urllib.error, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Load .env if present (no dependency on python-dotenv)
_env_path = BASE / '.env'
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line.startswith('export '):
            _line = _line[7:]
        if '=' in _line and not _line.startswith('#') and _line.strip():
            _k, _v = _line.split('=', 1)
            _v = _v.strip('"').strip("'")
            os.environ.setdefault(_k.strip(), _v)

LLM_API_KEY = os.environ.get("OPENROUTER_API_KEY", os.environ.get("LLM_API_KEY", ""))
LLM_MODEL = "deepseek/deepseek-v4-flash"

def call_llm(prompt, max_tokens=300, temperature=0.7):
    """Call DeepSeek V4 Flash via OpenRouter."""
    data = json.dumps({
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  LLM call failed: {e}", file=sys.stderr)
        return None


def generate_blurb(title, price, category_hint):
    """Generate a one-line hook for a product."""
    price_str = f"${price}" if price else "under $30"
    prompt = f"""Generate ONE punchy one-sentence hook for this product. Honest, benefit-focused, no hype. No 'in today's world' or 'game-changing'. Natural voice. Max 20 words.

Product: {title}
Price: {price_str}
Category: {category_hint}
"""
    result = call_llm(prompt, max_tokens=80, temperature=0.6)
    if result:
        # Strip quotes if present
        result = result.strip('"').strip("'")
    return result


def generate_description(title, price, category_hint):
    """Generate a 2-3 sentence why-it's-worth-it description."""
    price_str = f"${price}" if price else "a great price"
    prompt = f"""Write 2-3 sentences explaining why this product is worth buying. Honest, practical, no fluff. First-person voice is fine (we, you). Mention what problem it solves and who it's for. Max 60 words.

Product: {title}
Price: {price_str}
Category: {category_hint}

Format: plain text, no markdown, no leading prefix.
"""
    result = call_llm(prompt, max_tokens=150, temperature=0.6)
    if result:
        result = result.strip('"').strip("'")
        # Remove common prefixes
        for prefix in ["Here's why", "Why it's worth it:", "Why it's worth it"]:
            if result.startswith(prefix):
                result = result[len(prefix):].strip()
    return result


def category_hint_from_title(title):
    """Guess category from product title."""
    t = title.lower()
    if any(kw in t for kw in ['kitchen', 'cook', 'bake', 'food', 'knife', 'spoon', 'pan', 'pot', 'strainer', 'whisk']):
        return 'Kitchen'
    if any(kw in t for kw in ['synthesizer', 'musical', 'instrument', 'stylophone', 'keyboard']):
        return 'Music/Gadget'
    if any(kw in t for kw in ['wipes', 'broom', 'cleaning', 'command']):
        return 'Home/Household'
    if any(kw in t for kw in ['backpack', 'bag', 'north face', 'jester', 'laptop']):
        return 'Outdoor/Bags'
    if any(kw in t for kw in ['tool', 'drill', 'screwdriver', 'klein', 'gfci', 'tester']):
        return 'Tools/DIY'
    if any(kw in t for kw in ['mouse pad', 'mousepad', 'wrist rest', 'keyboard wrist']):
        return 'Office/Desk'
    if any(kw in t for kw in ['visor', 'car', 'automotive']):
        return 'Automotive'
    if any(kw in t for kw in ['cleaver', 'cutting', 'cuisinart']):
        return 'Kitchen'
    return 'General'


def process_batch(batch_file):
    """Process a batch file, generating descriptions for placeholder entries."""
    with open(batch_file) as f:
        products = json.load(f)

    # Find products needing descriptions
    need_blurb = [p for p in products if not p.get('blurb') or 'edit me' in (p.get('blurb', '') or '').lower()]
    need_desc = [p for p in products if not p.get('description') or 'edit me' in (p.get('description', '') or '').lower()]

    if not need_blurb and not need_desc:
        print(f"✅ All {len(products)} products already have descriptions.")
        return True

    print(f"Need blurbs: {len(need_blurb)}, need descriptions: {len(need_desc)}")
    
    for i, p in enumerate(products):
        title = p.get('title', '')
        price = p.get('price')
        hint = category_hint_from_title(title)
        
        needs_blurb = not p.get('blurb') or 'edit me' in (p.get('blurb', '') or '').lower()
        needs_desc = not p.get('description') or 'edit me' in (p.get('description', '') or '').lower()
        
        if not needs_blurb and not needs_desc:
            continue

        print(f"  [{i+1}/{len(products)}] {title[:50]}...", end='', flush=True)
        
        if needs_blurb:
            blurb = generate_blurb(title, price, hint)
            if blurb:
                p['blurb'] = blurb
                print(f" blurb ✓", end='', flush=True)
            else:
                print(f" blurb ✗", end='', flush=True)
            time.sleep(0.5)
        
        if needs_desc:
            desc = generate_description(title, price, hint)
            if desc:
                p['description'] = desc
                print(f" desc ✓", end='', flush=True)
            else:
                print(f" desc ✗", end='', flush=True)
            time.sleep(0.5)
        
        print()

    # Save
    with open(batch_file, 'w') as f:
        json.dump(products, f, indent=2)
    
    desc_count = sum(1 for p in products if p.get('description') and 'edit me' not in (p.get('description', '') or '').lower())
    blurb_count = sum(1 for p in products if p.get('blurb') and 'edit me' not in (p.get('blurb', '') or '').lower())
    print(f"\n✅ Saved: {len(products)} products ({desc_count} with descs, {blurb_count} with blurbs)")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lib/auto_describe.py <batch_file>")
        sys.exit(1)

    batch_file = sys.argv[1]
    if not os.path.exists(batch_file):
        print(f"FATAL: Batch file not found: {batch_file}")
        sys.exit(1)

    print(f"Auto-describe: {batch_file}")
    success = process_batch(batch_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
