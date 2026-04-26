#!/bin/bash

# Generate site from data/sample_products.json
rm -rf _site
node generate-pages.js

# === NEW: Copy the latest style.css into _site so changes take effect ===
cp style.css _site/

echo "Generated site with $(node -e "console.log(require('./data/sample_products.json').length)") products. Clean top-tier layout complete."
echo "Build done. (style.css copied to _site)"
