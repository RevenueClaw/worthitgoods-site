import json
import os
from pathlib import Path
import re

base_dir = Path('/home/ubuntu/.openclaw/workspace/test-affiliate-site')
products_path = base_dir / 'sample_products.json'
site_dir = base_dir / '_site'

site_dir.mkdir(exist_ok=True)
(images_dir := site_dir / 'images').mkdir(exist_ok=True)

with open(products_path, 'r') as f:
    products = json.load(f)

def slugify(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower().strip()).strip('-')

def generate_grid_html(products):
    cards = []
    for p in products:
        badges = ''.join([f'<span class="badge">{b}</span>' for b in p.get('badges', [])])
        cards.append(f'''
<div class="product-card">
  <div class="image-wrapper">
    <img src="{p["image"]}" alt="{p["title"]}" loading="lazy">
  </div>
  <div class="content">
    <div class="badges">{badges}</div>
    <h3>{p["title"]}</h3>
    <p class="teaser">{p["description"][:120]}...</p>
    <p class="price">{p["currency"]} {p["price"]:.0f}</p>
    <a href="product-{slugify(p["title"])}.html" class="cta">View Details</a>
  </div>
</div>''')
    return ''.join(cards)

index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WorthIt Goods - Curated Premium Products</title>
  <meta name="description" content="Discover curated premium products with honest reviews and exclusive deals.">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="hero">
    <nav class="navbar">
      <a href="/" class="logo">WorthIt Goods</a>
      <ul class="nav-links">
        <li><a href="/">Home</a></li>
        <li><a href="#products">Products</a></li>
        <li><a href="#reviews">Reviews</a></li>
      </ul>
    </nav>
    <div class="hero-content">
      <h1>Curated Premium Products That Are Actually Worth It</h1>
      <p>Expert-tested gear for better living. Honest reviews, exclusive deals.</p>
    </div>
    <div class="trust-bar">
      <div class="trust-badge">🔒 SSL Secured</div>
      <div class="trust-badge">⭐ Verified Reviews</div>
      <div class="trust-badge">🏆 Top-Rated Products</div>
    </div>
  </header>
  <section id="products" class="products-grid">
    {generate_grid_html(products)}
  </section>
  <section id="reviews" class="reviews">
    <h2>What Customers Say</h2>
    <div class="review-grid">
      <div class="review-card">
        <p>"Best selection of premium gear. Honest reviews made my decision easy."</p>
        <span>– Sarah K.</span>
      </div>
      <div class="review-card">
        <p>"Finally a site that cuts through the noise. Everything here is worth buying."</p>
        <span>– Mark T.</span>
      </div>
    </div>
  </section>
  <footer class="site-footer">
    <p>&copy; 2026 WorthIt Goods. All rights reserved.</p>
    <p><a href="/disclosure.html">Affiliate Disclosure</a></p>
  </footer>
</body>
</html>'''

with open(site_dir / 'index.html', 'w') as f:
    f.write(index_html)

detail_template = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | WorthIt Goods</title>
  <meta name="description" content="{desc_short}">
  <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{title}",
  "image": "{image}",
  "description": "{desc}",
  "offers": {{
    "@type": "Offer",
    "price": "{price}",
    "priceCurrency": "{currency}"
  }},
  "aggregateRating": {{
    "@type": "AggregateRating",
    "ratingValue": "{rating}",
    "bestRating": "5"
  }}
}}
  </script>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="hero">
    <nav class="navbar">
      <a href="/" class="logo">WorthIt Goods</a>
    </nav>
  </header>
  <main class="product-detail">
    <div class="breadcrumb">
      <a href="/">Home</a> › {category}
    </div>
    <div class="product-hero">
      <img src="{image}" alt="{title}" class="hero-img">
      <div class="hero-info">
        <h1>{title}</h1>
        <div class="rating">⭐ {rating}</div>
        <div class="badges">{badges_html}</div>
        <div class="price-large">{currency} {price}</div>
        <a href="{affiliate_url}" class="buy-btn" target="_blank" rel="nofollow noopener">Buy Now</a>
        <p class="disclosure">As an Amazon Associate we earn from qualifying purchases.</p>
      </div>
    </div>
    <section class="product-content">
      <h2>Description</h2>
      <p>{desc}</p>
      <h2>Specifications</h2>
      <table class="specs">
        <tr><td>Rating</td><td>{rating}/5</td></tr>
        <tr><td>Category</td><td>{category}</td></tr>
      </table>
    </section>
  </main>
  <footer class="site-footer">
    <p>&copy; 2026 WorthIt Goods.</p>
  </footer>
</body>
</html>'''

for p in products:
    slug = slugify(p['title'])
    badges_html = ''.join([f'<span class="badge">{b}</span>' for b in p.get('badges', [])])
    desc_short = p['description'][:160] + '...'
    
    detail = detail_template.format(
        title=p['title'],
        desc_short=desc_short,
        desc=p['description'],
        image=p['image'],
        rating=p['rating'],
        badges_html=badges_html,
        currency=p['currency'],
        price=f'{p["price"]:.0f}',
        affiliate_url=p['affiliate_url'],
        category=p.get('category', 'Electronics')
    )
    (site_dir / f'product-{slug}.html').write_text(detail)

# Copy assets
for asset in ['style.css', 'main.js', 'sitemap.xml']:
    asset_path = base_dir / asset
    if asset_path.exists():
        (site_dir / asset).write_bytes(asset_path.read_bytes())

print(f'Generated site with {len(products)} products in {site_dir}')
