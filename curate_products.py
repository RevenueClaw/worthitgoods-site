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
    - Phase 1: search fun queries (ALL 3 tiers run every time), score candidates, reserve top picks
    - Phase 2: fill remaining slots from standard category queries
    - Every batch includes at least 1 fun product before filling with staples
  - **Rating pre-filter:** ALL products checked for star rating BEFORE final batch
  - Output ready for add_batch.sh

Usage:
  python3 curate_products.py [--count 2]
"""

import json, os, random, sys, re, time
from pathlib import Path
from datetime import date

sys.path.insert(0, "/home/rock/.openclaw/workspace/chipradar")
from amazon_creators_api_v3 import AmazonCreatorsAPI

PARTNER_TAG = "worthitgoods-20"
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / f"curated_batch_{date.today():%Y-%m-%d}.json"

MIN_STAR_RATING = 4.5
MIN_REVIEW_COUNT = 100
FUN_MIN_STAR_RATING = 4.3
FUN_MIN_REVIEW_COUNT = 100

CURATION_QUERIES = {
    "kitchen": ["unique kitchen gadget","clever kitchen tool","silicone kitchen accessory","baking tool","chef recommended kitchen","kitchen organization","food storage solution"],
    "home": ["smart home gadget","home organization","desk organization","phone stand","cable management","home office setup"],
    "tools": ["home improvement tool","DIY gadget","multi tool","tool organizer","garage organization"],
    "outdoor": ["camping essential","outdoor gear","hiking accessory","backyard game","travel gadget"],
    "lifestyle": ["everyday carry","EDC gear","travel essential","phone accessory","desk organizer"],
    "automotive": ["vehicle interior organizer premium","car detailing tool professional","truck accessory useful","car tech gadget","vehicle organization system","auto interior upgrade","car seat organizer","garage storage solution"],
    "pets": ["clever pet product","innovative pet toy","interactive pet feeder","travel pet accessory","pet grooming tool","unique cat product","puzzle toy dog","pet travel essential","dog enrichment toy"],
    "fitness_recovery": ["muscle recovery tool","posture corrector innovative","massage gun compact","balance trainer home","resistance band system","exercise gadget unique","fitness accessory clever","stretching device"],
    "desk_gaming": ["ergonomic desk accessory unique","cable management clever","monitor arm premium","gaming desk organizer","standing desk accessory","wrist rest ergonomic","desk lamp innovative","mouse pad large premium"],
}

FUN_QUERIES = {
    "unique_gadgets": ["cool unique gadget","clever invention","ingenious gadget","award winning gadget","innovative product","genius design","smart invention","reddot design award","IF design award"],
    "clever_kitchen": ["genius kitchen gadget","clever kitchen invention","unique kitchen tool","chef secret weapon","kitchen must have"],
    "fun_tech": ["cool tech gadget","unique tech accessory","AI gadget","AI accessory","smart home fun","retro premium gadget","nostalgia tech","fun desk toy","DIY electronics kit","STEM kit"],
    "quirky_home": ["unique home decor","conversation piece home","unique decorative gift","interesting home accessory","creative wall art","unique lamp"],
    "interesting_edc": ["cool EDC","unique every day carry","premium EDC","interesting pocket tool","titanium gadget","innovative multi tool","EDC gear unique"],
    "outdoor_fun": ["camping gadget cool","hiking innovation","unique outdoor gear","backyard fun game","travel unique gadget","portable hammock"],
    "retro_nostalgia": ["retro gadget","retro premium gadget","nostalgic tech","vintage style modern","throwback game classic","classic design reimagined","retro gaming accessory","premium retro gaming","vintage inspired modern"],
}

FUN_KEYWORDS = ["innovative","patented","unique","award","genius","clever","ingenious","unusual","creative","one-of-a-kind","conversation","novel","original","reusable","multifunctional","2-in-1","3-in-1","multi-functional","titanium","premium","handmade","artisan","compact","portable","transforms","converts","folds","collapsible","solar","rechargeable","bamboo","ceramic","copper","solid wood","leather","magnetic","glass","stainless","retro","vintage","modern","minimalist","DIY","kit","build","assemble","custom","modular","adjustable","universal","compatible","smart","app","bluetooth","LED","sensor","award-winning","as seen on","shark tank","dragon's den","kickstarter","indiegogo","upgrade","next generation","version 2"]

# Additional fun query tiers for retry — broader angles to find fun products
# when the primary queries don't yield anything that passes the rating threshold
FUN_QUERIES_TIER_2 = {
    "gifts_more": ["unique gift under 50","cool gadget gift","impressive present","gift for gadget lover","birthday gift unique"],
    "popular_trending": ["trending gadget","viral amazon product","popular cool find","tiktok gadget","instagram worthy home"],
    "useful_problems": ["actually useful gadget","problem solving tool","life hack product","everyday problem solved","smart solution home"],
    "interesting_tech": ["bluetooth gadget cool","smart home unique","LED creative product","tech accessory fun","desk gadget useful"],
}

FUN_QUERIES_TIER_3 = {
    "top_rated_fun": ["highly rated unique","amazon choice gadget","editor pick fun","4.5 star unique","top rated cool"],
    "creative_design": ["creative design product","award winning design","ergonomic innovative","space saving clever","minimalist design cool"],
    "hobby_fun": ["DIY kit cool","STEM toy adult","board game unique","hobby gift interesting","makers tool"],
    "kitchen_odd": ["innovative kitchen tool","highly rated kitchen gadget","kitchen tool unusual","cooking innovation","oddly satisfying kitchen"],
}

FUN_BORING_PATTERNS = [r"basic",r"standard",r"ordinary",r"plain",r"simple",r"generic",r"replacement",r"refill",r"bulk",r"value pack",r"economy"]

def fun_score(title, brand=""):
    t = title.lower()
    score = 0.3
    for kw in FUN_KEYWORDS:
        if kw in t: score += 0.12
    for pat in FUN_BORING_PATTERNS:
        if re.search(pat, t): score -= 0.15
    if re.search(r"\b(patent|award|design|invention|shark tank|dragon|kickstarter|indiegogo)\b", t, re.I): score += 0.25
    if re.search(r"\b(2-in-1|3-in-1|4-in-1|multi|universal|adjustable|folding|collapsible|rechargeable|solar)\b", t, re.I): score += 0.10
    if re.search(r"\b(titanium|bamboo|copper|solid wood|ceramic|leather|carbon fiber|marble)\b", t, re.I): score += 0.08
    if re.search(r"\b(kit|DIY|build|assemble|custom)\b", t, re.I): score += 0.08
    if re.search(r"\b(bluetooth|smart|app|sensor|LED|digital)\b", t, re.I): score += 0.06
    if re.search(r"\b(retro|vintage|nostalgia|classic|modern|minimalist|unique)\b", t, re.I): score += 0.06
    return max(0.0, min(1.0, score))

EXCLUDE_TITLE_PATTERNS = [r"^Apple\s+",r"^Samsung\s+",r"^Sony\s+",r"^Amazon\s+(Echo|Fire|Kindle|Smart)",r"^Google\s+(Nest|Pixel|Home)",r"^Microsoft\s+(Surface|Xbox)",r"iPhone\s+\d+",r"AirPods",r"iPad",r"MacBook",r"iMac",r"Apple\s+Watch",r"^Nintendo\s+Switch",r"^PlayStation",r"Fitbit\s+",r"^Dyson\s+",r"^KitchenAid\s+(Stand\s+Mixer|Artisan)",r"Vitamin\s*ix\s+",r"Yeti\s+",r"Ninja\s+(Foodi|Professional|\d)",r"iRobot\s+"]
BORING_KEYWORDS = ["batteries","light bulb","paper towel","toilet paper","trash bag","cleaning supply","laundry","diaper","baby wipe","dog food","cat food","vitamin","supplement","ink cartridge","toner","filter replacement"]

EXISTING_CACHE = None
def load_existing():
    global EXISTING_CACHE
    if EXISTING_CACHE is None:
        try:
            with open("data/sample_products.json") as f: EXISTING_CACHE = json.load(f)
        except: EXISTING_CACHE = []
    return EXISTING_CACHE

import string as _string

def _clean_tokens(title):
    """Split title into lowercase tokens with punctuation stripped."""
    t = title.lower().strip()
    for ch in _string.punctuation:
        t = t.replace(ch, ' ')
    return [w for w in t.split() if w]

PRODUCT_NOUNS = {'rest','spoon','cup','bowl','knife','ladle','spatula','grater','zester','shears','skillet','mold','scale','timer','board','rack','holder','bag','pack','case','hat','shirt','pants','socks','gloves','lamp','light','fan','charger','cable','stand','mount','tool','pouch','organizer','mat','towel','kit','set','caddy','scoop','shooter','launcher','disc','puzzle','game','tumbler','mug','glass','bottle','jar','container','blanket','pillow','plush','coaster','vase','journal','brush','comb','mirror','tray','basket','bin','screwdriver','socket','wrench','hammer','level','camera','lens','tripod','speaker','adapter','hub','dock','flag','banner','windsock','bunting','paddleboard','hammock','cooler','lunchbox','plug','registration','purifier','filter','trimmer','shaver','sander','detector','monitor','tracker','alarm','lock','straps','harness','leash','collar','bowl','feeder','brush','clipper','dryer','heater','humidifier','diffuser','projector','keyboard','mouse','tablet','laptop','monitor','headphones','earbuds','microphone','webcam','router','backpack','duffle','tote','sling','pouch','wallet','stool','chair','desk','shelf','cabinet','drawer','curtain','blind','rug','mat','cushion','throw','flashlight','flash','beacon','outlet','socket','power','battery','strap','rope','tie','tape','glue','adhesive','clip','hook','nail','screw','bolt','nut','washer','keychain','lanyard','badge','sheath','holster','sleeve','cover','skin','wrap','grip','pad','cloth','foam','wire','tube','hose','connector','coupler','splitter','converter','sensor','indicator','gauge','meter','thermometer','compass','gps','transmitter','receiver','antenna','telescope','microscope','binoculars','sight','laser','bulb','ribbon','cord','usb','hdmi','ethernet','audio','video'}

def is_duplicate_by_content(title, check_asins=None):
    """Check if title is a duplicate of any existing product (by content or ASIN)."""
    existing = load_existing()
    # ASIN check
    if check_asins:
        for p in existing:
            existing_url = p.get("affiliate_url","")
            for new_asin in check_asins:
                if new_asin and new_asin in existing_url:
                    return True
    t = _clean_tokens(title)
    t_set = set(t)
    stop_words = {"and","the","for","with","in","of","to","a","an","is"}
    for p in existing:
        et = _clean_tokens(p.get("title",""))
        if not et: continue
        exist_set = set(et)
        common = t_set & exist_set
        meaningful = [w for w in common if len(w) > 3 and w not in stop_words]
        shared_nouns = set(meaningful) & PRODUCT_NOUNS
        if shared_nouns and len(meaningful) >= 2: return True
        if len(meaningful) >= 4: return True
    return False

def is_excluded(title, brand=""):
    t = title.lower()
    for pat in EXCLUDE_TITLE_PATTERNS:
        if re.search(pat, title): return True
    for kw in BORING_KEYWORDS:
        if kw in t: return True
    return False

ALL_CATEGORIES = list(CURATION_QUERIES.keys())

def get_active_categories(active_count=6):
    week_num = date.today().isocalendar()[1]
    rng = random.Random(week_num)
    shuffled = ALL_CATEGORIES[:]
    rng.shuffle(shuffled)
    return shuffled[:active_count]

def scrape_batch(candidates, label, fetcher_path):
    """Scrape ratings for a batch of candidate products."""
    need = [p for p in candidates if p.get("asin") and (not p.get("rating") or not p.get("reviews_count"))]
    if not need:
        return 0
    scrape_asins = [p["asin"] for p in need]
    import subprocess, json as json_mod
    result = subprocess.run(
        [sys.executable, fetcher_path, '--batch'] + scrape_asins,
        capture_output=True, text=True, timeout=300
    )
    if result.stdout.strip():
        try:
            ratings = json_mod.loads(result.stdout.strip())
            count = 0
            for r in ratings:
                asin = r.get("asin")
                if r.get("star_rating") and r.get("review_count"):
                    for p in need:
                        if p.get("asin") == asin:
                            p["rating"] = r["star_rating"]
                            p["reviews_count"] = r["review_count"]
                            count += 1
                            break
            print(f"    Got {count}/{len(scrape_asins)} ratings for {label}")
        except json_mod.JSONDecodeError:
            print(f"    Failed to parse rating fetch output for {label}")
    if result.stderr:
        print(f"    stderr: {result.stderr[:200]}")
    return len(need)

def search_fun_tier(api, seen_asins, tier_queries, fun_target=5, item_count=20):
    """Search a tier of fun queries and collect candidates.
    
    Returns list of candidate product dicts with _fun_score set.
    Updates seen_asins in-place to avoid re-searching same ASINs.
    item_count controls how many PAAPI results to fetch per query (default 20
    since many get filtered out by dedup, image, and exclusion checks).
    """
    candidates = []
    for category, queries in tier_queries.items():
        hits = 0
        print(f"  [{category}]")
        for query in queries:
            if hits >= fun_target: break
            print(f"    '{query}'...", end=" ", flush=True)
            try:
                results = api.search_items(query, item_count=item_count)
            except Exception as e:
                print(f"error: {e}")
                continue
            if not results:
                print("no results")
                continue
            new_count = 0
            for r in results:
                if hits >= fun_target: break
                asin = r.get("asin","")
                if not asin or asin in seen_asins: continue
                title = r.get("title","") or ""
                brand = r.get("brand","") or ""
                if is_excluded(title,brand): continue
                if is_duplicate_by_content(title, [asin]): continue
                images = r.get("images",{})
                primary = (images.get("primary",{}) if isinstance(images,dict) else {})
                large = (primary.get("large",{}) if isinstance(primary,dict) else {})
                img = large.get("url","") if isinstance(large,dict) else ""
                if not img: continue
                score = fun_score(title,brand)
                product = {
                    "title":title,"image":img,
                    "description":"(edit me - write genuine why-it-is-worth-it description)",
                    "blurb":"(edit me - one-line hook)",
                    "affiliate_url":f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                    "asin":asin,"_fun_score":round(score,2),
                }
                candidates.append(product)
                seen_asins.add(asin)
                hits += 1; new_count += 1
                print(f"\n      + [fun={score:.2f}] {title[:60]}")
            if new_count == 0: print("(no new)")
            else: print(f"      +{new_count}")
            time.sleep(0.3)
        print(f"    total fun candidates: {hits}")
    candidates.sort(key=lambda p: p["_fun_score"], reverse=True)
    return candidates


def curate_products(count_per_category=2):
    api = AmazonCreatorsAPI(partner_tag=PARTNER_TAG)
    fun_candidates = []
    standard_candidates = []
    seen_asins = set()
    active_categories = get_active_categories(active_count=6)
    total_target = count_per_category * len(active_categories)

    print(f"\n{'='*60}")
    print(f"WorthItGoods Product Curation Pipeline")
    print(f"Target: {total_target} products ({count_per_category} per category)")
    print(f"Active categories: {', '.join(active_categories)}")
    print(f"{'='*60}")

    # Phase 1: Fun products (3 tiers, ALL run every time)
    # Each tier uses different search queries to find fun products.
    # No early exit: we search all 3 tiers and pool every candidate that
    # passes the rating filter, then sort by fun_score and pick the best.
    # This maximizes the chance of finding 1-2 genuinely great fun picks
    # instead of settling for the first product that clears the bar.
    print(f"\n{'─'*60}\n  PHASE 1: Fun Product Search (3 tiers, no early exit)\n{'─'*60}\n")
    rating_fetcher = os.path.join(os.path.dirname(__file__),'scripts','fetch_rating.py')
    fun_passing = []
    fun_query_tiers = [
        ("Tier 1 — Primary", FUN_QUERIES),
        ("Tier 2 — Broader", FUN_QUERIES_TIER_2),
        ("Tier 3 — Safety Net", FUN_QUERIES_TIER_3),
    ]

    for tier_label, tier_queries in fun_query_tiers:
        print(f"\n  \u203a {tier_label}")
        tier_candidates = search_fun_tier(api, seen_asins, tier_queries, fun_target=5, item_count=20)
        if not tier_candidates:
            print(f"  No candidates found in {tier_label}")
            continue

        fun_candidates.extend(tier_candidates)

        # Scrape ratings for this tier's candidates immediately
        print(f"  Scraping ratings for {len(tier_candidates)} fun candidates...")
        scrape_batch(tier_candidates, f"{tier_label} fun", rating_fetcher)

        # Filter by fun rating threshold
        tier_passing = 0
        for p in tier_candidates:
            rating = p.get("rating") or 0
            reviews = p.get("reviews_count") or 0
            if rating >= FUN_MIN_STAR_RATING and reviews >= FUN_MIN_REVIEW_COUNT:
                fun_passing.append(p)
                tier_passing += 1
                print(f"    \N{check mark} FUN PASS: {rating}\u2606 / {reviews} reviews | {p['title'][:60]}")
            else:
                print(f"    \N{cross mark} FUN FAIL: {rating}\u2606 / {reviews} reviews | {p['title'][:50]}")

        # Cooldown before next tier (all tiers run every time)
        if tier_label != fun_query_tiers[-1][0]:
            print(f"  Tier done: {len(fun_passing)} passing so far. Trying next tier in 5s...")
            time.sleep(5)

    if not fun_passing:
        print(f"\n  \u26a0\ufe0f No fun products passed threshold after all 3 tiers. Accepting 0 fun products this week.")

    fun_passing.sort(key=lambda p: p.get("_fun_score", 0), reverse=True)
    print(f"\n  Phase 1 complete: {len(fun_candidates)} total fun candidates, {len(fun_passing)} passing filter")

    # Phase 2: Standard products
    standard_needed = total_target + 6
    print(f"\n{'─'*60}\n  PHASE 2: Standard Product Search (need ~{standard_needed} candidates)\n{'─'*60}\n")
    for category in active_categories:
        queries = CURATION_QUERIES[category]
        if len(standard_candidates) >= standard_needed: break
        hits = 0
        print(f"\n--- {category.upper()} ---")
        for query in queries:
            if hits >= count_per_category or len(standard_candidates) >= standard_needed: break
            print(f"  '{query}'...", end=" ", flush=True)
            try:
                results = api.search_items(query, item_count=20)
            except Exception as e:
                print(f"error: {e}")
                continue
            if not results:
                print("no results")
                continue
            new_count = 0
            for r in results:
                if hits >= count_per_category or len(standard_candidates) >= standard_needed: break
                asin = r.get("asin","")
                if not asin or asin in seen_asins: continue
                title = r.get("title","") or ""
                brand = r.get("brand","") or ""
                if is_excluded(title,brand): continue
                if is_duplicate_by_content(title, [asin]): continue
                images = r.get("images",{})
                primary = (images.get("primary",{}) if isinstance(images,dict) else {})
                large = (primary.get("large",{}) if isinstance(primary,dict) else {})
                img = large.get("url","") if isinstance(large,dict) else ""
                if not img: continue
                score = fun_score(title,brand)
                product = {
                    "title":title,"image":img,
                    "description":"(edit me - write genuine why-it-is-worth-it description)",
                    "blurb":"(edit me - one-line hook)",
                    "affiliate_url":f"https://www.amazon.com/dp/{asin}?tag={PARTNER_TAG}",
                    "asin":asin,
                }
                standard_candidates.append(product)
                seen_asins.add(asin)
                hits += 1; new_count += 1
                fun_indicator = f" [fun={score:.2f}]" if score >= 0.5 else ""
                print(f"\n    + {title[:60]}{fun_indicator}")
            if new_count == 0: print("(no new)")
            else: print(f"    +{new_count}")
            time.sleep(0.3)
        print(f"  total: {hits}")

    print(f"\n  Phase 2 complete: {len(standard_candidates)} standard candidates")

    # Phase 3: Rating filter for standard products only (fun already filtered in Phase 1)
    print(f"\n{'─'*60}\n  PHASE 3: Standard Product Rating Filter\n  Standard >= {MIN_STAR_RATING}\u2606 / {MIN_REVIEW_COUNT} reviews\n{'─'*60}")

    rating_fetcher = os.path.join(os.path.dirname(__file__),'scripts','fetch_rating.py')

    # Scrape standard products
    if standard_candidates:
        if fun_candidates:
            print(f"  Cooldown 5s before scraping standard products...")
            time.sleep(5)
        scrape_batch(standard_candidates, "standard products", rating_fetcher)

    # Filter standard candidates
    standard_passing = []
    for p in standard_candidates:
        rating = p.get("rating") or 0
        reviews = p.get("reviews_count") or 0
        if rating >= MIN_STAR_RATING and reviews >= MIN_REVIEW_COUNT:
            standard_passing.append(p)
            print(f"    PASS: {rating}\u2606 / {reviews} reviews | {p['title'][:60]}")
        else:
            print(f"    FAIL: {rating}\u2606 / {reviews} reviews | {p['title'][:50]}")

    # Build final curated list
    fun_slots = min(2, len(fun_passing))
    curated = []
    curated_asins = set()

    for p in fun_passing[:fun_slots]:
        curated.append({
            "title":p["title"],"image":p["image"],
            "description":p["description"],"blurb":p["blurb"],
            "affiliate_url":p["affiliate_url"],"asin":p["asin"],
        })
        curated_asins.add(p["asin"])

    for p in standard_passing:
        if len(curated) >= total_target: break
        if p.get("asin") not in curated_asins:
            curated.append({
                "title":p["title"],"image":p["image"],
                "description":p["description"],"blurb":p["blurb"],
                "affiliate_url":p["affiliate_url"],"asin":p["asin"],
            })
            curated_asins.add(p["asin"])

    print(f"\n  After rating filter: {len(curated)}/{total_target} products")

    # Enrichment: PAAPI prices
    if curated:
        print(f"\n  ENRICHMENT: PAAPI prices for {len(curated)} products")
        for asin in [p["asin"] for p in curated]:
            try:
                ed = api.get_item(asin)
                if ed and "error" not in ed and ed.get("price"):
                    for p in curated:
                        if p.get("asin") == asin:
                            p["price"] = ed["price"]
                            break
            except Exception as ee:
                print(f"  Warning: Enrichment failed for {asin}: {ee}")
            time.sleep(0.2)
        for p in curated:
            p.pop("asin", None)
        print(f"  Enrichment complete")

    print(f"\n  Final batch: {len(curated)} products (target {total_target})")
    if not curated:
        print("  No products passed rating filter!")
    return curated

def save(products):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(products, f, indent=2)
    print(f"\nSaved {len(products)} products to {OUTPUT_FILE}")
    print(f"Edit descriptions before merging, then: ./add_batch.sh {OUTPUT_FILE}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=2)
    args = parser.parse_args()

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            products = curate_products(count_per_category=args.count)
            if products:
                save(products)
                print(f"\N{check mark} Curation complete: {len(products)} products")
                return 0
            else:
                print(f"\N{cross mark} Attempt {attempt+1}/{max_retries+1}: No products passed filter")
                if attempt < max_retries:
                    wait = 60 * (attempt + 1)
                    print(f"  Retrying in {wait}s...")
                    time.sleep(wait)
        except Exception as e:
            print(f"\N{cross mark} Attempt {attempt+1}/{max_retries+1} failed: {e}")
            if attempt < max_retries:
                wait = 60 * (attempt + 1)
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)

    print("\N{cross mark} All retries exhausted.")
    return 1

if __name__ == "__main__":
    sys.exit(main())