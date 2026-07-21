#!/usr/bin/env python3
"""
WorthItGoods — PAAPI Product Curation Pipeline
Finds hidden-gem products via Amazon Creators API and outputs a batch JSON.

Strategy:
  - Query by category with discovery-friendly keywords
  - Filter for high ratings (4.5+) and sufficient reviews (100+)
  - Exclude obvious/boring products (brand-name commodities, consumables)
  - Skip duplicates (same product type already on site)
  - **Ensure at least 1-2 "fun/interesting/unique" products per batch**
    - Dedicated FUN_QUERIES target novelty, clever design, conversation-starters
    - fun_score() measures novelty/uniqueness/cool-factor from title keywords
    - Phase 1: search fun queries, score candidates, reserve top picks
    - Phase 2: fill remaining slots from standard category queries
    - Every batch includes at least 1 fun product before filling with staples
    - Note: some products get their "fun" from visual design (e.g. novelty dish towels,
      witty mugs, creative prints) — the title alone won't always score high. The
      FUN_QUERIES search terms ("funny gift", "novelty", "conversation starter")
      are designed to catch these. The cron agent should also review the final
      batch visually and swap out anything too bland.
  - **Category rotation:** 9 categories total, 6 active per week. New batch gets
    a different mix via week-number-seeded shuffle. Automotive refined with
    enthusiast-focused queries. Pets, fitness/recovery, desk/gaming added.
  - **Rating pre-filter:** ALL products are checked for star rating and review count
    BEFORE being added to the final batch. Standard products need >= 4.5 stars
    and >= 100 reviews. Fun products get a slightly lower threshold (4.0 stars,
    50 reviews) to allow novelty items through.
  - Generate compelling descriptions and blurbs
  - Output ready for add_batch.sh

Usage:
  python3 curate_products.py [--count 2]
"""

import json
import os
import random
import sys
import re
import time
from pathlib import Path
from datetime import date

sys.path.insert(0, "/home/rock/.openclaw/workspace/chipradar")
from amazon_creators_api_v3 import AmazonCreatorsAPI

PARTNER_TAG = "worthitgoods-20"
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / f"curated_batch_{date.today():%Y-%m-%d}.json"

# Rating thresholds
MIN_STAR_RATING = 4.5
MIN_REVIEW_COUNT = 100
FUN_MIN_STAR_RATING = 4.0
FUN_MIN_REVIEW_COUNT = 50

CURATION_QUERIES = {
    "kitchen": [
        "unique kitchen gadget", "clever kitchen tool", "silicone kitchen accessory",
        "baking tool", "chef recommended kitchen",
        "kitchen organization", "food storage solution",
    ],
    "home": [
        "smart home gadget", "home organization", "desk organization",
        "phone stand", "cable management", "home office setup",
    ],
    "tools": [
        "home improvement tool", "DIY gadget", "multi tool",
        "tool organizer", "garage organization",
    ],
    "outdoor": [
        "camping essential", "outdoor gear", "hiking accessory",
        "backyard game", "travel gadget",
    ],
    "lifestyle": [
        "everyday carry", "EDC gear", "travel essential",
        "phone accessory", "desk organizer",
    ],
    "automotive": [
        "vehicle interior organizer premium", "car detailing tool professional",
        "truck accessory useful", "car tech gadget", "vehicle organization system",
        "auto interior upgrade", "car seat organizer", "garage storage solution",
    ],
    "pets": [
        "clever pet product", "innovative pet toy", "interactive pet feeder",
        "travel pet accessory", "pet grooming tool", "unique cat product",
        "puzzle toy dog", "pet travel essential", "dog enrichment toy",
    ],
    "fitness_recovery": [
        "muscle recovery tool", "posture corrector innovative",
        "massage gun compact", "balance trainer home", "resistance band system",
        "exercise gadget unique", "fitness accessory clever", "stretching device",
    ],
    "desk_gaming": [
        "ergonomic desk accessory unique", "cable management clever",
        "monitor arm premium", "gaming desk organizer", "standing desk accessory",
        "wrist rest ergonomic", "desk lamp innovative", "mouse pad large premium",
    ],
}

# ── Fun / Interesting / Unique Queries ────────────────────────────────────────
# These are novelty, clever design, and conversation-starter products.
# Every batch MUST include at least 1-2 products from these queries.
FUN_QUERIES = {
    "unique_gadgets": [
        "cool unique gadget", "clever invention", "ingenious gadget",
        "award winning gadget", "innovative product", "genius design",
        "smart invention", "reddot design award", "IF design award",
    ],
    "clever_kitchen": [
        "genius kitchen gadget", "clever kitchen invention",
        "unique kitchen tool", "chef secret weapon", "kitchen hack",
    ],
    "fun_tech": [
        "cool tech gadget", "unique tech accessory",
        "retro gadget", "nostalgia tech", "fun desk toy",
        "DIY electronics kit", "STEM kit",
    ],
    "quirky_home": [
        "unique home decor", "funny gift", "novelty gift",
        "conversation starter", "interesting home accessory",
        "creative wall art", "unique lamp",
    ],
    "interesting_edc": [
        "cool EDC", "unique every day carry", "interesting pocket tool",
        "titanium gadget", "innovative multi tool", "EDC gear unique",
    ],
    "outdoor_fun": [
        "camping gadget cool", "hiking innovation", "unique outdoor gear",
        "backyard fun game", "travel unique gadget", "portable hammock",
    ],
    "retro_nostalgia": [
        "retro gadget", "nostalgic tech", "vintage style modern",
        "throwback game classic", "classic design reimagined",
        "retro gaming accessory", "vintage inspired modern",
    ],
}

# ── Fun Score — rates products on novelty/interestingness/uniqueness ───────
FUN_KEYWORDS = [
    "innovative", "patented", "unique", "award", "genius", "clever", "ingenious",
    "unusual", "creative", "one-of-a-kind", "conversation", "novel", "original",
    "reusable", "multifunctional", "2-in-1", "3-in-1", "multi-functional",
    "titanium", "premium", "handmade", "artisan", "compact", "portable",
    "transforms", "converts", "folds", "collapsible", "solar", "rechargeable",
    "bamboo", "ceramic", "copper", "solid wood", "leather", "magnetic",
    "glass", "stainless", "retro", "vintage", "modern", "minimalist",
    "DIY", "kit", "build", "assemble", "custom", "modular", "adjustable",
    "universal", "compatible", "smart", "app", "bluetooth", "LED", "sensor",
    "award-winning", "as seen on", "shark tank", "dragon's den", "kickstarter",
    "indiegogo", "upgrade", "next generation", "version 2",
]


FUN_BORING_PATTERNS = [
    # These patterns make even a decent product feel boring
    r"basic", r"standard", r"ordinary", r"plain", r"simple", r"generic",
    r"replacement", r"refill", r"bulk", r"value pack", r"economy",
]


def fun_score(title: str, brand: str = "") -> float:
    """Rate a product's novelty/interestingness on a 0.0-1.0 scale.

    Factors:
    - Interesting/unique keywords in the title (positive signal)
    - Boring descriptors in the title (negative signal)
    - Presence of a patent, award, or design recognition
    - Product has a specific mechanism/feature that stands out
    - Brand helps (some brands are inherently interesting)
    """
    t = title.lower()
    score = 0.3  # baseline — most products are at least somewhat interesting

    # Positive signals
    for kw in FUN_KEYWORDS:
        if kw in t:
            score += 0.12

    # Negative signals
    for pat in FUN_BORING_PATTERNS:
        if re.search(pat, t):
            score -= 0.15

    # Boost for specific interesting patterns
    if re.search(r"\b(patent|award|design|invention|shark tank|dragon|kickstarter|indiegogo)\b", t, re.I):
        score += 0.25
    if re.search(r"\b(2-in-1|3-in-1|4-in-1|multi|universal|adjustable|folding|collapsible|rechargeable|solar)\b", t, re.I):
        score += 0.10
    if re.search(r"\b(titanium|bamboo|copper|solid wood|ceramic|leather|carbon fiber|marble)\b", t, re.I):
        score += 0.08
    if re.search(r"\b(kit|DIY|build|assemble|custom)\b", t, re.I):
        score += 0.08
    if re.search(r"\b(bluetooth|smart|app|sensor|LED|digital)\b", t, re.I):
        score += 0.06
    if re.search(r"\b(retro|vintage|nostalgia|classic|modern|minimalist|unique)\b", t, re.I):
        score += 0.06

    # Clamp
    return max(0.0, min(1.0, score))


EXCLUDE_TITLE_PATTERNS = [
    r"^Apple\s+",
    r"^Samsung\s+",
    r"^Sony\s+",
    r"^Amazon\s+(Echo|Fire|Kindle)",
    r"^Google\s+(Nest|Pixel|Home)",
    r"^Microsoft\s+(Surface|Xbox)",
    r"iPhone\s+\d+",
    r"AirPods",
    r"iPad",
    r"MacBook",
    r"iMac",
    r"Apple\s+Watch",
    r"^Nintendo\s+Switch",
    r"^PlayStation",
    r"Fitbit\s+",
    r"^Dyson\s+",
    r"^KitchenAid\s+(Stand\s+Mixer|Artisan)",
    r"Vitamin\s*ix\s+",
    r"Yeti\s+",
    r"Ninja\s+(Foodi|Professional|\d)",
    r"iRobot\s+",
]

BORING_KEYWORDS = [
    "batteries", "light bulb", "paper towel", "toilet paper",
    "trash bag", "cleaning supply", "laundry", "diaper",
    "baby wipe", "dog food", "cat food", "vitamin", "supplement",
    "ink cartridge", "toner", "filter replacement",
]

EXISTING_CACHE = None

def load_existing():
    global EXISTING_CACHE
    if EXISTING_CACHE is None:
        try:
            with open("data/sample_products.json") as f:
                EXISTING_CACHE = json.load(f)
        except:
            EXISTING_CACHE = []
    return EXISTING_CACHE

# Product type nouns — shared use of these indicates same product type
PRODUCT_NOUNS = {
    'rest', 'spoon', 'cup', 'bowl', 'knife', 'ladle', 'spatula', 'grater', 'zester',
    'shears', 'skillet', 'mold', 'scale', 'timer', 'board', 'rack', 'holder',
    'bag', 'pack', 'case', 'hat', 'shirt', 'pants', 'socks', 'gloves',
    'lamp', 'light', 'fan', 'charger', 'cable', 'stand', 'mount',
    'tool', 'pouch', 'organizer', 'mat', 'towel', 'kit', 'set', 'caddy',
    'scoop', 'shooter', 'launcher', 'disc', 'puzzle', 'game',
    'tumbler', 'mug', 'glass', 'bottle', 'jar', 'container',
    'blanket', 'pillow', 'plush', 'coaster', 'vase', 'journal',
    'brush', 'comb', 'mirror', 'tray', 'basket', 'bin',
    'screwdriver', 'socket', 'wrench', 'hammer', 'level',
    'camera', 'lens', 'tripod', 'speaker', 'adapter', 'hub', 'dock',
    'flag', 'banner', 'windsock', 'bunting',
    'paddleboard', 'hammock', 'cooler', 'lunchbox',
    'plug', 'registration', 'purifier', 'filter', 'trimmer', 'shaver',
    'sander', 'detector', 'monitor', 'tracker', 'alarm', 'lock',
    'straps', 'harness', 'leash', 'collar', 'bowl', 'feeder',
    'brush', 'clipper', 'dryer', 'heater', 'humidifier', 'diffuser',
    'projector', 'keyboard', 'mouse', 'tablet', 'laptop', 'monitor',
    'headphones', 'earbuds', 'microphone', 'webcam', 'router',
    'backpack', 'duffle', 'tote', 'sling', 'pouch', 'wallet',
    'stool', 'chair', 'desk', 'shelf', 'cabinet', 'drawer',
    'curtain', 'blind', 'rug', 'mat', 'cushion', 'throw',
}


def is_duplicate_by_content(title):
    """Detect if a product is essentially the same as something already on site.

    Logic:
    - 4+ meaningful common words (no overlap in product noun) -> duplicate
    - 2+ meaningful common words WITH a shared product noun -> duplicate
    - Otherwise allow (different product types from same brand are fine)
    """
    existing = load_existing()
    t = title.lower().strip()

    for p in existing:
        et = p.get("title", "").lower().strip()
        if not et:
            continue
        new_words = set(t.split())
        exist_words = set(et.split())
        common = new_words & exist_words

        stop_words = {"and", "the", "for", "with", "in", "of", "to", "a", "an", "is", "-", "|", ",", "."}
        meaningful = [w for w in common if len(w) > 3 and w not in stop_words]
        shared_nouns = set(meaningful) & PRODUCT_NOUNS

        # 4+ shared words without a shared noun = false positive risk (e.g. "stainless steel" matches)
        # Only flag if also sharing a product type
        if shared_nouns and len(meaningful) >= 2:
            return True
        if len(meaningful) >= 4:
            return True

    return False

def is_excluded(title, brand=""):
    t = title.lower()
    for pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, title):
            return True
    for kw in BORING_KEYWORDS:
        if kw in t:
            return True
    return False

# ── Category Rotation ──────────────────────────────────────────────────────────
# 9 total categories, 6 active per week. Seeded by ISO week number so each
# Monday batch gets a deterministic but different mix.
ALL_CATEGORIES = list(CURATION_QUERIES.keys())


def get_active_categories(active_count: int = 6):
    """Pick a rotating subset of categories using week number as seed."""
    week_num = date.today().isocalendar()[1]
    rng = random.Random(week_num)
    shuffled = ALL_CATEGORIES[:]
    rng.shuffle(shuffled)
    return shuffled[:active_count]


def curate_products(count_per_category=2):
    api = AmazonCreatorsAPI(partner_tag=PARTNER_TAG)
    curated = []
    all_candidates = []
    fun_candidates = []
    seen_asins = set()
    active_categories = get_active_categories(active_count=6)
    total_target = count_per_category * len(active_categories)

    print(f"\n{'='*60}")
    print(f"WorthItGoods — Product Curation Pipeline")
    print(f"Target: {total_target} products ({count_per_category} per category)")
    print(f"Active categories: {', '.join(active_categories)}")
    print(f"Fun requirement: at least 1 product per batch")
    print(f"Rating filter: >= {MIN_STAR_RATING} stars / >= {MIN_REVIEW_COUNT} reviews")
    print(f"Fun rating filter: >= {FUN_MIN_STAR_RATING} stars / >= {FUN_MIN_REVIEW_COUNT} reviews")
    print(f"{'='*60}\n")

    # ── Phase 1: Search fun/interesting queries first ──
    # These catch funny designs, clever inventions, conversation-starters
    # that the regular search queries miss.
    print(f"\n{'─'*60}")
    print("  PHASE 1: Fun / Interesting Product Search")
    print(f"{'─'*60}\n")

    for category, queries in FUN_QUERIES.items():
        hits = 0
        fun_target = 3  # gather plenty of candidates, we'll pick the best
        print(f"  [{category}]")

        for query in queries:
            if hits >= fun_target:
                break

            print(f"    '{query}'...", end=" ", flush=True)
            try:
                results = api.search_items(query, item_count=10)
            except Exception as e:
                print(f"error: {e}")
                continue

            if not results:
                print("no results")
                continue

            new_count = 0
            for r in results:
                if hits >= fun_target:
                    break

                asin = r.get("asin", "")
                if not asin or asin in seen_asins:
                    continue

                title = r.get("title", "") or ""
                brand = r.get("brand", "") or ""

                if is_excluded(title, brand):
                    continue
                if is_duplicate_by_content(title):
                    continue

                images = r.get("images", {})
                primary = images.get("primary", {}) if isinstance(images, dict) else {}
                large = primary.get("large", {}) if isinstance(primary, dict) else {}
                img = large.get("url", "") if isinstance(large, dict) else ""
                if not img:
                    continue

                score = fun_score(title, brand)

                product = {
                    "title": title,
                    "image": img,
                    "description": f"(edit me — write genuine why-it-is-worth-it description)",
                    "blurb": f"(edit me — one-line hook)",
                    "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                    "asin": asin,
                    "_fun_score": round(score, 2),
                }
                
                fun_candidates.append(product)
                seen_asins.add(asin)
                hits += 1
                new_count += 1
                print(f"\n      + [fun={score:.2f}] {title[:60]}")

            if new_count == 0:
                print("(no new)")
            else:
                print(f"      +{new_count}")

            time.sleep(0.3)

        print(f"    total fun candidates: {hits}")

    # Sort fun candidates by score descending
    fun_candidates.sort(key=lambda p: p["_fun_score"], reverse=True)
    
    print(f"\n  Phase 1 complete: {len(fun_candidates)} fun candidates")

    # ── Phase 2: Fill slots from standard queries ──
    # We need enough standard candidates since fun products are capped at 2 max.
    # Fun candidates already found: {len(fun_candidates)}
    standard_needed = total_target + 4  # collect extra for rating filter pass-through
    print(f"\n{'─'*60}")
    print(f"  PHASE 2: Standard Product Search (looking for ~{standard_needed} candidates)")
    print(f"{'─'*60}\n")

    for category in active_categories:
        queries = CURATION_QUERIES[category]
        if len(all_candidates) >= total_target + 4:
            break
        hits = 0
        print(f"\n--- {category.upper()} ---")
        
        for query in queries:
            if hits >= count_per_category or len(all_candidates) >= total_target + 4:
                break

            print(f"  '{query}'...", end=" ", flush=True)
            try:
                results = api.search_items(query, item_count=10)
            except Exception as e:
                print(f"error: {e}")
                continue

            if not results:
                print("no results")
                continue

            new_count = 0
            for r in results:
                if hits >= count_per_category or len(all_candidates) >= total_target:
                    break

                asin = r.get("asin", "")
                if not asin or asin in seen_asins:
                    continue

                title = r.get("title", "") or ""
                brand = r.get("brand", "") or ""

                if is_excluded(title, brand):
                    continue
                if is_duplicate_by_content(title):
                    continue

                images = r.get("images", {})
                primary = images.get("primary", {}) if isinstance(images, dict) else {}
                large = primary.get("large", {}) if isinstance(primary, dict) else {}
                img = large.get("url", "") if isinstance(large, dict) else ""
                if not img:
                    continue

                score = fun_score(title, brand)

                product = {
                    "title": title,
                    "image": img,
                    "description": f"(edit me — write genuine why-it-is-worth-it description)",
                    "blurb": f"(edit me — one-line hook)",
                    "affiliate_url": f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                    "asin": asin,
                }

                all_candidates.append(product)  # standard candidates only
                seen_asins.add(asin)
                hits += 1
                new_count += 1
                fun_indicator = f" [fun={score:.2f}]" if score >= 0.5 else ""
                print(f"\n    + {title[:60]}{fun_indicator}")

            if new_count == 0:
                print("(no new)")
            else:
                print(f"    +{new_count}")

            time.sleep(0.3)

        print(f"  total: {hits}")

    print(f"\n  Phase 2 complete: {len(all_candidates)} total candidates")

    # ── Phase 3: RATING PRE-FILTER ──
    # Check every candidate's star rating and review count BEFORE adding to final batch.
    # Only include products that meet the quality threshold.
    print(f"\n{'─'*60}")
    print(f"  PHASE 3: Rating Filter")
    print(f"  Standard: >= {MIN_STAR_RATING} stars / >= {MIN_REVIEW_COUNT} reviews")
    print(f"  Fun:      >= {FUN_MIN_STAR_RATING} stars / >= {FUN_MIN_REVIEW_COUNT} reviews")
    print(f"{'─'*60}")

    # Collect all candidate ASINs that need rating checks
    rating_targets = [p for p in fun_candidates if p.get("asin")] + [p for p in all_candidates if p.get("asin")]
    rating_asins = [p["asin"] for p in rating_targets]

    if rating_asins:
        rating_fetcher = os.path.join(os.path.dirname(__file__), 'scripts', 'fetch_rating.py')

        # Step 3a: Try PAAPI first for all candidates
        print(f"  Checking {len(rating_asins)} ASINs via PAAPI...")
        try:
            enriched_data = api.get_items(rating_asins)
            if isinstance(enriched_data, dict):
                for p in rating_targets:
                    asin = p["asin"]
                    ed = enriched_data.get(asin, {})
                    if ed and "error" not in ed:
                        reviews = ed.get("customer_reviews", {}) or {}
                        if reviews.get("star_rating"):
                            p["rating"] = reviews["star_rating"]
                        if reviews.get("count"):
                            p["reviews_count"] = reviews["count"]
        except Exception as e:
            print(f"    PAAPI batch check failed: {e}")

        # Step 3b: Scrape remaining via fetch_rating.py (curl-based)
        need_scrape = [p for p in rating_targets if not p.get("rating") or not p.get("reviews_count")]
        if need_scrape and os.path.exists(rating_fetcher):
            scrape_asins = [p["asin"] for p in need_scrape]
            print(f"  Scraping ratings for {len(scrape_asins)} products (curl)...")
            import subprocess, json as json_mod
            result = subprocess.run(
                [sys.executable, rating_fetcher, '--batch'] + scrape_asins,
                capture_output=True, text=True, timeout=300
            )
            if result.stdout.strip():
                try:
                    ratings = json_mod.loads(result.stdout.strip())
                    for r in ratings:
                        asin = r.get("asin")
                        if r.get("star_rating") and r.get("review_count"):
                            for p in need_scrape:
                                if p.get("asin") == asin:
                                    p["rating"] = r["star_rating"]
                                    p["reviews_count"] = r["review_count"]
                                    break
                except json_mod.JSONDecodeError:
                    pass
            if result.stderr:
                print(f"    stderr: {result.stderr[:200]}")

        # Step 3c: Filter candidates by rating threshold
        # Fun candidates (has _fun_score) get a slightly lower threshold
        # to allow novelty/interesting items through
        fun_passing = []
        standard_passing = []

        for p in rating_targets:
            rating = p.get("rating") or 0
            reviews = p.get("reviews_count") or 0

            if p.get("_fun_score") is not None:
                # Fun product threshold
                if rating >= FUN_MIN_STAR_RATING and reviews >= FUN_MIN_REVIEW_COUNT:
                    fun_passing.append(p)
                    print(f"    FUN PASS: {rating} stars / {reviews} reviews | {p['title'][:60]}")
                else:
                    print(f"    FUN FAIL: {rating} stars / {reviews} reviews | {p['title'][:50]}")
            else:
                # Standard product threshold
                if rating >= MIN_STAR_RATING and reviews >= MIN_REVIEW_COUNT:
                    standard_passing.append(p)
                    print(f"    PASS: {rating} stars / {reviews} reviews | {p['title'][:60]}")
                else:
                    print(f"    FAIL: {rating} stars / {reviews} reviews | {p['title'][:50]}")

        # Ensure at least 1 fun product in batch
        # If none passed the threshold, force the highest-scoring fun candidate
        if not fun_passing and fun_candidates:
            best_fun = fun_candidates[0]
            asin = best_fun.get("asin")
            match = next((p for p in rating_targets if p.get("asin") == asin), None)
            if match:
                fun_passing.append(match)
                print(f"\n  Forcing fun product (score={best_fun.get('_fun_score', 0):.2f}) into batch even though below rating threshold")

        # Build final curated list: fun products first, then standard
        fun_slots = min(2, len(fun_passing))
        standard_slots = total_target - fun_slots

        # Deduplicate: ensure we don't add the same ASIN from both lists
        curated_asins = set()
        curated = []

        # Add fun products first
        for p in fun_passing[:fun_slots]:
            curated.append({
                "title": p["title"],
                "image": p["image"],
                "description": p["description"],
                "blurb": p["blurb"],
                "affiliate_url": p["affiliate_url"],
                "asin": p["asin"],
            })
            curated_asins.add(p["asin"])

        # Add standard products (skip any ASIN already added as fun)
        for p in standard_passing:
            if len(curated) >= total_target:
                break
            if p.get("asin") not in curated_asins:
                curated.append({
                    "title": p["title"],
                    "image": p["image"],
                    "description": p["description"],
                    "blurb": p["blurb"],
                    "affiliate_url": p["affiliate_url"],
                    "asin": p["asin"],
                })
                curated_asins.add(p["asin"])

        print(f"\n  After rating filter: {len(curated)}/{total_target} products")
    else:
        print("  No ASINs to rate-check")

    # ── Enrichment: PAAPI extras (price, features, sales rank) ──
    if curated:
        print(f"\n{'─'*60}")
        print(f"  FINAL ENRICHMENT: PAAPI extras for {len(curated)} products")
        print(f"{'─'*60}")

        enrich_asins = [p["asin"] for p in curated]
        for asin in enrich_asins:
            try:
                ed = api.get_item(asin)
                if ed and "error" not in ed:
                    if ed.get("price"):
                        for p in curated:
                            if p.get("asin") == asin:
                                p["price"] = ed["price"]
                                break
            except Exception as e:
                print(f"  Enrichment failed for {asin}: {e}")
                time.sleep(0.2)

        # Clean up internal ASIN field
        for p in curated:
            p.pop("asin", None)
        print(f"  Enrichment complete")

    print(f"\n  Final batch: {len(curated)} products (target was {total_target})")

    if len(curated) == 0:
        print("  No products passed rating filter! Check fetch_rating.py or reduce thresholds.")

    return curated


def save(products):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(products, f, indent=2)
    print(f"\n{'='*60}")
    print(f"Saved {len(products)} products to {OUTPUT_FILE}")
    print(f"IMPORTANT: Edit descriptions before merging!")
    print(f"Then: ./add_batch.sh {OUTPUT_FILE}")
    print(f"{'='*60}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=2)
    args = parser.parse_args()
    products = curate_products(count_per_category=args.count)
    if products:
        save(products)
        return 0
    else:
        print("No products found.")
        return 1


if __name__ == "__main__":
    sys.exit(main())