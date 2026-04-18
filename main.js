// Load products and render based on URL
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('data/sample_products.json');
    const products = await response.json();

    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    if (id) {
      const product = products.find(p => p.id === id);
      if (product) {
        renderDetail(product, products);
      } else {
        renderGrid(products);
      }
    } else {
      renderGrid(products);
    }
  } catch (error) {
    console.error('Failed to load products:', error);
    document.getElementById('app').innerHTML = '<p>Products temporarily unavailable. Please refresh.</p>';
  }
});

// Render grid view
function renderGrid(products) {
  document.title = 'WorthIt Goods - Curated Premium Products';
  const app = document.getElementById('app');
  app.innerHTML = `
    <section class="products-section">
      <div class="filter-bar">
        <input type="text" id="searchProducts" placeholder="Search products...">
        <select id="categoryFilter">
          <option value="">All Categories</option>
          <option value="Electronics">Electronics</option>
          <option value="Smart Home">Smart Home</option>
          <option value="Wearables">Wearables</option>
          <option value="Security">Security</option>
          <option value="Home">Home</option>
        </select>
      </div>
      <div id="product-grid" class="products-grid"></div>
    </section>
  `;

  const grid = document.getElementById('product-grid');
  grid.innerHTML = products.map(productCard).join('');

  setupFilters(products);
}

// Render detail view
function renderDetail(product, products) {
  document.title = `${product.title} | WorthIt Goods`;
  const app = document.getElementById('app');
  app.innerHTML = `
    <div class="breadcrumb">
      <a href="/">Home</a> › ${product.category || 'Products'}
    </div>
    <article class="product-detail">
      <div class="product-hero">
        <img src="${product.image}" alt="${product.title}" class="hero-img">
        <aside class="hero-sidebar">
          <h1>${product.title}</h1>
          <div class="rating-line">
            <span class="stars">⭐ ${product.rating}</span>
            <span class="review-count">(${Math.floor(Math.random() * 500 + 100)} reviews)</span>
          </div>
          <div class="badges">
            ${product.badges.map(b => `<span class="badge">${b}</span>`).join('')}
          </div>
          <div class="price-large">${product.currency} ${product.price.toLocaleString()}</div>
          <a href="${product.affiliate_url}" class="buy-btn" target="_blank" rel="nofollow noopener">Buy Now</a>
          <p class="disclosure">As an Amazon Associate, we earn from qualifying purchases. Prices may vary.</p>
        </aside>
      </div>
      <section class="product-specs">
        <h2>Why Buy This?</h2>
        <p>${product.description}</p>
        <table>
          <tr><td>Rating</td><td>${product.rating}/5</td></tr>
          <tr><td>Category</td><td>${product.category}</td></tr>
          <tr><td>Shipping</td><td>${product.badges.includes('Free Shipping') ? 'Free' : 'Standard'}</td></tr>
        </table>
      </section>
      <section class="related-products">
        <h2>You May Also Like</h2>
        <div class="products-grid">
          ${products.filter(p => p.id !== product.id).slice(0,4).map(productCard).join('')}
        </div>
      </section>
    </article>
  `;
}

// Product card HTML template
function productCard(product) {
  return `
    <div class="product-card" data-category="${product.category}" data-rating="${product.rating}">
      <div class="image-wrapper">
        <img src="${product.image}" alt="${product.title}" loading="lazy">
      </div>
      <div class="content">
        <h3>${product.title}</h3>
        <div class="badges">
          ${product.badges.map(b => `<span class="badge">${b}</span>`).join('')}
        </div>
        <p class="price">${product.currency} ${product.price.toLocaleString()}</p>
        <p class="teaser">${product.description.substring(0,80)}...</p>
        <a href="?id=${product.id}" class="cta">View Details</a>
      </div>
    </div>
  `;
}

// Filter and search
function setupFilters(products) {
  const searchInput = document.getElementById('searchProducts');
  const categoryFilter = document.getElementById('categoryFilter');
  const grid = document.getElementById('product-grid');

  function filterProducts() {
    const search = searchInput.value.toLowerCase();
    const category = categoryFilter.value;
    const filtered = products.filter(p => 
      p.title.toLowerCase().includes(search) && 
      (!category || p.category === category)
    );
    grid.innerHTML = filtered.map(productCard).join('');
  }

  searchInput.addEventListener('input', filterProducts);
  categoryFilter.addEventListener('change', filterProducts);
}

// Trust badges
document.querySelectorAll('.trust-badge').forEach(badge => {
  badge.addEventListener('click', () => {
    const info = badge.dataset.info || 'Premium quality guaranteed';
    alert(info);
  });
});
