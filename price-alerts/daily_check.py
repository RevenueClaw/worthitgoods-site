#!/usr/bin/env python3
"""
WorthItGoods Price Checker — Daily Run
========================================
Checks all ASINs, records prices, sends alerts on drops.
Safe to run daily at low-traffic times.

Usage: cd /home/rock/.openclaw/workspace/worthitgoods-repo/price-alerts && python3 daily_check.py
"""

import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, "/home/rock/workspace/chipradar")
sys.path.insert(0, str(Path(__file__).parent))

from price_checker import check_price, extract_asin, send_drop_notification, mark_notified
from price_alerts import get_db, get_subscribers_for_asin, get_last_price, record_price

PRODUCTS_FILE = Path(__file__).parent.parent / "worthitgoods_products.json"
DROP_THRESHOLD = 5.0  # percent


def run():
    print(f"=== WorthItGoods Daily Price Check — {datetime.now(timezone.utc).isoformat()} ===")
    
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    
    # Build ASIN map
    asin_map = {}
    for p in products:
        asin = extract_asin(p.get("url", ""))
        if asin:
            asin_map[asin] = {
                "title": p.get("title", "Unknown"),
                "url": p.get("url", "")
            }
    
    print(f"Loaded {len(asin_map)} ASINs from {len(products)} products")
    
    checked = verified_prices = errors = drops = notifications = 0
    db = get_db()
    
    for asin, info in sorted(asin_map.items()):
        checked += 1
        print(f"  [{checked}/{len(asin_map)}] {info['title'][:50]}...", end=" ")
        
        result = check_price(asin, info["title"])
        
        if result["status"] == "verified":
            price = result["price"]
            verified_prices += 1
            
            # Record price in history
            db.execute(
                "INSERT INTO price_history (asin, price, currency) VALUES (?, ?, 'USD')",
                (asin, price)
            )
            db.commit()
            
            # Check if this is a drop vs the previous checked price
            last_price = get_last_price(asin)
            if last_price and last_price > price:
                drop_pct = ((last_price - price) / last_price) * 100
                if drop_pct >= DROP_THRESHOLD:
                    drops += 1
                    print(f"\n    📉 Drop! ${last_price:.2f} → ${price:.2f} ({drop_pct:.0f}%)")
                    
                    # Notify subscribers
                    subs = get_subscribers_for_asin(asin)
                    for sub in subs:
                        prev = sub.get("last_notified_price")
                        if prev is None or price < prev:
                            ok = send_drop_notification(
                                sub["email"], info["title"], asin,
                                last_price, price, info["url"]
                            )
                            if ok:
                                mark_notified(sub["email"], asin, price)
                                notifications += 1
                                print(f"      📧 Notified {sub['email']}")
                                time.sleep(0.3)
            else:
                print(f"${price:.2f}")
        else:
            errors += 1
            print(f"⚠ {result['status']}: {result.get('error', '')}")
        
        time.sleep(0.5)  # API rate limiting
    
    db.close()
    
    print(f"\n{'='*50}")
    print(f"Summary: {verified_prices} verified, {errors} errors, {drops} drops, {notifications} notifications")
    print(f"{'='*50}")


if __name__ == "__main__":
    run()
