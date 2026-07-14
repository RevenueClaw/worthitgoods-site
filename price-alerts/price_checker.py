#!/usr/bin/env python3
"""
WorthItGoods Price Checker
==========================
Checks current prices for all tracked products, records price history,
and sends email notifications to subscribers on significant drops.

Runs daily via cron. Also feeds data fresh into the price_alerts.db for
the subscription system on the site.

Reuses: AmazonCreatorsAPI from chipradar
"""

import sys
import json
import time
import os
import re
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, "/home/rock/workspace/chipradar")

try:
    from amazon_creators_api_v1 import AmazonCreatorsAPI
except ImportError:
    print("ERROR: Could not import AmazonCreatorsAPI from chipradar.", file=sys.stderr)
    sys.exit(1)

# Import price alert database
BASE = Path(__file__).parent
PRODUCTS_FILE = BASE.parent / "worthitgoods_products.json"
PARENT = BASE.parent  # price-alerts is a subdirectory

sys.path.insert(0, str(BASE))
from price_alerts import get_db, record_price, get_subscribers_for_asin, mark_notified, get_last_price

PRICE_FLOOR = 3.0
PRICE_CEILING = 999.99
DROP_THRESHOLD_PERCENT = 5.0  # Minimum % drop to trigger a notification


def extract_asin(url: str) -> str:
    """Extract ASIN from an Amazon URL."""
    if not url:
        return None
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    # Try alternate URL format
    match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)
    return None


def check_price(asin: str, product_title: str = "") -> dict:
    """Check current price for a single ASIN. Returns price info dict."""
    result = {
        "asin": asin,
        "title": product_title,
        "price": None,
        "status": "error",
        "error": None,
    }
    
    for attempt in range(3):
        try:
            api = AmazonCreatorsAPI(partner_tag="worthitgoods-20")
            item = api.get_item(asin)
            price = item.get("price")
            
            if price is not None and PRICE_FLOOR <= price <= PRICE_CEILING:
                result["price"] = round(price, 2)
                result["status"] = "verified"
            elif price is not None:
                result["price"] = round(price, 2)
                result["status"] = "below_floor"
            else:
                result["status"] = "unavailable"
                result["error"] = "No price found"
            
            # Get title if not provided
            if not product_title:
                info = item.get("item_info", {}) or {}
                title_data = info.get("title", {}) or {}
                result["title"] = (title_data.get("value", "") or title_data.get("display_value", ""))[:200]
            
            break
            
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt < 2:
                wait = 2.0 * (attempt + 1)
                print(f"    Rate limited on {asin}, retry {attempt+1} in {wait:.0f}s...")
                time.sleep(wait)
                continue
            result["status"] = "error"
            result["error"] = str(err_str)[:200]
            break
    
    return result


def send_drop_notification(email: str, product_title: str, asin: str, 
                           old_price: float, new_price: float, affiliate_url: str):
    """Send a price drop email notification via AgentMail."""
    try:
        from agentmail import AgentMail
        client = AgentMail()
        
        drop_pct = ((old_price - new_price) / old_price) * 100
        subject = f"📉 Price Drop Alert: {product_title[:50]} — Now ${new_price:.2f}"
        
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<div style="border:2px solid #ff6b6b;border-radius:12px;padding:24px;">
<div style="font-size:14px;color:#ff6b6b;font-weight:600;margin-bottom:8px;">📉 PRICE DROP</div>
<h2 style="margin:0 0 12px;font-size:20px;">{product_title}</h2>
<div style="background:#f8f9fa;border-radius:8px;padding:16px;margin:16px 0;">
<table style="width:100%;border-collapse:collapse;">
<tr>
<td style="text-align:center;padding:8px;">
<div style="font-size:12px;color:#6b7280;">Was</div>
<div style="font-size:22px;font-weight:700;color:#9ca3af;text-decoration:line-through;">${old_price:.2f}</div>
</td>
<td style="text-align:center;padding:8px;">
<div style="font-size:28px;color:#10b981;">→</div>
</td>
<td style="text-align:center;padding:8px;">
<div style="font-size:12px;color:#6b7280;">Now</div>
<div style="font-size:22px;font-weight:700;color:#10b981;">${new_price:.2f}</div>
</td>
<td style="text-align:center;padding:8px;">
<div style="font-size:12px;color:#6b7280;">You Save</div>
<div style="font-size:18px;font-weight:700;color:#10b981;">-{drop_pct:.0f}%</div>
</td>
</tr>
</table>
</div>
<a href="{affiliate_url}" style="display:block;padding:14px 24px;background:linear-gradient(135deg,#ff9a56,#ff6b6b);color:#fff;text-decoration:none;border-radius:8px;text-align:center;font-size:16px;font-weight:600;">View Deal on Amazon →</a>
<p style="font-size:12px;color:#9ca3af;margin-top:20px;text-align:center;">
You're receiving this because you subscribed to price alerts at WorthItGoods.com.<br>
<a href="https://www.worthitgoods.com/unsubscribe?email={email}" style="color:#6b7280;">Unsubscribe from this alert</a>
</p>
</div>
</body>
</html>"""
        
        client.inboxes.messages.send(
            inbox_id="revenueclaw@agentmail.to",
            to=email,
            subject=subject,
            html=html,
        )
        return True
    except Exception as e:
        print(f"    ⚠ Email send failed for {email}: {e}")
        return False


def check_all_prices():
    """
    Main function: check all known products, record prices, handle drops.
    This reads all products from the products file and checks their ASINs.
    """
    # Load products
    if not PRODUCTS_FILE.exists():
        print(f"Products file not found: {PRODUCTS_FILE}")
        return
    
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    
    print(f"Loaded {len(products)} products")
    
    # Extract ASINs
    asin_map = {}
    for p in products:
        asin = extract_asin(p.get("url", ""))
        if not asin:
            # Some products might have affiliate_url containing the ASIN
            asin = extract_asin(p.get("url", ""))
        if asin:
            asin_map[asin] = p.get("title", "Unknown Product")
    
    print(f"Found {len(asin_map)} unique ASINs to check")
    
    checked = 0
    verified = 0
    drops_found = 0
    notifications_sent = 0
    
    # Check each price
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    
    for asin, title in sorted(asin_map.items()):
        print(f"  [{checked+1}/{len(asin_map)}] Checking {asin} ({title[:40]}...)", end="")
        
        result = check_price(asin, title)
        
        if result["status"] == "verified":
            price = result["price"]
            verified += 1
            print(f" → ${price:.2f}")
            
            # Record price
            db_cursor.execute(
                "INSERT INTO price_history (asin, price, currency) VALUES (?, ?, 'USD')",
                (asin, price)
            )
            db_conn.commit()
            
            # Check for price drop vs last known
            last_price = get_last_price(asin)
            if last_price and last_price > price:
                drop_pct = ((last_price - price) / last_price) * 100
                if drop_pct >= DROP_THRESHOLD_PERCENT:
                    drops_found += 1
                    print(f"    📉 Price drop detected! ${last_price:.2f} → ${price:.2f} ({drop_pct:.1f}%)")
                    
                    # Find subscribers for this ASIN
                    subscribers = get_subscribers_for_asin(asin)
                    for sub in subscribers:
                        prev_notified = sub.get("last_notified_price")
                        # Only notify if price dropped below last notification price
                        if prev_notified is None or price < prev_notified:
                            affiliate_url = products[0].get("url", "")
                            # Find the right URL
                            for p in products:
                                if extract_asin(p.get("url", "")) == asin:
                                    affiliate_url = p.get("url", "")
                                    break
                            
                            ok = send_drop_notification(
                                sub["email"], title, asin,
                                last_price, price, affiliate_url
                            )
                            if ok:
                                mark_notified(sub["email"], asin, price)
                                notifications_sent += 1
                                print(f"      📧 Notified {sub['email']}")
                            time.sleep(0.5)  # Rate limit emails
            
        elif result["status"] == "unavailable" or result["status"] == "below_floor":
            print(f" → {result['status']} ({result.get('error', 'no error')})")
        else:
            print(f" → ERROR: {result.get('error', 'unknown')}")
        
        checked += 1
        time.sleep(0.6)  # Rate limit API calls
    
    db_conn.close()
    
    print(f"\n{'='*50}")
    print(f"Summary: {verified} verified, {drops_found} drops, {notifications_sent} notifications sent")
    print(f"{'='*50}")


if __name__ == "__main__":
    check_all_prices()