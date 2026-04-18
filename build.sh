#!/usr/bin/env bash
# Build script for WorthItGoods - generates pages from data and deploys to _site/

set -e

echo "Generating product pages..."
python3 generate-site.py

echo "Copying assets..."
mkdir -p _site/images
cp -r index.html style.css main.js sitemap.xml _site/ 2>/dev/null || true
cp -r images/* _site/images/ 2>/dev/null || true

echo "Build complete. _site/ ready for deployment."
ls -la _site/
