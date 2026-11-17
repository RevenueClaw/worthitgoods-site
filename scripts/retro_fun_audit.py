#!/usr/bin/env python3
"""Retro-sweep the live catalog through the taste policy (browse + theme-fit).

Usage:
  python3 scripts/retro_fun_audit.py            # dry-run report
  python3 scripts/retro_fun_audit.py --apply [--delete-approved titles.json]
     --apply only strips bad THEME TAGS; product DELETION additionally needs an
     owner-approved JSON list of exact titles (retro sweeps must never remove
     hand-curated stock — the 2026-11-17 incident).

  --apply deletes browse-failures and STRIPS the theme tag from off-theme
  items (kept as evergreen). Afterwards: bash build.sh, commit, push.

Run from repo root with OPENROUTER_API_KEY in env.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from curation_policy import sweep  # noqa: E402

SRC = Path("data/sample_products.json")


def main():
    apply = "--apply" in sys.argv
    products = json.loads(SRC.read_text())
    print(f"catalog: {len(products)} items — sweeping (hard-block -> LLM browse+fit)")
    keep, untag, drop = sweep(products)
    keep_ids = {id(p) for p in keep}
    untag_titles = {str(p.get("title", "")) for p in untag}
    final = [p for p in keep] + untag  # untagged items stay in the catalog
    print(f"\nSUMMARY: keep {len(keep)}, untag-keep {len(untag)}, drop {len(drop)}")
    for p in drop:
        print(f"  DROP:   {str(p.get('title',''))[:72]}")
    for p in untag:
        print(f"  UNTAG:  {str(p.get('title',''))[:72]}")
    if apply:
        # GUARD (2026-11-17, after the owner's curated back half was nearly
        # destroyed by an aggressive sweep): retro audits may ONLY untag
        # off-theme items. DELETIONS require an explicit owner-approved title
        # file: --delete-approved <json list of titles>.
        approved = []
        if "--delete-approved" in sys.argv:
            ai = sys.argv.index("--delete-approved")
            approved = set(json.loads(Path(sys.argv[ai+1]).read_text()))
        if approved:
            drop = [p for p in drop if str(p.get("title")) in approved]
        else:
            print("NOTE: deletions withheld (no --delete-approved list); untag applied only")
            drop = []
        final = [x for x in final if x not in drop] if drop else final
        SRC.write_text(json.dumps(final, indent=2))
        print(f"applied — sample_products.json now {len(final)} items ({len(untag)} theme-stripped)")
        print("next: bash build.sh && git add -A && git commit && git push")
    elif not apply:
        print("(dry-run; pass --apply to remove)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
