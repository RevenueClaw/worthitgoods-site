#!/usr/bin/env bash
set -e

mkdir -p _site/data
cp index.html style.css main.js sitemap.xml _site/
cp sample_products.json _site/data/
cp -r images _site/ 2>/dev/null || true

echo "Build complete. _site/ ready."
ls -la _site/data/
