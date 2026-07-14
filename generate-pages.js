const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const siteDir = '_site';

// ── Seasonal Theme Configuration ──────────────────────────────────────────────
const SEASONAL_THEME = process.env.SEASONAL_THEME || '';

const THEMES = {
    back_to_school: {
        badge: '🎒 Back to School Picks',
        tagline: 'Smart dorm & school essentials that actually make campus life better',
    },
    fall_essentials: {
        badge: '🍂 Fall Essentials',
        tagline: 'Cozy up — warm throws, comfort food gear, and the best of sweater weather',
    },
    halloween: {
        badge: '🎃 Halloween Fun',
        tagline: 'Spooky season gear — decorations, costumes, party games, and treats',
    },
    thanksgiving_host: {
        badge: '🦃 Thanksgiving Hosting',
        tagline: 'Everything you need to host a memorable Thanksgiving without the stress',
    },
    holiday_gifts: {
        badge: '🎁 Holiday Gift Guide',
        tagline: 'Gifts people actually want — hand-picked for everyone on your list',
    },
};

const activeTheme = THEMES[SEASONAL_THEME] || null;

if (!fs.existsSync(siteDir)) {
    fs.mkdirSync(siteDir, { recursive: true });
}

const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));


function cleanTitle(title) {
    if (title.length <= 55) return title;
    for (const sep of [' \u2013 ', ' \u2014 ', ' - ', ' | ', ' \u2013', ' \u2014']) {
        const idx = title.indexOf(sep);
        if (idx > 30 && idx < 100) return title.slice(0, idx).trim();
    }
    const comma = title.indexOf(', ', 45);
    if (comma > 40 && comma < 100) return title.slice(0, comma).trim();
    return title.slice(0, 55).trim() + '\u2026';
}

// ── SEO: JSON-LD Structured Data ────────────────────────────────────────────

function generateProductSchema(products) {
    // Product schema for every item — enables Google rich results
    const productSchemas = products.map((p, i) => ({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p.title,
        "image": p.image,
        "description": (p.blurb || p.description).substring(0, 300),
        "offers": {
            "@type": "Offer",
            "url": p.affiliate_url,
            "availability": "https://schema.org/InStock",
            "seller": {
                "@type": "Organization",
                "name": "Amazon.com"
            }
        }
    }));

    // WebSite schema for site search
    const siteSchema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "WorthItGoods",
        "url": "https://www.worthitgoods.com",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": "https://www.worthitgoods.com/#products"
            },
            "query-input": "required name=search_term_string"
        },
        "description": "Curated products actually worth buying. Honest reviews, hand-picked finds."
    };

    // Organization schema
    const orgSchema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "WorthItGoods",
        "url": "https://www.worthitgoods.com",
        "description": "Curated product discovery — honest picks, no hype."
    };

    return `
<script type="application/ld+json">${JSON.stringify(siteSchema, null, 2)}</script>
<script type="application/ld+json">${JSON.stringify(orgSchema, null, 2)}</script>
<script type="application/ld+json">${JSON.stringify(productSchemas, null, 2)}</script>`;
}


function renderProduct(p) {
    const badge = p.badge ? `<div class="product-badge" data-badge="${p.badge.replace(/"/g, '&quot;')}">${p.badge}</div>` : '';
    return `
                <div class="product-card${p.badge ? ' has-badge' : ''}">
                    <div class="image-wrapper">
                        <img src="${p.image}" alt="${cleanTitle(p.title)} — WorthItGoods worth-buying pick" loading="lazy">
                        ${badge}
                    </div>
                    <div class="content">
                        <h3>${cleanTitle(p.title)}</h3>
                        
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
    <title>${products.slice(0, 3).map(p => cleanTitle(p.title)).join(' • ')} — WorthItGoods</title>

    <!-- Open Graph / Facebook -->
    <meta property="og:title" content="${products.slice(0, 2).map(p => cleanTitle(p.title)).join(' & ')} — WorthItGoods">
    <meta property="og:description" content="${products.slice(0, 4).map(p => p.blurb || p.description.substring(0, 80)).join(' | ')}">
    <meta property="og:image" content="${products[0].image}">
    <meta property="og:image:width" content="500">
    <meta property="og:image:height" content="500">
    <meta property="og:image:alt" content="${cleanTitle(products[0].title)} — featured worth-it pick on WorthItGoods">
    <meta property="og:url" content="https://www.worthitgoods.com">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="WorthItGoods">

    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="WorthItGoods — Hand-picked Products Actually Worth Buying">
    <meta name="twitter:description" content="${products.slice(0, 3).map(p => cleanTitle(p.title)).join(', ')} and more worth-it finds.">
    <meta name="twitter:image" content="${products[0].image}">

    ${generateProductSchema(products)}

    <meta name="p:domain_verify" content="ca0773faec0aacd987007dc40e6e32f2"/>
    <link rel="alternate" type="application/rss+xml" title="WorthIt Goods — Blog RSS Feed" href="https://www.worthitgoods.com/feed.xml" />
    <!-- Google Search Console: replace with your verification meta tag from search.google.com/search-console -->
    <!-- <meta name="google-site-verification" content="..." /> -->
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
            margin: 50px auto;
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
    <div class="hero"${activeTheme ? ` data-theme="${SEASONAL_THEME}"` : ''}>
        <div class="hero-content">
            ${activeTheme ? `<div class="theme-badge">${activeTheme.badge}</div>` : ''}
            <h1>WorthIt Goods</h1>
            <p>${activeTheme ? activeTheme.tagline : 'Honest, hand-picked products that actually deliver.<br>No junk. No hype. Just gear worth your money and time.'}</p>
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
        <div class="footer-links" style="margin-bottom: 20px;">
            <a href="/" style="color: #ff9a56; text-decoration: none; margin: 0 12px;">Home</a>
            <a href="/blog.html" style="color: #ff9a56; text-decoration: none; margin: 0 12px;">Blog</a>
            <a href="/feed.xml" style="color: #ff9a56; text-decoration: none; margin: 0 12px;">RSS Feed</a>
            <a href="/#products" style="color: #ff9a56; text-decoration: none; margin: 0 12px;">All Products</a>
            <a href="/privacy.html" style="color: #ff9a56; text-decoration: none; margin: 0 12px;">Privacy</a>
        </div>
        <p>© 2026 WorthIt Goods. Honest picks, no hype.</p>
        <p>As an Amazon Associate, I earn from qualifying purchases. Prices may vary.</p>
    </footer>

</body>
</html>`;

fs.writeFileSync(path.join(siteDir, 'index.html'), indexHTML);
console.log('Generated site with ' + products.length + ' products. Enhanced descriptions now collapsible.');
