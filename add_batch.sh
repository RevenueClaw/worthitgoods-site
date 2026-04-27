#!/usr/bin/env bash
# add_batch.sh – safely prepend a new batch of products
# Usage: ./add_batch.sh path/to/new_batch.json
set -euo pipefail
PRODUCTS_FILE="data/sample_products.json"
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 path/to/new_batch.json" >&2
  exit 1
fi
NEW_BATCH="$1"
if [[ ! -f "$NEW_BATCH" ]]; then
  echo "New batch file not found: $NEW_BATCH" >&2
  exit 1
fi
# Validate JSONs
if ! jq empty "$NEW_BATCH" >/dev/null 2>&1; then
  echo "❌ New batch JSON malformed" >&2
  exit 1
fi
if [[ ! -f "$PRODUCTS_FILE" ]]; then
  echo "Existing products file missing: $PRODUCTS_FILE" >&2
  exit 1
fi
if ! jq empty "$PRODUCTS_FILE" >/dev/null 2>&1; then
  echo "❌ Existing products JSON malformed" >&2
  exit 1
fi
# Merge – prepend
TMP="${PRODUCTS_FILE}.tmp"
jq -s '.[0] + .[1]' "$NEW_BATCH" "$PRODUCTS_FILE" > "$TMP"
if ! jq empty "$TMP" >/dev/null 2>&1; then
  echo "❌ Merged JSON broken" >&2
  rm -f "$TMP"
  exit 1
fi
mv "$TMP" "$PRODUCTS_FILE"
echo "✅ Prepended $(jq length \"$NEW_BATCH\") new products to $PRODUCTS_FILE"
# Optional local build if script exists
if [[ -x ./build.sh ]]; then
  echo "🚧 Running local build..."
  ./build.sh
  echo "✅ Build finished"
fi
