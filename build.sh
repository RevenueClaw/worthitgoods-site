#!/usr/bin/env bash
# Build script for WorthItGoods site
set -euo pipefail

# Remove any previous build output
rm -rf _site
mkdir -p _site

# Generate the styled site using the JavaScript generator (produces HTML with CSS grid, images, etc.)
node generate-pages.js

# Copy static assets (CSS, JS, sitemap) into the built site directory
cp style.css main.js sitemap.xml _site/

# Ensure all local product images are included
if [ -d images ]; then
  cp -r images _site/
fi

# Verify the build succeeded
if [ -f _site/index.html ]; then
  echo "Build complete. _site/ ready."
else
  echo "Error: index.html missing after build."
  exit 1
fi

# List site data directory contents (optional, harmless if empty)
ls -la _site/data/ || true
