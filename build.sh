#!/usr/bin/env bash
# Build script for Cloudflare Pages

# Create output directory
mkdir -p _site

# Copy all files to output directory
cp -r *.html *.css *.js _site/

# Copy image directory if exists
if [ -d "images" ]; then
    cp -r images _site/
fi

# Copy sitemap if exists
if [ -f "sitemap.xml" ]; then
    cp sitemap.xml _site/
fi

echo "Build complete. Files copied to _site/ directory."
