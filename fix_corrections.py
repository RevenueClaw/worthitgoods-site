#!/usr/bin/env python3
"""Fix shifted product descriptions in worthitgoods data."""
import json

DATA_FILE = "data/sample_products.json"

with open(DATA_FILE) as f:
    prods = json.load(f)

CORRECTIONS = {
    18: "Patriotic multicolor Crocs that let you show some spirit without sacrificing comfort. The classic Crocs design means they are lightweight, easy to clean, and comfortable for all-day wear at the BBQ or parade. Summer footwear that does not take itself too seriously.",
    19: "A 60-inch flannel tortilla blanket that is soft enough for cozying up and big enough to wrap yourself in like a burrito. The 285GSM flannel is noticeably thicker than novelty blankets half the price. Self-care with a sense of humor.",
    20: "A pleated fan flag set that adds dimension and movement to your 4th of July display. The brass grommets and zip ties make installation on porch railings or fences quick and secure. Better than flat flags for visual impact.",
    21: "An inflatable paddleboard that is stable enough for beginners yet responsive enough for experienced riders. The included kayak seat adds versatility, and the full accessory package means you are ready to hit the water right out of the box.",
    22: "A custom photo Hawaiian shirt that makes for an unforgettable gift at family gatherings or bachelor parties. The print quality is sharp and durable, and the fabric is breathable enough for real summer wear. The gift that keeps getting laughs.",
    23: "A rechargeable LED flying disc with 108 RGB lights that create stunning patterns after dark. Waterproof and durable enough for serious throws, it turns an evening park hang into something memorable. The frisbee upgrade you did not know existed.",
    24: "A double cotton hammock with a steel stand that sets up anywhere with no trees needed. The 450-pound capacity handles two adults, and the upgraded polyester end strings resist fraying longer than standard cotton. Backyard luxury in minutes.",
}

for idx, desc in CORRECTIONS.items():
    prods[idx]["description"] = desc

with open(DATA_FILE, "w") as f:
    json.dump(prods, f, indent=2)

print(f"Corrected {len(CORRECTIONS)} descriptions")