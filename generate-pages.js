const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const siteDir = '_site';

if (!fs.existsSync(siteDir)) {
    fs.mkdirSync(siteDir, { recursive: true });
}

const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));


function renderProduct(p) {
    return `
                <div class="product-card">
                    <div class="image-wrapper">
                        <img src="${p.image}" alt="${p.title}">
                    </div>
                    <div class="content">
                        <h3>${p.title}</h3>
                        
                        <!-- Short preview: blurb -->
                        <p class="short-desc">${(p.blurb || p.description.substring(0, 180)).replace(/\n/g, ' ').trim()}${p.blurb ? '' : '...'}</p>
                        
                        <!-- Full enhanced description -->
                        <p class="full-desc">${p.description}</p>
                        
                        <button class="toggle-btn" onclick="
                            const content = this.parentElement;
                            const short = content.querySelector('.short-desc');
                            const full = content.querySelector('.full-desc');
                            if (full.style.display === 'block') {
                                full.style.display = 'none';
                                short.style.display = 'block';
                                this.textContent = 'Why It\u2019s Worth It \u2192';
                            } else {
                                full.style.display = 'block';
                                short.style.display = 'none';
                                this.textContent = 'Show less \u2191';
                            }
                            ">
                            Why It\u2019s Worth It \u2192
                        </button>
                        
                        <a href="${p.affiliate_url}" class="cta" target="_blank" rel="nofollow">Shop on Amazon</a>
                    </div>
                </div>
            `;
}
const indexHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WorthIt Goods • Products Actually Worth Buying</title>

    <!-- Open Graph / Facebook -->
    <meta property="og:title" content="WorthIt Goods - Honest Curated Products Worth Buying">
    <meta property="og:description" content="Hand-picked products that are actually worth it. Honest reviews, comparisons, and buying advice.">
    <meta property="og:image" content="https://www.worthitgoods.com/assets/og-image.jpg?v=20260430">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="WorthItGoods - Honest Curated Products Worth Buying (Updated 2026-04-30 12:28 EDT)">
    <!-- FORCE COMMIT: OG image cache bust via alt/timestamp -->
    <meta property="og:url" content="https://www.worthitgoods.com">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="WorthItGoods">

    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="WorthIt Goods - Honest Curated Products Worth Buying">
    <meta name="twitter:description" content="Hand-picked products that are actually worth it.">
    <meta name="twitter:image" content="https://www.worthitgoods.com/assets/og-image.jpg?v=20260430">

    <link rel="stylesheet" href="/style.css">
    <style>
        :root { --accent: #16a34a; --dark: #1f2937; }
        * { box-sizing: border-box; margin:0; padding:0; }
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; color: #333; background: #f8fafc; }
        
        .hero { background: linear-gradient(135deg, #ff9a56, #ff6b6b, #4ecdc4, #ff9a56, #4ecdc4); background-size: 400% 400%; color: white; text-align: center; height: 45vh !important; min-height: 300px !important; padding: 2rem 1rem !important; position: relative; overflow: hidden; animation: gradient-shift 20s ease infinite; }
        .hero-content { position: relative; z-index: 1; max-width: 780px; margin: 0 auto; }
        .hero h1 { font-size: 3.1rem; margin-bottom: 18px; line-height: 1.05; font-weight: 700; }
        .hero p { font-size: 1.4rem; max-width: 680px; margin: 0 auto 32px; opacity: 0.95; }
        .cta-button { background: white; color: var(--dark); padding: 16px 40px; border-radius: 50px; font-weight: 700; text-decoration: none; display: inline-block; font-size: 1.15rem; transition: all 0.3s; }
        .cta-button:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0,0,0,0.15); }

        /* Gradient morph — subtle, elegant color flow */
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        /* Diagonal light sweep — single soft ray moving across */
        .hero::after {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.06) 45%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.06) 55%, transparent 70%);
            background-size: 200% 100%;
            animation: light-sweep 8s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        @keyframes light-sweep {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        /* Newsletter signup — polished card */
        .newsletter-section {
            background: white;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            padding: 50px 40px;
            text-align: center;
            max-width: 700px;
            margin: -40px auto 50px;
            position: relative;
            z-index: 2;
            border: 1px solid rgba(0,0,0,0.04);
        }
        .newsletter-section .nl-icon {
            width: 56px; height: 56px;
            background: linear-gradient(135deg, #ff9a56, #ff6b6b);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 18px;
            font-size: 24px;
        }
        .newsletter-section h2 { font-size: 1.6rem; margin-bottom: 8px; color: var(--dark); }
        .newsletter-section p { font-size: 1rem; color: #6b7280; margin-bottom: 24px; max-width: 480px; margin-left: auto; margin-right: auto; }
        .newsletter-form { display: flex; gap: 8px; max-width: 440px; margin: 0 auto; }
        .newsletter-form input[type="email"] {
            flex: 1; padding: 13px 18px; border: 2px solid #e5e7eb; border-radius: 10px;
            font-size: 0.95rem; outline: none; transition: border-color 0.2s; font-family: inherit;
        }
        .newsletter-form input[type="email"]:focus { border-color: #ff6b6b; }
        .newsletter-form button {
            background: linear-gradient(135deg, #ff9a56, #ff6b6b);
            color: white; border: none; padding: 13px 28px; border-radius: 10px;
            font-size: 0.95rem; font-weight: 600; cursor: pointer;
            transition: all 0.3s; white-space: nowrap; font-family: inherit;
        }
        .newsletter-form button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255,107,107,0.3);
        }
        .newsletter-msg { margin-top: 14px; font-size: 0.9rem; min-height: 22px; }
        .newsletter-msg.error { color: #dc2626; }
        .newsletter-msg.success { color: #16a34a; }
        .nl-guarantee { font-size: 0.82rem; color: #9ca3af; margin-top: 14px; }

        .products-section { padding: 80px 20px; }
        .section-title { text-align: center; font-size: 2.5rem; margin-bottom: 50px; color: var(--dark); }

        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
            gap: 32px;
            max-width: 1320px;
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
        .product-card:hover img { transform: scale(1.07); }

        .content { 
            padding: 22px; 
            flex-grow: 1; 
            display: flex; 
            flex-direction: column; 
        }
        .content h3 { font-size: 1.32rem; margin-bottom: 12px; line-height: 1.3; }
        
        /* Short description shown by default */
        .short-desc {
            color: #555;
            margin-bottom: 18px;
            flex-grow: 1;
            font-size: 0.97rem;
            min-height: 4em;
            line-height: 1.5;
        }

        /* Full enhanced description - hidden until toggled */
        .full-desc {
            display: none;
            color: #444;
            font-size: 0.97rem;
            line-height: 1.65;
            margin: 1rem 0 18px 0;
        }

        .toggle-btn {
            background: none;
            border: none;
            color: var(--accent);
            font-weight: 600;
            cursor: pointer;
            padding: 4px 0;
            text-align: left;
            font-size: 0.95rem;
        }
        .toggle-btn:hover { text-decoration: underline; }

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

        footer { background: #1f2937; color: #aaa; text-align: center; padding: 60px 20px 40px; }
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

        <section id="products" class="products-section" style="padding-top: 20px;">
        <h2 class="section-title">Our Latest Worth-It Picks</h2>
        <div class="products-grid">
            ${products.slice(0, 12).map(p => renderProduct(p)).join('')}
        </div>

        <div class="newsletter-section">
            <div class="nl-icon">✉</div>
            <h2>Never Miss a Worth-It Find</h2>
            <p>New hand-picked picks every 2 weeks. Honest reviews, zero hype, unsubscribe anytime.</p>
            <form class="newsletter-form" id="wigNewsletterForm">
                <input type="email" id="newsletterEmail" placeholder="your@email.com" required>
                <button type="submit">Subscribe</button>
            </form>
            <div id="newsletterMsg" class="newsletter-msg"></div>
            <div class="nl-guarantee">No spam · Unsubscribe with 1 click · Hand-picked only</div>
        </div>

        <div class="products-grid">
            ${products.slice(12).map(p => renderProduct(p)).join('')}
        </div>
    </section>

    <script>
    document.getElementById('wigNewsletterForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const email = document.getElementById('newsletterEmail').value;
        const msg = document.getElementById('newsletterMsg');
        msg.className = 'newsletter-msg';
        msg.textContent = 'Subscribing...';
        try {
            const res = await fetch('http://192.168.4.127:9003/api/newsletter/signup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email})
            });
            const data = await res.json();
            if (data.success) {
                msg.className = 'newsletter-msg success';
                msg.textContent = data.message;
                document.getElementById('newsletterEmail').value = '';
            } else {
                msg.className = 'newsletter-msg error';
                msg.textContent = data.message;
            }
        } catch(err) {
            msg.className = 'newsletter-msg error';
            msg.textContent = 'Something went wrong. Please try again later.';
        }
    });
    </script>

    <footer>
        <p>© 2026 WorthIt Goods. All rights reserved.</p>
        <p>As an Amazon Associate, I earn from qualifying purchases. This does not affect the price you pay.</p>
    </footer>

</body>
</html>`;

fs.writeFileSync(path.join(siteDir, 'index.html'), indexHTML);
console.log('Generated site with ' + products.length + ' products. Enhanced descriptions now collapsible.');
