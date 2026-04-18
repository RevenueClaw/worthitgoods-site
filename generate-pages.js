const fs = require('fs');
const path = require('path');

const productsDataPath = 'sample_products.json';
const siteDir = '_site';
const templateDir = 'templates'; // Optional, for now inline templates

// Ensure directories
if (!fs.existsSync(siteDir)) fs.mkdirSync(siteDir, { recursive: true });
if (!fs.existsSync('images')) fs.mkdirSync('images', { recursive: true });

// Read products
const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));

// Slugify function
function slugify(title) {
  return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// Grid template for index.html
function generateGridHTML(products) {
  return products.map(product => `
    <div class="product-card" data-category="${product.category || 'general'}" data-id="${product.id}">
      <div class="image-wrapper">
        <img src="${product.image || 'images/placeholder.jpg'}" alt="${product.title}" loading="lazy">
      </div>
      <div class="content">
        <h3>${product.title}</h3>
        <div class="badges">
          ${product.badges ? product.badges.map(b => `<span class="badge">${b}</span>`).join('') : ''}
        </div>
        <p class="price">${product.currency} ${product.price.toLocaleString()}</p>
        <p class="teaser">${product.description.substring(0, 100)}...</p>
        <a href="product-${slugify(product.title)}.html" class="cta">View Details</a>
      </div>
    </div>
  `).join('\n');
}

// Detail template
function generateDetailHTML(product, relatedProducts) {
  const related = relatedProducts.slice(0, 3).map(p => `
    <div class="related-card">
      <img src="${p.image}" alt="${p.title}">
      <h4>${p.title}</h4>
      <a href="product-${slugify(p.title)}.html">View</a>
    </div>
  `).join('');

  const benefits = product.description.split('. ').slice(0, 3).map(b => `<li>${b}</li>`).join('');
  const specs = [
    `Rating: ${product.rating}/5`,
    `Category: ${product.category}`,
    `Free Shipping: ${product.badges?.includes('Free Shipping') ? 'Yes' : 'No'}`
  ].map(s => `<tr><td>${s}</td></tr>`).join('');

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${product.title} | WorthIt Goods</title>
  <meta name="description" content="${product.description.substring(0, 160)}">
  <meta property="og:title" content="${product.title}">
  <meta property="og:description" content="${product.description.substring(0, 160)}">
  <meta property="og:image" content="${product.image}">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "${product.title}",
    "image": "${product.image}",
    "description": "${product.description}",
    "offers": {
      "@type": "Offer",
      "price": "${product.price}",
      "priceCurrency": "${product.currency}"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "${product.rating}",
      "bestRating": "5"
    }
  }
  </script>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="hero">
    <nav class="navbar">
      <a href="/" class="logo">WorthIt Goods</a>
      <ul class="nav-links">
        <li><a href="/">Home</a></li>
        <li><a href="/#categories">Categories</a></li>
        <li><a href="/#reviews">Reviews</a></li>
      </ul>
    </nav>
  </header>
  <main class="product-detail">
    <nav class="breadcrumb">
      <a href="/">Home</a> > <span>${product.category}</span>
    </nav>
    <div class="product-hero">
      <img src="${product.image}" alt="${product.title}" class="hero-img">
      <div class="hero-info">
        <h1>${product.title}</h1>
        <div class="rating">⭐ ${product.rating} (${Math.floor(Math.random() * 1000 + 100)} reviews)</div>
        <div class="badges">
          ${product.badges ? product.badges.map(b => `<span class="badge">${b}</span>`).join('') : ''}
        </div>
        <div class="price-large">${product.currency} ${product.price.toLocaleString()}</div>
        <a href="${product.affiliate_url}" class="buy-btn" target="_blank" rel="nofollow noopener">Buy Now (via Amazon)</a>
        <p class="disclosure">As an Amazon Associate, we earn from qualifying purchases. Prices and availability may change.</p>
      </div>
    </div>
    <section class="product-content">
      <h2>Why It's Worth It</h2>
      <ul>${benefits}</ul>
      <h2>Specifications</h2>
      <table>${specs}</table>
      <h2>Customer Reviews</h2>
      <div class="reviews">
        <div class="review">
          <p>⭐ 5/5 - "Amazing quality, exceeded expectations!"</p>
          <span>John D.</span>
        </div>
        <div class="review">
          <p>⭐ 4.8/5 - "Perfect for my needs, fast delivery."</p>
          <span>Sarah K.</span>
        </div>
      </div>
    </section>
    <section class="related-products">
      <h2>You May Also Like</h2>
      <div class="products-grid">
        ${related}
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <p>&copy; 2026 WorthIt Goods. All rights reserved.</p>
    <p><a href="/privacy.html">Privacy</a> | <a href="/disclosure.html">Affiliate Disclosure</a></p>
  </footer>
  <script src="main.js"></script>
</body>
</html>`;
}

// Generate index.html
let indexHTML = `<!DOCTYPE html>
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
        <li><a href="#categories">Categories</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#blog">Blog</a></li>
      </ul>
    </nav>
    <div class="hero-content">
      <h1>Curated Premium Products That Are Actually Worth It</h1>
      <p>Expert-tested gear for better living. Honest reviews, exclusive deals.</p>
      <div class="search-bar">
        <input type="text" id="searchProducts" placeholder="Search 100+ premium products...">
      </div>
    </div>
    <div class="trust-bar">
      <div class="trust-badge">🔒 SSL Secured</div>
      <div class="trust-badge">⭐ Verified Reviews</div>
      <div class="trust-badge">🏆 Top-Rated Products</div>
    </div>
  </header>
  <section class="categories" id="categories">
    <h2>Shop by Category</h2>
    <div class="category-tags">
      Electronics, Smart Home, Wearables, Security, Home
    </div>
  </section>
  <section id="products" class="products-grid">
    ${generateGridHTML(products)}
  </section>
  <section id="reviews" class="reviews">
    <h2>What Customers Say</h2>
    <div class="review-grid">
      <div class="review-card">
        <p>"Best selection of premium gear. Honest reviews made my decision easy."</p>
        <span>– Sarah K., Verified Buyer</span>
      </div>
      <div class="review-card">
        <p>"Finally a site that cuts through the noise. Everything here is worth buying."</p>
        <span>– Mark T., 5⭐</span>
      </div>
    </div>
  </section>
  <footer class="site-footer">
    <div class="footer-content">
      <div class="newsletter">
        <h3>Stay Updated</h3>
        <p>Get weekly deals delivered to your inbox.</p>
        <form>
          <input type="email" placeholder="your@email.com">
          <button type="submit">Subscribe</button>
        </form>
      </div>
      <div class="footer-links">
        <a href="/privacy.html">Privacy Policy</a>
        <a href="/terms.html">Terms</a>
        <a href="/disclosure.html">Affiliate Disclosure</a>
      </div>
      <div class="social">
        Twitter Facebook Instagram
      </div>
    </div>
    <p>&copy; 2026 WorthIt Goods. All rights reserved.</p>
  </footer>
  <script src="main.js"></script>
</body>
</html>`;

fs.writeFileSync(path.join(siteDir, 'index.html'), indexHTML);

// Generate detail pages
products.forEach((product, index) => {
  const related = products.filter(p => p.id !== product.id);
  const detailHTML = generateDetailHTML(product, related);
  const slug = slugify(product.title);
  fs.writeFileSync(path.join(siteDir, `product-${slug}.html`), detailHTML);
});

// Copy assets
['style.css', 'main.js', 'sitemap.xml'].forEach(file => {
  if (fs.existsSync(file)) {
    fs.copyFileSync(file, path.join(siteDir, file));
  }
});

if (fs.existsSync('images')) {
  fs.cpSync('images', path.join(siteDir, 'images'), { recursive: true });
}

console.log(`Generated site with ${products.length} products. Check _site/ directory.`);
