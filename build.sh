#!/bin/bash

# ── Seasonal theme auto-detect ──
# Priority: CLI --theme flag > .seasonal-active file > none
THEME=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --theme)
            THEME="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--theme back_to_school|fall_essentials|halloween|thanksgiving_host|holiday_gifts]"
            exit 1
            ;;
    esac
done

# If no --theme flag, check .seasonal-active
if [[ -z "$THEME" && -f .seasonal-active ]]; then
    THEME_FILE=".seasonal-active"
    THEME_TIMESTAMP=$(cat "$THEME_FILE")
    NOW=$(date +%s)
    AGE=$((NOW - THEME_TIMESTAMP))
    MAX_AGE=$((5 * 86400))
    if [[ $AGE -lt $MAX_AGE ]]; then
        # Theme is still active — read theme name from curate_seasonal.py or default
        if [[ -f .seasonal-theme-name ]]; then
            THEME=$(cat .seasonal-theme-name)
        else
            THEME="back_to_school"
        fi
        echo "🎨 Seasonal theme active: $THEME"
    fi
fi

# === SAFETY NET: Recover comparison/blog files that exist only in _site ===
# Published articles must always be committed to source directories (comparisons/ or blog/)
# but if anything was generated directly in _site, this prevents data loss on rebuild.
if [ -d "_site/comparisons" ]; then
    mkdir -p comparisons
    for f in _site/comparisons/*.html; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        if [ ! -f "comparisons/$base" ]; then
            cp "$f" "comparisons/$base"
            echo "⚠️  Recovered: comparisons/$base (was only in _site)"
        fi
    done
fi

# Generate site from data/sample_products.json
rm -rf _site
SEASONAL_THEME="$THEME" node generate-pages.js

# Copy style
cp style.css _site/

# Generate blogs
node generate-blogs.js

# Generate RSS feed
node generate-rss.js

# Generate Google Shopping product feed
python3 scripts/generate_google_shopping_feed.py

# Copy Google Shopping feed to _site
cp google_shopping_products.xml _site/

# Copy assets (css, images, etc.)
cp -r assets _site/

# Enforce exactly 9 cards before newsletter section
python3 scripts/enforce_blog_layout.py blog.html

# Copy blog
mkdir -p _site/blog
cp blog.html _site/
cp blog/*.html _site/blog/

# === Overlay with custom blog post (hand-crafted prose, real product images) ===
cp blog/custom-5-kitchen-tools.html _site/blog/2026-07-08-5-kitchen-tools.html

# Copy comparison pages
cp -r comparisons _site/comparisons/

# Blog overlay: 2026-07-19-home-office
cp blog/custom-2026-07-19-home-office.html _site/blog/2026-07-19-home-office.html

# Blog overlay: 2026-07-26-gift-ideas
cp blog/custom-2026-07-26-gift-ideas.html _site/blog/2026-07-26-gift-ideas.html

# Blog overlay: 2026-08-02-outdoor-trail
cp blog/custom-2026-08-02-outdoor-trail.html _site/blog/2026-08-02-outdoor-trail.html

# Copy privacy page
cp unsubscribe.html _site/
cp privacy.html _site/

# Google Search Console verification
cp googlef652381e8198d3b7.html _site/

# Bing Webmaster Tools verification
cp BingSiteAuth.xml _site/

# 404 page, robots.txt
cp 404.html _site/
cp robots.txt _site/

# Generate sitemap
TODAY=$(date -u +%Y-%m-%d)

cat > _site/sitemap.xml << 'XML_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://www.worthitgoods.com/</loc><priority>1.0</priority><lastmod>XML_TODAY</lastmod></url>
  <url><loc>https://www.worthitgoods.com/blog.html</loc><priority>0.9</priority><lastmod>XML_TODAY</lastmod></url>
  <url><loc>https://www.worthitgoods.com/feed.xml</loc><priority>0.8</priority><lastmod>XML_TODAY</lastmod></url>
  <url><loc>https://www.worthitgoods.com/privacy.html</loc><priority>0.3</priority><lastmod>XML_TODAY</lastmod></url>
  <url><loc>https://www.worthitgoods.com/unsubscribe</loc><priority>0.1</priority><lastmod>XML_TODAY</lastmod></url>
XML_EOF

sed -i "s/XML_TODAY/$TODAY/g" _site/sitemap.xml

for f in blog/*.html; do
  slug=$(basename "$f" .html)
  [[ $slug == custom-* ]] && continue
  # Use git log for lastmod date, fall back to file mtime
  LASTMOD=$(git log -1 --format=%aI "$f" 2>/dev/null | head -c 10 || stat -c %y "$f" | head -c 10)
  printf '  <url><loc>https://www.worthitgoods.com/blog/%s</loc><priority>0.7</priority><lastmod>%s</lastmod></url>\n' "$slug.html" "${LASTMOD:-$TODAY}" >> _site/sitemap.xml
done

for f in comparisons/*.html; do
  slug=$(basename "$f" .html)
  LASTMOD=$(git log -1 --format=%aI "$f" 2>/dev/null | head -c 10 || stat -c %y "$f" | head -c 10)
  printf '  <url><loc>https://www.worthitgoods.com/comparisons/%s</loc><priority>0.7</priority><lastmod>%s</lastmod></url>
' "$slug.html" "${LASTMOD:-$TODAY}" >> _site/sitemap.xml
done

echo '</urlset>' >> _site/sitemap.xml

echo "Sitemap: $(grep -c '<url>' _site/sitemap.xml) URLs"

# Submit sitemap to search engines
python3 scripts/submit_sitemap.py 2>&1 | tail -5

find _site -name '*.html' | wc -l | xargs -I{} echo "{} HTML pages built."