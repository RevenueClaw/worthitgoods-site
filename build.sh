#!/bin/bash

# Generate site from data/sample_products.json
rm -rf _site
node generate-pages.js

# Copy style
cp style.css _site/

# Generate blogs
node generate-blogs.js

# Copy assets (css, images, etc.)
cp -r assets _site/

# Copy blog
mkdir -p _site/blog
cp blog.html _site/
cp blog/*.html _site/blog/

# === Overwrite with hand-crafted blog post (prose, newsletter CTA, custom descriptions) ===
cp blog/custom-5-kitchen-tools.html _site/blog/2026-07-08-5-kitchen-tools.html
cp blog/custom-5-kitchen-tools.html blog/2026-07-08-5-kitchen-tools.html

find _site -name '*.html' | head -5

echo "\nBuild done. Toggles + 5 blog posts ready."