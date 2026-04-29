#!/bin/bash

# Generate site from data/sample_products.json
rm -rf _site
mkdir -p _site/blog
mkdir -p _site/blog

node generate-pages.js
node generate-blogs.js
node generate-blog-index.js

# Copy blogs MD to _site/blog for direct serving (readable raw MD)
cp blog/*.md _site/blog/ || echo "No blog MD to copy"

# Copy style.css
cp style.css _site/

# Simple blog list update in blog.html (manual for now)
sed -i 's|<!-- New posts.*||' blog.html || true


echo "Generated site with $(node -e "console.log(require('./data/sample_products.json').length)") products."
echo "Blogs copied to _site/blog/ for direct links."
echo "Build done."
