#!/bin/bash
set -e

echo "=== WorthItGoods Build ==="

rm -rf _site
mkdir -p _site/images

# Safely copy images if they exist
if [ -d "images" ] && [ "$(ls -A images 2>/dev/null)" ]; then
 cp -r images/* _site/images/ 2>/dev/null || true
 echo "Images copied."
else
 echo "Warning: No images/ folder found. Creating empty one."
 mkdir -p _site/images
fi

# Copy other assets
cp style.css _site/ 2>/dev/null || true
cp main.js _site/ 2>/dev/null || true
cp index.html _site/ 2>/dev/null || true

echo "Build completed. _site/ ready."
ls -la _site/