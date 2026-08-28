#!/usr/bin/env python3
"""Generate real descriptions for placeholder products in sample_products.json"""
import json, os, re, urllib.request, sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(REPO_DIR, "data", "sample_products.json")

def call_llm(prompt, max_tokens=2000):
    api_key = os.environ.get("LLM_API_KEY", "")
    data_bytes = json.dumps({
        "model": "deepseek/deepseek-v4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        url = "https://openrouter.ai/api/v1/chat/completions"
    else:
        url = "http://192.168.4.131:18792/infer"
    try:
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None

def main():
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    idx_list = [i for i, p in enumerate(data) if "edit me" in str(p.get("description","")) or "edit me" in str(p.get("blurb",""))]
    print(f"Found {len(idx_list)} products with placeholder descriptions")
    
    if not idx_list:
        print("No placeholders to fix!")
        return 0
    
    product_lines = []
    for idx in idx_list:
        p = data[idx]
        product_lines.append(f"PRODUCT {idx}: ${p['price']} — {p['title']}")
        product_lines.append(f"  Image URL: {p['image']}")
        asin = ''
        for field in ['asin', 'ASIN']:
            if field in p:
                asin = p[field]
                break
        if not asin and 'affiliate_url' in p:
            m = re.search(r'/dp/([A-Z0-9]{10})', p['affiliate_url'])
            if m: asin = m.group(1)
        if not asin:
            asin = 'unknown'
        product_lines.append(f"  ASIN: {asin}")
        product_lines.append("")
    
    prompt = """You are writing product descriptions for WorthItGoods.com, an honest product curation site. Voice: direct, slightly irreverent, no hype. Use contractions. Keep blurbs under 15 words and descriptions under 60 words.

For each product below, generate:
1. A one-line blurb (hook) that makes someone want to click — short, punchy, honest
2. A genuine "why it's worth it" description (2-4 sentences, honest voice)

Format your response EXACTLY as:
PRODUCT [idx]:
BLURB: <one line>
DESCRIPTION: <2-4 sentence description>

---
""" + "\n".join(product_lines)
    
    print("Calling LLM to generate descriptions...")
    response = call_llm(prompt)
    if not response:
        print("FAILED: Could not get LLM response")
        return 1
    
    print(f"\n=== LLM Response ===\n{response}\n")
    
    # Parse response and update data
    current_idx = None
    updates = {}
    
    for line in response.split("\n"):
        line = line.strip()
        m = re.match(r"PRODUCT\s+(\d+):", line)
        if m:
            current_idx = int(m.group(1))
            if current_idx not in updates:
                updates[current_idx] = {}
            continue
        
        m = re.match(r"BLURB:\s*(.+)", line)
        if m and current_idx is not None:
            updates[current_idx]["blurb"] = m.group(1).strip()
            continue
        
        m = re.match(r"DESCRIPTION:\s*(.+)", line)
        if m and current_idx is not None:
            if "description" not in updates[current_idx]:
                updates[current_idx]["description"] = ""
            updates[current_idx]["description"] += m.group(1).strip() + " "
        elif line and current_idx is not None and "description" in updates.get(current_idx, {}):
            updates[current_idx]["description"] += line + " "
    
    # Clean up descriptions
    for idx in updates:
        if "description" in updates[idx]:
            updates[idx]["description"] = updates[idx]["description"].strip()
    
    # Apply updates
    updated_count = 0
    for idx_str, vals in updates.items():
        idx = int(idx_str)
        if "blurb" in vals:
            data[idx]["blurb"] = vals["blurb"]
            updated_count += 1
            print(f"  ✓ Updated blurb for [{idx}]: {vals['blurb'][:60]}")
        if "description" in vals:
            data[idx]["description"] = vals["description"]
            updated_count += 1
            print(f"  ✓ Updated description for [{idx}]: {vals['description'][:60]}")
    
    if updated_count > 0:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\n✅ Saved {updated_count} field updates to {DATA_FILE}")
    else:
        print("\n⚠️ No updates applied. Check LLM response format.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
