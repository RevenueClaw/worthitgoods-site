const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const siteDir = '_site';

if (!fs.existsSync(siteDir)) fs.mkdirSync(siteDir, { recursive: true });

// Read products
const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));

// Generate clean index.html
const indexHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WorthIt Goods • Products Actually Worth Buying</title>
    <style>
        :root { --accent: #16a34a; --dark: #1f2937; }
        * { box-sizing: border-box; margin:0; padding:0; }
        body { font-family: system-ui, sans-serif; line-height: 1.6; color: #333; background: #f8fafc; }
        
        .hero { background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; text-align: center; padding: 100px 20px 80px; }
        .hero h1 { font-size: 2.9rem; margin-bottom: 16px; line-height: 1.1; }
        .hero p { font-size: 1.35rem; max-width: 720px; margin: 0 auto 30px; opacity: 0.95; }
        .cta-button { background: white; color: var(--dark); padding: 16px 36px; border-radius: 50px; font-weight: 600; text-decoration: none; display: inline-block; font-size: 1.1rem; }

        .products-section { padding: 70px 20px; }
        .section-title { text-align: center; font-size: 2.4rem; margin-bottom: 45px; color: var(--dark); }

        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
            gap: 30px;
            max-width: 1300px;
            margin: 0 auto;
        }

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
        .product-card:hover { transform: translateY(-12px); box-shadow: 0 20px 40px rgba(0,0,0,0.18); }
        .product-card img { width: 100%; height: 235px; object-fit: cover; }
        .content { padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }
        .content h3 { font-size: 1.3rem; margin-bottom: 12px; line-height: 1.3; }
        .content p { color: #555; margin-bottom: 20px; flex-grow: 1; font-size: 0.98rem; }
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

        footer { background: #1f2937; color: #ccc; text-align: center; padding: 50px 20px 40px; font-size: 0.95rem; }
    </style>
</head>
<body>

    <div class="hero">
        <h1>Curated Products That Are <span style="color:#fcd34d">Actually Worth It</span></h1>
        <p>No junk. No hype. Just honest, hand-picked recommendations for gear that genuinely improves daily life.</p>
        <a href="#products" class="cta-button">Browse All Worth-It Picks</a>
    </div>

    <section id="products" class="products-section">
        <h2 class="section-title">Our Latest Worth-It Picks</h2>
        <div class="products-grid">
            ${products.map(p => `
            <div class="product-card">
                <img src="${p.image}" alt="${p.title}">
                <div class="content">
                    <h3>${p.title}</h3>
                    <p>${p.description}</p>
                    <a href="${p.affiliate_url}" class="cta" target="_blank" rel="nofollow">Shop on Amazon</a>
                </div>
            </div>`).join('')}
        </div>
    </section>

    <footer>
        <p>&copy; 2026 WorthIt Goods. All rights reserved.</p>
        <p>As an Amazon Associate, I earn from qualifying purchases. This does not affect the price you pay.</p>
    </footer>

</body>
</html>`;

fs.writeFileSync(path.join(siteDir, 'index.html'), indexHTML);
console.log(`Generated site with ${products.length} products. Clean top-tier layout complete.`);
