import json
import os
import requests
from pathlib import Path

# API Keys (set via environment variables or replace with actual keys locally)
PARTNERIZE_KEY = os.environ.get("PARTNERIZE_KEY", "")
IMPACT_SID = os.environ.get("IMPACT_SID", "")
AWIN_TOKEN = os.environ.get("AWIN_TOKEN", "")

# Output path
OUTPUT_DIR = Path("/home/rock/.openclaw/workspace/worthitgoods-site/data")
OUTPUT_FILE = OUTPUT_DIR / "offers.json"

def fetch_partnerize_offers():
    if not PARTNERIZE_KEY:
        print("[MOCK] Fetching mock Partnerize offers...")
        return [{"id": "pz_1", "title": "Mock Partnerize Product", "price": 10.00}]
    
    url = "https://api.partnerize.com/v1/offers"
    headers = {"Authorization": f"Bearer {PARTNERIZE_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Partnerize fetch failed: {e}")
        return []

def fetch_impact_offers():
    if not IMPACT_SID:
        print("[MOCK] Fetching mock Impact offers...")
        return [{"id": "imp_1", "title": "Mock Impact Product", "price": 20.00}]
        
    url = f"https://api.impact.com/Mediapartners/{IMPACT_SID}/offers"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Impact fetch failed: {e}")
        return []

def fetch_awin_offers():
    if not AWIN_TOKEN:
        print("[MOCK] Fetching mock Awin offers...")
        return [{"id": "aw_1", "title": "Mock Awin Product", "price": 30.00}]
        
    url = f"https://api.awin.com/publishers/offers?accessToken={AWIN_TOKEN}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Awin fetch failed: {e}")
        return []

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    partnerize_data = fetch_partnerize_offers()
    impact_data = fetch_impact_offers()
    awin_data = fetch_awin_offers()

    combined = {
        "partnerize": partnerize_data,
        "impact": impact_data,
        "awin": awin_data
    }

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2)
        print(f"[SUCCESS] Offer data refreshed. Saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to write offers to file: {e}")
