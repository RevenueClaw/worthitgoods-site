#!/usr/bin/env bash
# Build script for Cloudflare Pages

# Create output directory
mkdir -p _site

# Copy all necessary assets
cp -r index.html _site/
cp -r style.css _site/
cp -r main.js _site/

# Copy image directory if exists
if [ -d "images" ]; then
    cp -r images _site/
fi

# Copy sitemap if exists
if [ -f "sitemap.xml" ]; then
    cp sitemap.xml _site/
fi

echo "Build complete. Files copied to _site/ directory."
