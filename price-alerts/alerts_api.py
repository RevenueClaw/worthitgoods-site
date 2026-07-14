#!/usr/bin/env python3
"""
WorthItGoods Price Alert Subscription API
==========================================
Simple HTTP server for handling price alert subscriptions.
Runs on localhost or Pi5 for the static site to POST to.

Endpoints:
  POST /subscribe  — {"email": "...", "asin": "..."} 
  POST /unsubscribe — {"email": "..."}
  GET  /health — returns ok

Usage: python3 alerts_api.py [--port 9004]
"""

import sys
import json
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from price_alerts import subscribe, unsubscribe, get_subscription_count

try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler


class AlertHandler(BaseHTTPRequestHandler):
    
    def _send(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self._send({"ok": True})
    
    def do_GET(self):
        if self.path == "/health":
            self._send({"status": "ok", "subscriptions": get_subscription_count()})
        else:
            self._send({"error": "Not found"}, 404)
    
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body) if body else {}
        except Exception:
            self._send({"success": False, "message": "Invalid JSON"}, 400)
            return
        
        if self.path == "/subscribe":
            email = data.get("email", "").strip()
            asin = data.get("asin", "").strip()
            product = data.get("product_title", "")
            if not email or not asin:
                self._send({"success": False, "message": "Email and ASIN required"}, 400)
                return
            result = subscribe(email, asin, product)
            self._send(result)
        
        elif self.path == "/unsubscribe":
            email = data.get("email", "").strip()
            if not email:
                self._send({"success": False, "message": "Email required"}, 400)
                return
            result = unsubscribe(email)
            self._send(result)
        
        else:
            self._send({"error": "Not found"}, 404)


def main():
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--port" else 9004
    
    # Ensure database is initialized
    from price_alerts import init_db
    init_db()
    
    server = HTTPServer(("0.0.0.0", port), AlertHandler)
    print(f"WorthItGoods Price Alert API running on port {port}")
    print(f"  POST /subscribe   — subscribe to price alerts")
    print(f"  POST /unsubscribe  — unsubscribe")
    print(f"  GET  /health       — health check")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()