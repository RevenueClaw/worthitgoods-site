#!/usr/bin/env python3
"""
Auto Comparison Generator — runs the scout, picks the best candidate,
queries competitor prices/features, and writes the comparison article.

Usage:
    python3 scripts/auto_comparison.py                     # Full auto run
    python3 scripts/auto_comparison.py --dry-run            # Show what it'd do
    python3 scripts/auto_comparison.py --article <name>     # Write specific article

Requires: AmazonCreatorsAPI, web_search capability (via agent turn)
"""

import json
import os
import re
import sys
import subprocess
from datetime import datetime, timedelta, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATES_FILE = os.path.join(SCRIPTS_DIR, "comparison_candidates.json")
OUTPUT_FILE = os.path.join(SCRIPTS_DIR, "auto_comparison_result.json")

# Template for the cron publish command
CRON_PUBLISH_TEMPLATE = '''cd {repo} && python3 scripts/publish_comparison.py {slug} "{date}" "{title}" "{description}" "{image}"'''


def load_candidates():
    """Load comparison candidates from scout output."""
    if not os.path.exists(CANDIDATES_FILE):
        print("No candidates file found. Run scout_comparisons.py first.")
        return None
    
    with open(CANDIDATES_FILE) as f:
        return json.load(f)


def save_result(result):
    """Save auto_comparison result."""
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    return OUTPUT_FILE


def generate_article_slug(title):
    """Generate URL-friendly slug from title."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = slourg[:60].strip('-')
    return slug


def pick_best_candidate(candidates):
    """Pick the best candidate for a comparison article."""
    if not candidates or "comparison_candidates" not in candidates:
        return None
    
    picks = candidates["comparison_candidates"]
    
    # Filter: must have at least one competitor
    picks = [p for p in picks if p.get("competitors")]
    
    if not picks:
        return None
    
    # Sort by priority, then by having the most competitors
    picks.sort(key=lambda p: (
        0 if p.get("priority") == "high" else 1,
        -len(p.get("competitors", []))
    ))
    
    return picks[0] if picks else None


def main():
    dry_run = "--dry-run" in sys.argv
    
    print(f"Auto Comparison Generator")
    print(f"{'='*50}")
    
    # Load scout results
    candidates = load_candidates()
    if not candidates:
        print("No candidates available. Run scout_comparisons.py first.")
        sys.exit(1)
    
    best = pick_best_candidate(candidates)
    
    if not best:
        print("No viable candidates found.")
        sys.exit(1)
    
    product_name = best["title"][:80]
    for comp in best.get("competitors", []):
        comp_name = comp.get("name", "unknown")
        comp_price = comp.get("price", "N/A")
        print(f"\nBest candidate for new comparison:")
        print(f"  Our product: {product_name}")
        print(f"  vs           {comp_name} (${comp_price})")
        print(f"  Category:    {best.get('category', '?')}")
        print(f"  Our ASIN:    {best.get('asin', '?')}")
        print(f"  Their ASIN:  {comp.get('asin', '?')}")
    
    print(f"\n{'='*50}")
    print(f"Result saved to: {OUTPUT_FILE}")
    
    # Build result for the agent to use
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "our_asin": best.get("asin"),
            "our_title": product_name,
            "our_price": best.get("price"),
            "category": best.get("category"),
            "our_url": best.get("url"),
            "competitors": [
                {
                    "name": comp.get("name"),
                    "asin": comp.get("asin"),
                    "price": comp.get("price"),
                    "type": comp.get("type"),
                }
                for comp in best.get("competitors", [])
            ]
        },
        "publish_command_skeleton": CRON_PUBLISH_TEMPLATE.format(
            repo=REPO_DIR,
            slug="{slug}",
            date="{date}",
            title="{title}",
            description="{description}",
            image="{image}"
        ),
        "instructions": {
            "next_steps": [
                "1. Use AmazonCreatorsAPI to get features for both products",
                "2. Write the comparison article HTML",
                "3. Save to comparisons/{slug}.html",
                "4. git add + git commit + git push",
                "5. Create cron job for scheduled publish",
            ]
        }
    }
    
    if not dry_run:
        save_result(result)
    
    print(f"\nNext: agent writes the article using AmazonCreatorsAPI data")
    print(f"Target publish: ~4 weeks out (to stagger with existing schedule)")


if __name__ == "__main__":
    main()