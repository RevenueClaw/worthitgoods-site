#!/bin/bash
set -e

echo "Starting build..."

# Create output directory
rm -rf _site
mkdir -p _site/images
mkdir -p _site

# Copy all static assets
cp -r images/* _site/images/ 2>/dev/null || true
cp style.css _site/
cp main.js _site/
cp index.html _site/ # we'll make index.html self-contained

echo "Assets copied."

# If index.html is missing or broken, create a minimal working one with the grid
if [ ! -s _site/index.html ] || ! grep -q "products-grid" _site/index.html; then
 echo "Creating simple index.html with grid..."
 cat > _site/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8">
 <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <title>WorthItGoods - Products Worth Buying</title>
 <link rel="stylesheet" href="style.css">
</head>
<body>
 <header>
 <h1>Worth It Goods</h1>
 <p>Curated products that are actually worth it</p>
 </header>

 <div class="products-grid">
 <!-- PLACEHOLDER CARDS START -->
 </div>

 <script src="main.js"></script>
</body>
</html>
EOF
fi

echo "Build completed successfully."