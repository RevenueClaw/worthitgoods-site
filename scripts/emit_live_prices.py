#!/usr/bin/env python3
"""AMZ-COMPLIANCE 2026-11-05.

Amazon Associates policy: do not cache/display Amazon pricing content, do not use
it in price tracking/graphs, and do not send price alerts. This emitter is disabled
so no Amazon price data is published to the static site.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "live-prices.json"

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "disabled": True,
        "reason": "Amazon Associates compliance: Amazon pricing is not tracked, cached, or displayed.",
        "prices": {}
    }, separators=(",", ":")))
    print(f"DISABLED: wrote {OUT} with no Amazon price data.")

if __name__ == "__main__":
    main()
