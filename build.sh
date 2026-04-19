#!/bin/bash
set -e

echo "=== WorthItGoods Aggressive Build ==="

rm -rf _site
mkdir -p _site/images

echo "Copying images..."
cp images/* _site/images/
NUM_IMAGES=$(ls _site/images/*.jpg 2>/dev/null | wc -l)
if [ "$NUM_IMAGES" -ne 10 ]; then
  echo "ERROR: Expected 10 images, got $NUM_IMAGES"
  exit 1
fi
echo "Copied $NUM_IMAGES images OK"

cp style.css _site/
cp main.js _site/
cp index.html _site/

if ! grep -q "hero" _site/index.html || ! grep -q "products-grid" _site/index.html || ! grep -q "cta" _site/index.html; then
  echo "ERROR: index.html missing premium elements"
  exit 1
fi

echo "Build SUCCESS. _site contents:"
ls -la _site/
ls -la _site/images/ | head -5
echo "Deploy-ready."