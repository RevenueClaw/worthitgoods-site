const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const siteDir = '_site';

if (!fs.existsSync(siteDir)) {
    fs.mkdirSync(siteDir, { recursive: true });
}

// Read products
const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));

// Generate improved index.html
const indexHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WorthIt Goods • Products Actually Worth Buying</title>
    <style>
        :root {
            --accent: #16a34a;
            --dark: #1f2937;
            --light: #f8fafc;
        }
        * { box-sizing: border-box; margin:0; padding:0; }
        body { 
            font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            background: var(--light); 
        }
        
        /* Hero - Stronger & More Branded */
        .hero { 
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            color: white; 
            text-align: center; 
            padding: 120px 20px 100px; 
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: url('https://picsum.photos/id/1077/2000/1200') center/cover no-repeat;
            opacity: 0.15;
            z-index: 0;
        }
        .hero-content {
            position: relative;
            z-index: 1;
            max-width: 780px;
            margin: 0 auto;
        }
        .hero h1 { 
            font-size: 3.1rem; 
            margin-bottom: 18px; 
            line-height: 1.05;
            font-weight: 700;
        }
        .hero p { 
            font-size: 1.4rem; 
            max-width: 680px; 
            margin: 0 auto 32px; 
            opacity: 0.95;
        }
        .cta-button { 
            background: white; 
            color: var(--dark); 
            padding: 16px 40px; 
            border-radius: 50px; 
            font-weight: 700; 
            text-decoration: none; 
            display: inline-block; 
            font-size: 1.15rem; 
            transition: all 0.3s;
        }
        .cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }

        .products-section { padding: 80px 20px; }
        .section-title { 
            text-align: center; 
            font-size: 2.5rem; 
            margin-bottom: 50px; 
            color: var(--dark); 
        }

        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
            gap: 32px;
            max-width: 1320px;
            margin: 0 auto;
        }

        /* Product Cards - Unchanged from your approved version */
        .product-card {
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            height: 100%;
            transition: all 0.3s ease;
        }
        .product-card:hover { 
            transform: translateY(-12px); 
            box-shadow: 0 20px 40px rgba(0,0,0,0.18); 
        }

        .product-card .image-wrapper {
            height: 260px;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #ffffff;
            overflow: hidden;
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }

        .product-card img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            transition: transform 0.4s ease;
        }

        .product-card:hover img {
            transform: scale(1.07);
        }

        .content { 
            padding: 22px; 
            flex-grow: 1; 
            display: flex; 
            flex-direction: column; 
        }
        .content h3 { 
            font-size: 1.32rem; 
            margin-bottom: 12px; 
            line-height: 1.3; 
        }
        .content p { 
            color: #555; 
            margin-bottom: 22px; 
            flex-grow: 1; 
            font-size: 0.97rem; 
        }
        .cta {
            background: var(--accent);
            color: white;
            text-align: center;
            padding: 14px 24px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            margin-top: auto;
            display: block;
        }
        .cta:hover { background: #15803d; }

        /* Footer */
        footer { 
            background: #1f2937; 
            color: #aaa; 
            text-align: center; 
            padding: 60px 20px 40px; 
        }
        .footer-content {
            max-width: 1100px;
            margin: 0 auto 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 30px;
            text-align: left;
        }
        .footer-col h4 {
            color: white;
            margin-bottom: 12px;
        }
        footer a {
            color: #aaa;
            text-decoration: none;
        }
        footer a:hover { color: #60a5fa; }

        .copyright {
            border-top: 1px solid #374151;
            padding-top: 25px;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>

    <div class="hero">
        <div class="hero-content">
            <h1>WorthIt Goods</h1>
            <p>Honest, hand-picked products that actually deliver.<br>No junk. No hype. Just gear worth your money and time.</p>
            <a href="#products" class="cta-button">Browse Worth-It Picks</a>
        </div>
    </div>

    <section id="products" class="products-section">
        <h2 class="section-title">Our Latest Worth-It Picks</h2>
        <div class="products-grid">
            ${products.map(p => `
                <div class="product-card">
                    <div class="image-wrapper">
                        <img src="${p.image}" alt="${p.title}">
                    </div>
                    <div class="content">
                        <h3>${p.title}</h3>
                        <p>${p.description}</p>
                        <a href="${p.affiliate_url}" class="cta" target="_blank" rel="nofollow">Shop on Amazon</a>
                    </div>
                </div>
            `).join('')}
        </div>
    </section>

    <footer>
        <div class="footer-content">
            <div class="footer-col">
                <h4>WorthIt Goods</h4>
                <p>Curated recommendations for products that genuinely improve daily life.</p>
            </div>
            <div class="footer-col">
                <h4>Quick Links</h4>
                <p><a href="#products">All Products</a></p>
            </div>
            <div class="footer-col">
                <h4>Legal</h4>
                <p><a href="#">Privacy</a></p>
                <p><a href="#">Affiliate Disclosure</a></p>
            </div>
        </div>
        <div class="copyright">
            <p>© 2026 WorthIt Goods. All rights reserved.</p>
            <p>As an Amazon Associate, I earn from qualifying purchases. Prices and availability are subject to change.</p>
        </div>
    </footer>

</body>
</html>`;

fs.writeFileSync(path.join(siteDir, 'index.html'), indexHTML);
console.log('Generated site with ' + products.length + ' products. Improved hero + polish applied.');
