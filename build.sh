#!/bin/bash

rm -rf _site
mkdir -p _site/images
cp -r images/* _site/images/ 2>/dev/null || true
cp style.css _site/
cp main.js _site/
cp index.html _site/

echo "Build done."