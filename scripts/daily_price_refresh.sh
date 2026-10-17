#!/bin/bash
# Daily WorthItGoods price refresh.
#
# Root problem this fixes: comparison pages bake prices into text at build time
# and the site was built from a stale dataset, so visitors were shown prices
# Amazon would not honor (that mismatch is what suppresses purchases).
# price-sync.js corrects the display in the browser; this job keeps the data it
# reads fresh and publishes it, without needing a full page rebuild.
set -euo pipefail

REPO=/home/rock/workspace/worthitgoods-site
LOG=/tmp/wig_price_refresh.log
cd "$REPO"
echo "=== $(date -Is) price refresh ===" >> "$LOG"

# 1. Refresh prices from Amazon PAAPI into the product dataset.
python3 scripts/batch_price_sweep.py >> "$LOG" 2>&1

# 2. Emit the slim JSON the browser hydrates from.
python3 scripts/emit_live_prices.py >> "$LOG" 2>&1

# 3. Mirror into the published directory.
mkdir -p _site/assets
cp assets/live-prices.json _site/assets/live-prices.json

# 4. Deploy only if something changed.
git add assets/live-prices.json _site/assets/live-prices.json
if git diff --cached --quiet; then
    echo "no price changes" >> "$LOG"
else
    git commit -q -m "chore: daily price refresh $(date +%F)"
    git push origin HEAD >> "$LOG" 2>&1
    echo "deployed" >> "$LOG"
fi
echo "OK" >> "$LOG"