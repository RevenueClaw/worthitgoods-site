const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const siteDir = '_site';

if (!fs.existsSync(siteDir)) {
    fs.mkdirSync(siteDir, { recursive: true });
}

const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));

const indexHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WorthIt Goods • Products Actually Worth Buying</title>
    <style>
        :root { --accent: #16a34a; --dark: #1f2937; }
        * { box-sizing: border-box; margin:0; padding:0; }
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; background: #f8fafc; }
        
        header { background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; padding: 1.5rem 0; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        nav { max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.8rem; font-weight: 700; letter-spacing: -1px; }
        nav ul { display: flex; list-style: none; gap: 2rem; }
        nav a { color: white; text-decoration: none; font-weight: 500; transition: color 0.3s; }
        nav a:hover { color: #00d4ff; }
        
        .hero { background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('https://picsum.photos/id/1077/1920/1080') center/cover no-repeat; height: 90vh; min-height: 600px; display: flex; align-items: center; color: white; text-align: center; }
        .hero-content { max-width: 800px; margin: 0 auto; padding: 2rem; }
        .hero h1 { font-size: 3.5rem; margin-bottom: 1rem; line-height: 1.1; }
        .hero p { font-size: 1.4rem; margin-bottom: 2rem; opacity: 0.95; }
        .cta-button { background: #00d4ff; color: #1a1a1a; padding: 1rem 2.5rem; border-radius: 50px; font-size: 1.2rem; font-weight: 700; text-decoration: none; transition: all 0.3s; box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3); }
        .cta-button:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4); }

        .products-section { max-width: 1200px; margin: 4rem auto; padding: 0 2rem; }
        .section-header { text-align: center; margin-bottom: 3rem; }
        .section-header h2 { font-size: 2.8rem; margin-bottom: 0.5rem; }
        .section-header p { font-size: 1.2rem; color: #666; max-width: 600px; margin: 0 auto; }

        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 2rem; }
        .product-card { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); transition: transform 0.3s, box-shadow 0.3s; display: flex; flex-direction: column; height: 100%; }
        .product-card:hover { transform: translateY(-8px); box-shadow: 0 15px 35px rgba(0,0,0,0.12); }
        .product-card .image-wrapper { height: 220px; display: flex; align-items: center; justify-content: center; background-color: #ffffff; overflow: hidden; padding: 12px; border-bottom: 1px solid #f0f0f0; }
        .product-card img { width: 100%; height: 100%; object-fit: contain; transition: transform 0.4s ease; }
        .product-card:hover img { transform: scale(1.04); }
        .product-info { padding: 1.5rem; display: flex; flex-direction: column; flex-grow: 1; }
        .product-info h3 { font-size: 1.35rem; margin-bottom: 0.75rem; line-height: 1.3; color: #1a1a1a; }
        .product-info p { color: #666; font-size: 0.95rem; margin-bottom: 1.25rem; flex-grow: 1; }
        .view-product { background: #1a1a1a; color: white; padding: 0.85rem 1.8rem; border-radius: 50px; text-decoration: none; font-weight: 600; text-align: center; transition: all 0.3s; margin-top: auto; display: block; }
        .view-product:hover { background: #00d4ff; color: #1a1a1a; }

        footer { background: #1a1a1a; color: #aaa; padding: 3rem 0 1.5rem; margin-top: 4rem; }
        .footer-content { max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; }
        .footer-col h4 { color: white; margin-bottom: 1rem; font-size: 1.1rem; }
        .footer-col a { color: #aaa; text-decoration: none; display: block; margin-bottom: 0.5rem; }
        .footer-col a:hover { color: #00d4ff; }
        .copyright { text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #333; font-size: 0.9rem; }
    </style>
</head>
<body>

    <header>
      <nav>
        <a href="/" class="logo">WorthItGoods</a>
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/blog.html">Blog</a></li>
        </ul>
      </nav>
    </header>

    <div class="hero">
        <div class="hero-content">
            <h1>WorthIt Goods</h1>
            <p>Honest, hand-picked products that actually deliver.<br>No junk. No hype. Just gear worth your money and time.</p>
            <a href="#products" class="cta-button">Browse Worth-It Picks</a>
        </div>
    </div>

    <section id="products" class="products-section">
        <div class="section-header">
            <h2>Our Latest Worth-It Picks</h2>
            <p>Newest at top – curated for real value.</p>
        </div>
        <div class="product-grid">
            ${products.map(p => `
                <div class="product-card">
                    <div class="image-wrapper">
                        <img src="${p.image}" alt="${p.title}">
                    </div>
                    <div class="product-info">
                        <h3>${p.title}</h3>
                        <p class="short-desc">${p.description.substring(0, 220)}...</p>
                        <p class="full-desc" style="display: none;">${p.description}</p>
                        <button class="toggle-btn" onclick="this.parentElement.querySelector('.full-desc').style.display = this.parentElement.querySelector('.full-desc').style.display === 'block' ? 'none' : 'block'; this.textContent = this.textContent === 'Why It's Worth It →' ? 'Show less ↑' : 'Why It's Worth It →';">
                            Why It's Worth It →
                        </button>
                        <a href="${p.affiliate_url}" class="view-product" target="_blank" rel="nofollow">Shop on Amazon</a>
                    </div>
                </div>
            `).join('')}
        </div>
    </section>

    <footer>
        <div class="footer-content">
            <div class="footer-col">
                <h4>WorthItGoods</h4>
                <p>Curated products that deliver real value.</p>
            </div>
            <div class="footer-col">
                <h4>Quick Links</h4>
                <a href="/">Home</a>
                <a href="/blog.html">Blog</a>
            </a>
        </div>
        <div class="copyright">
            <p>© 2026 WorthIt Goods. As an Amazon Associate, I earn from qualifying purchases.</p>
        </div>
    </footer>

</body>
</html>`;

fs.writeFileSync(path.join(siteDir, 'index.html'), indexHTML);
console.log('Generated site with ' + products.length + ' products. Enhanced descriptions now collapsible.');