import json
import os
from pathlib import Path

# Absolute paths
base_dir = Path('/home/ubuntu/.openclaw/workspace/test-affiliate-site')
products_path = base_dir / 'sample_products.json'
site_dir = base_dir / '_site'

# Ensure directories
site_dir.mkdir(exist_ok=True)
images_dir = site_dir / 'images'
images_dir.mkdir(exist_ok=True)

# Read products
with open(products_path, 'r') as f:
    products = json.load(f)

def slugify(title):
    return title.lower().replace(' ', '-').replace('[^a-z0-9-]', '').strip('-')

def generate_grid_html(products):
    return ''.join([
        f'''
        <div class="product-card" data-category="{p.get('category', 'general')}" data-id="{p["id"]}">
          <div class="image-wrapper">
            <img src="{p["image"]}" alt="{p["title"]}" loading="lazy">
          </div>
          <div class="content">
            <h3>{p["title"]}</h3>
            {"".join([f"<span class="badge">{b}</span>" for b in p.get("badges", [])])}
            <p class="price">{p["currency"]} ${p["price"]:.2f}</p>
            <p class="teaser">{p["description"][:120]}...</p>
            <a href="product-{slugify(p["title"])}.html" class="cta">View Details</a>
          </div>
        </div>
        ''' for p in products
    ])

# Index HTML with hero, nav, trust bar
index_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WorthIt Goods - Curated Premium Products</title>
  <meta name="description" content="Discover curated premium products with honest reviews and exclusive deals. WorthIt Goods helps you make smarter purchases.">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="hero">
    <nav class="navbar">
      <a href="/" class="logo">WorthIt Goods</a>
      <ul class="nav-links">
        <li><a href="/">Home</a></li>
        <li><a href="#products">Shop All</a></li>
        <li><a href="#reviews">Reviews</a></li>
        <li><a href="#about">About</a></li>
      </ul>
    </nav>
    <div class="hero-content">
      <h1>Upgrade Your Routine with WorthIt Goods</h1>
      <p>Premium products tested by experts. Always ready to buy.</p>
      <div class="search-bar">
        <input type="text" id="searchProducts" placeholder="Search products...">
      </div>
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
    <p><a href="#privacy">Privacy Policy</a> | <a href="#disclosure">Affiliate Disclosure</a> | <a href="#terms">Terms</a></p>
  </footer>
  <script src="main.js"></script>
</body>
</html>'''

with open(site_dir / 'index.html', 'w') as f:
    f.write(index_html)

# Detail page
detail_template = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | WorthIt Goods</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="hero">
    <nav class="navbar">
      <a href="/" class="logo">WorthIt Goods</a>
    </nav>
  </header>
  <div class="product-detail">
    <div class="breadcrumb">
      <a href="/">Home</a> > {category}
    </div>
    <div class="product-hero">
      <img src="{image}" alt="{title}">
      <div class="hero-info">
        <h1>{title}</h1>
        <div class="rating">⭐ {rating} <span>(1,234 reviews)</span></div>
        <div class="badges">
{ badges }
        </div>
        <div class="price-large">{currency} ${price:.2f}</div>
        <a href="{url}" class="buy-btn" target="_blank">Buy Now</a>
        <p class="disclosure">As an Amazon Associate we earn from qualifying purchases.</p>
      </div>
    </div>
    <section class="product-content">
      <h2>Description</h2>
      <p>{desc}</p>
    </section>
  </div>
  <footer class="site-footer">
    <p>&copy; 2026 WorthIt Goods.</p>
  </footer>
</body>
</html>'''

for p in products:
    slug = slugify(p['title'])
    badges = ''.join([f'<span class="badge">{b}</span>' for b in p.get('badges', [])])
    detail = detail_template.format(
        title=p['title'],
        desc=p['description'][:300] + '...',
        category=p.get('category', 'Electronics'),
        image=p['image'],
        rating=p['rating'],
        badges=badges,
        currency=p['currency'],
        price=p['price'],
        url=p['affiliate_url']
    )
    with open(site_dir / f'product-{slug}.html', 'w') as f:
        f.write(detail)

# Copy assets
for asset in ['style.css', 'main.js']:
    if os.path.exists(base_dir / asset):
        (site_dir / asset).write_bytes((base_dir / asset).read_bytes())

print(f'Generated {len(products)} pages in {site_dir}')
