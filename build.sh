#!/bin/bash

# Generate site from data/sample_products.json (34 products)
rm -rf _site
node generate-pages.js
echo "Generated site with $(node -e "console.log(require('./data/sample_products.json').length)") products. Build done."