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
        <div class="product-card" data-category="{p.get("category", "general")}" data-id="{p["id"]}">
          <div class="image-wrapper">
            <img src="{p["image"]}" alt="{p["title"]}" loading="lazy">
          </div>
          <div class="content">
            <h3>{p["title"]}</h3>
            {''.join([f'<span class="badge">{b}</span>' for b in p.get("badges", [])])}
            <p class="price">{p["currency"]} ${float(p["price"]):.2f}</p>
            <p class="teaser">{p["description"][:120]}...</p>
            <a href="product-{slugify(p["title"])}.html" class="cta">View Details</a>
          </div>
        </div>
        ''' for p in products
    ])

# Index HTML
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
        <li><a href="#products">Products</a></li>
        <li><a href="#reviews">Reviews</a></li>
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
    <p><a href="#privacy">Privacy</a> | <a href="#disclosure">Affiliate Disclosure</a></p>
  </footer>
  <script src="main.js"></script>
</body>
</html>'''

with open(site_dir / 'index.html', 'w') as f:
    f.write(index_html)

# Detail template
detail_template = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | WorthIt Goods</title>
  <meta name="description" content="{desc_short}">
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
        <div class="rating">⭐ {rating} ({reviews_count} reviews)</div>
        <div class="badges">
{badges_html}
        </div>
        <div class="price-large">{currency} ${price:.2f}</div>
        <a href="{affiliate_url}" class="buy-btn" target="_blank" rel="nofollow noopener">Buy Now</a>
        <p class="disclosure">As an Amazon Associate, we earn from qualifying purchases.</p>
      </div>
    </div>
    <section class="product-content">
      <h2>Why It's Worth It</h2>
      <ul class="benefits">
        <li>{benefit1}</li>
        <li>{benefit2}</li>
        <li>{benefit3}</li>
      </ul>
      <h2>Specifications</h2>
      <table class="specs">
        <tr><td>Rating</td><td>{rating}/5</td></tr>
        <tr><td>Category</td><td>{category}</td></tr>
        <tr><td>Free Shipping</td><td>{free_shipping}</td></tr>
      </table>
      <h2>Customer Reviews</h2>
      <div class="reviews-grid">
        <div class="review-card">
          <p>⭐ 5/5 - "Amazing quality!"</p>
          <span>John D.</span>
        </div>
        <div class="review-card">
          <p>⭐ 4.8/5 - "Perfect!"</p>
          <span>Sarah K.</span>
        </div>
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <p>&copy; 2026 WorthIt Goods.</p>
  </footer>
</body>
</html>'''

for p in products:
    slug = slugify(p['title'])
    filename = site_dir / f'product-{slug}.html'
    
    desc_short = p['description'][:160] + '...'
    badges_html = ''.join([f'<span class="badge">{b}</span>' for b in p.get('badges', [])])
    reviews_count = 150 + len(products) * 10
    sentences = p['description'].split('. ')[:3]
benefit1 = sentences[0] + '.' if len(sentences) > 0 else p['description'][:100] + '.'
benefit2 = sentences[1] + '.' if len(sentences) > 1 else 'High-quality and reliable.'
benefit3 = sentences[2] + '.' if len(sentences) > 2 else 'Customer favorite with great reviews.'
    free_shipping = 'Yes' if 'Free Shipping' in p.get('badges', []) else 'No'
    
    detail_content = detail_template.format(
        title=p['title'],
        desc_short=desc_short,
        category=p.get('category', 'Electronics'),
        image=p['image'],
        rating=p['rating'],
        reviews_count=reviews_count,
        badges_html=badges_html,
        currency=p['currency'],
        price=float(p['price']),
        affiliate_url=p['affiliate_url'],
        benefit1=benefit1,
        benefit2=benefit2,
        benefit3=benefit3,
        free_shipping=free_shipping
    )
    
    with open(filename, 'w') as f:
        f.write(detail_content)

# Copy assets
for asset in ['style.css', 'main.js', 'sitemap.xml']:
    if os.path.exists(base_dir / asset):
        (site_dir / asset).write_bytes((base_dir / asset).read_bytes())

print(f'Site generated with {len(products)} products. Deploy _site/ directory.')
