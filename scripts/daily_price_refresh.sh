#!/bin/bash
# AMZ-COMPLIANCE 2026-11-05: DISABLED.
# This job previously fetched Amazon PAAPI prices, published live-prices.json, and
# pushed to master. Amazon Associates policy prohibits caching Amazon pricing >24h,
# price tracking/graphs, and price alerts. Do not re-enable without compliance review.
LOG=/tmp/wig_price_refresh.log
echo "=== $(date -Is) DISABLED: Amazon price refresh skipped (compliance) ===" >> "$LOG"
exit 0
