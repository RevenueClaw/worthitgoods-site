// Dynamic product renderer for WorthItGoods
// Loads sample_products.json, renders 24 products grid, search/filter, detail view via ?id=

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('sample_products.json');
    const products = await response.json();
    
    // Check for detail view
    const urlParams = new URLSearchParams(window.location.search);
    const productId = urlParams.get('id');
    
    if (productId) {
      const product = products.find(p => p.id === productId);
      if (product) {
        renderDetail(product, products);
        return;
      }
    }
    
    renderLanding(products);
  } catch (error) {
    console.error('Failed to load products:', error);
    // Static fallback: Do not overwrite grid
  }
});

function renderLanding(products) {
  document.title = 'WorthIt Goods - Curated Premium Products';
  
  const grid = document.querySelector('.products-grid');
  grid.innerHTML = products.map(productCard).join('');
  
  setupFilters(products);
}

function productCard(product) {
  return `
    <div class="product-card" data-category="${product.category || 'general'}" data-id="${product.id}">
      <div class="image-wrapper">
        <img src="${product.image}" alt="${product.title}" loading="lazy">
      </div>
      <div class="content">
        <div class="badges">
          ${product.badges.map(b => `<span class="badge">${b}</span>`).join('')}
        </div>
        <h3>${product.title}</h3>
        <p class="teaser">${product.description.substring(0, 100)}...</p>
        <p class="price">${product.currency} ${Number(product.price).toLocaleString()}</p>
        <a href="?id=${product.id}" class="cta">View Details</a>
      </div>
    </div>
  `;
}

function renderDetail(product, allProducts) {
  document.title = `${product.title} | WorthIt Goods`;
  
  const app = document.querySelector('.app-container') || document.body;
  app.innerHTML = `
    <div class="breadcrumb">
      <a href="/">Home</a> › ${product.category || 'Products'}
    </div>
    <article class="product-detail">
      <div class="product-hero">
        <img src="${product.image}" alt="${product.title}" class="hero-img">
        <div class="hero-info">
          <h1>${product.title}</h1>
          <div class="rating">⭐ ${product.rating} <span>(${Math.floor(Math.random() * 1000 + 100)} reviews)</span></div>
          <div class="badges">
            ${product.badges.map(b => `<span class="badge">${b}</span>`).join('')}
          </div>
          <div class="price-large">${product.currency} ${Number(product.price).toLocaleString()}</div>
          <a href="${product.affiliate_url}" class="buy-btn" target="_blank" rel="nofollow noopener">Buy Now</a>
          <p class="disclosure">As an Amazon Associate, we earn from qualifying purchases. Prices and availability may change.</p>
        </div>
      </div>
      <section class="product-content">
        <h2>Why It's Worth It</h2>
        <p>${product.description}</p>
        <table class="specs">
          <tr><td>Rating</td><td>${product.rating}/5</td></tr>
          <tr><td>Category</td><td>${product.category}</td></tr>
          <tr><td>Shipping</td><td>${product.badges.includes('Free Shipping') ? 'Free' : 'Standard'}</td></tr>
        </table>
        <h2>Customer Reviews</h2>
        <div class="reviews-grid">
          <div class="review-card">
            <p>⭐ 5/5 - "Amazing quality, exceeded expectations!"</p>
            <span>John D.</span>
          </div>
          <div class="review-card">
            <p>⭐ 4.8/5 - "Perfect for my needs, fast delivery."</p>
            <span>Sarah K.</span>
          </div>
        </div>
      </section>
      <section class="related-products">
        <h2>You May Also Like</h2>
        <div class="products-grid">
          ${allProducts.filter(p => p.id !== product.id).slice(0, 4).map(productCard).join('')}
        </div>
      </section>
    </article>
  `;
}

function setupFilters(products) {
  const searchInput = document.getElementById('searchProducts');
  const categoryFilter = document.getElementById('categoryFilter');
  
  function filterProducts() {
    const searchTerm = searchInput.value.toLowerCase();
    const category = categoryFilter ? categoryFilter.value : '';
    
    const filtered = products.filter(p => 
      p.title.toLowerCase().includes(searchTerm) &&
      (!category || p.category === category)
    );
    
    const grid = document.querySelector('.products-grid');
    grid.innerHTML = filtered.map(productCard).join('');
  }
  
  if (searchInput) searchInput.addEventListener('input', filterProducts);
  if (categoryFilter) categoryFilter.addEventListener('change', filterProducts);
}

// Trust badges
document.querySelectorAll('.trust-badge').forEach(badge => {
  badge.addEventListener('click', () => {
    const info = badge.dataset.info || 'Premium quality guaranteed';
    // Use modern notification instead of alert
    const toast = document.createElement('div');
    toast.textContent = info;
    toast.style.cssText = 'position:fixed;top:20px;right:20px;background:white;padding:1rem;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:9999;';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  });
});

// Newsletter form
document.querySelector('.newsletter-form')?.addEventListener('submit', (e) => {
  e.preventDefault();
  // Simulate subscription
  alert('Thanks for subscribing! Check your email.');
});