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

find _site -name '*.html' | head -5

find _site -name '*.html' | head -5
echo "\nBuild done. Toggles + 5 blog posts ready."
