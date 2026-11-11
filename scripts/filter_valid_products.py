#!/usr/bin/env python3
"""
Preflight filter for WorthItGoods product JSON.

Reads a product JSON file, validates every record, drops rejected records,
and writes a clean JSON file. Rejected records are appended to
logs/validation_rejects.log.

Usage:
    python3 scripts/filter_valid_products.py <input.json> <output.json>
"""
import json
import sys
from pathlib import Path

# Make sure we can import validate_product_record.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_product_record import validate_products


def main():
    if len(sys.argv) < 3:
        print("Usage: filter_valid_products.py <input.json> <output.json>", file=sys.stderr)
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    if not in_path.exists():
        print(f"FATAL: input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    products = json.loads(in_path.read_text(encoding="utf-8"))
    result = validate_products(products, rejects_log=Path("logs/validation_rejects.log"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result["valid"], indent=2), encoding="utf-8")

    print(f"filter_valid: {len(products)} in, {len(result['valid'])} valid, {len(result['invalid'])} rejected")
    if result["invalid"]:
        print(f"  see logs/validation_rejects.log")


if __name__ == "__main__":
    main()
