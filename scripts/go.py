#!/usr/bin/env python3
"""WorthItGoods affiliate link click tracker & redirector.
Usage: /go/{product-slug} or /go/asin/{asin}
Records click → 301 redirects to Amazon with affiliate tag.

Amazon tag: worthitgoods-20
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clicks.db"
AMAZON_TAG = "worthitgoods-20"

# Product slug → ASIN mapping (generated from product pages)
# This is a fallback — main lookup is from URL param
SLUG_TO_ASIN = {}

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT,
            slug TEXT,
            referrer TEXT,
            user_agent TEXT,
            ip TEXT,
            timestamp TEXT,
            page TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            total_clicks INTEGER DEFAULT 0,
            unique_asins INTEGER DEFAULT 0,
            top_products TEXT
        )
    """)
    conn.commit()
    return conn

def record_click(conn, asin, slug, referrer, user_agent, ip, page):
    conn.execute(
        "INSERT INTO clicks (asin, slug, referrer, user_agent, ip, timestamp, page) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (asin, slug, referrer, user_agent, ip, datetime.now().isoformat(), page)
    )
    conn.commit()

def get_stats(conn, days=7):
    cursor = conn.execute("""
        SELECT asin, COUNT(*) as cnt FROM clicks
        WHERE timestamp > datetime('now', ?)
        GROUP BY asin ORDER BY cnt DESC LIMIT 10
    """, (f'-{days} days',))
    return cursor.fetchall()

class ClickHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")
        params = parse_qs(parsed.query)
        
        conn = init_db()
        
        # Route: /go/{slug} or /go/asin/{asin}
        parts = path.split("/")
        asin = None
        slug = None
        page = None
        
        if path.startswith("go/asin/"):
            asin = path.replace("go/asin/", "")
        elif path.startswith("go/"):
            slug = path.replace("go/", "")
            asin = params.get("asin", [None])[0]
            page = params.get("page", ["/"])[0]
        
        if not asin and not slug:
            # Stats page
            if path == "go/stats":
                stats = get_stats(conn, 7)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"clicks_7d": [{"asin": r[0], "count": r[1]} for r in stats]}).encode())
                return
            
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        
        referrer = self.headers.get("Referer", "")
        ua = self.headers.get("User-Agent", "")
        ip = self.client_address[0]
        
        record_click(conn, asin or "", slug or "", referrer, ua, ip, page or "")
        
        # Redirect to Amazon
        if asin:
            redirect_url = f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
        else:
            redirect_url = f"https://www.amazon.com?tag={AMAZON_TAG}"
        
        self.send_response(301)
        self.send_header("Location", redirect_url)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Silence server logs

def run_server(port=8094):
    server = HTTPServer(("0.0.0.0", port), ClickHandler)
    print(f"Click tracker on :{port}")
    server.serve_forever()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        conn = init_db()
        stats = get_stats(conn, int(sys.argv[2]) if len(sys.argv) > 2 else 7)
        print(f"Click stats ({len(sys.argv[2]) if len(sys.argv) > 2 else 7} days):")
        for asin, count in stats:
            print(f"  {asin}: {count} clicks")
    else:
        run_server()
