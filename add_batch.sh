#!/usr/bin/env bash
# add_batch.sh – safely prepend a new batch of products (jq-free)
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
# Validate JSONs (python, no jq dependency)
python3 - "$NEW_BATCH" <<'PY'
import json,sys
try:
    json.load(open(sys.argv[1]))
except Exception as e:
    print(f"❌ New batch JSON malformed: {e}", file=sys.stderr)
    sys.exit(1)
PY
if [[ ! -f "$PRODUCTS_FILE" ]]; then
  echo "Existing products file missing: $PRODUCTS_FILE" >&2
  exit 1
fi
python3 - "$PRODUCTS_FILE" <<'PY'
import json,sys
try:
    json.load(open(sys.argv[1]))
except Exception as e:
    print(f"❌ Existing products JSON malformed: {e}", file=sys.stderr)
    sys.exit(1)
PY

# 🔍 AUTO-DEDUP: Check each new product against existing products
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEDUP_SCRIPT="$SCRIPT_DIR/check_dedup.py"
if [[ -f "$DEDUP_SCRIPT" ]]; then
  echo "🔍 Checking new batch for duplicates..."
  set +e
  DUP_OUT=$(python3 "$DEDUP_SCRIPT" "$NEW_BATCH" "$PRODUCTS_FILE" 2>&1)
  DUP_RC=$?
  set -e
  if [[ $DUP_RC -eq 1 ]]; then
    echo "$DUP_OUT"
    echo "❌ Duplicates found — remove them before adding batch"
    exit 1
  elif [[ -n "$DUP_OUT" && "$DUP_OUT" != OK* ]]; then
    echo "$DUP_OUT"
  fi
  echo "✅ No duplicates detected"
fi

# Merge – prepend (python, no jq dependency)
TMP="${PRODUCTS_FILE}.tmp"
python3 - "$NEW_BATCH" "$PRODUCTS_FILE" "$TMP" <<'PY'
import json,sys
new=json.load(open(sys.argv[1]))
prod=json.load(open(sys.argv[2]))
merged=new+prod
json.dump(merged,open(sys.argv[3],'w'),indent=2)
print(f"✅ Prepended {len(new)} new products to {sys.argv[2]}")
PY
mv "$TMP" "$PRODUCTS_FILE"

# Optional local build if script exists
if [[ -x ./build.sh ]]; then
  echo "🚧 Running local build..."
  ./build.sh
  echo "✅ Build finished"
fi
