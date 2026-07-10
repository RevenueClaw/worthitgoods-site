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

# === Overlay with custom blog post (hand-crafted prose, real product images) ===
cp blog/custom-5-kitchen-tools.html _site/blog/2026-07-08-5-kitchen-tools.html

# Copy privacy page
cp unsubscribe.html _site/
cp privacy.html _site/

# Generate sitemap
cat > _site/sitemap.xml << 'XML_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://www.worthitgoods.com/</loc><priority>1.0</priority></url>
  <url><loc>https://www.worthitgoods.com/blog.html</loc><priority>0.9</priority></url>
  <url><loc>https://www.worthitgoods.com/privacy.html</loc><priority>0.3</priority></url>
  <url><loc>https://www.worthitgoods.com/unsubscribe</loc><priority>0.1</priority></url>
XML_EOF

for f in blog/*.html; do
  slug=$(basename "$f" .html)
  [[ $slug == custom-* ]] && continue
  printf '  <url><loc>https://www.worthitgoods.com/blog/%s</loc><priority>0.7</priority></url>\n' "$slug.html" >> _site/sitemap.xml
done

echo '</urlset>' >> _site/sitemap.xml

echo "Sitemap: $(grep -c '<url>' _site/sitemap.xml) URLs"

find _site -name '*.html' | wc -l | xargs -I{} echo "{} HTML pages built."