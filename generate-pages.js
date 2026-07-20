const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const siteDir = '_site';

// ── Seasonal Theme Configuration ──────────────────────────────────────────────
const SEASONAL_THEME = process.env.SEASONAL_THEME || (() => {
    try {
        // Check filesystem for .seasonal-active + .seasonal-theme-name
        // Cloudflare Pages checks out a fresh copy — these files are in git
        const fs = require('fs');
        const activePath = '.seasonal-active';
        const namePath = '.seasonal-theme-name';
        if (fs.existsSync(activePath) && fs.existsSync(namePath)) {
            const ts = parseInt(fs.readFileSync(activePath, 'utf8').trim(), 10);
            const now = Math.floor(Date.now() / 1000);
            const maxAge = 5 * 86400; // 5 days
            if (now - ts < maxAge) {
                const theme = fs.readFileSync(namePath, 'utf8').trim();
                console.log('🎨 Seasonal theme detected:', theme);
                return theme;
            } else {
                console.log('⏳ Seasonal theme expired');
            }
        }
    } catch (_) {}
    return '';
})();

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
                        
                        ${p.price ? `<div class="price-tag">$${p.price.toFixed(2)}</div>` : ''}
                        
                        <!-- Short preview: blurb -->
                        <p class="short-desc">${(p.blurb || p.description.substring(0, 180)).replace(/\n/g, ' ').trim()}${p.blurb ? '' : '...'}</p>
                        
                        <!-- Full enhanced description -->
                        <p class="full-desc">${p.description}</p>
                        
                        <button class="toggle-btn">Why It\u2019s Worth It \u2192</button>
                        
                        <a href="${p.affiliate_url}" class="cta" target="_blank" rel="nofollow">Shop on Amazon</a>
                        <div style="text-align:center;margin-top:8px;">
                            <a href="#" class="price-alert-link" onclick="openPriceAlert('${p.asin}', '${cleanTitle(p.title).replace(/'/g, "\\'").replace(/"/g, "&quot;").replace(/\n/g, ' ')}');return false;" style="font-size:0.8rem;color:#9ca3af;text-decoration:none;display:inline-flex;align-items:center;gap:4px;">
                                <span style="font-size:0.85rem;">🔔</span> Get Price Alert
                            </a>
                        </div>
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
    <link rel="canonical" href="https://www.worthitgoods.com">

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
    <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
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
        /* ── Themed Hero Backgrounds ── */
        .hero[data-theme="back_to_school"] {
            background: linear-gradient(135deg, #1a365d 0%, #2d6a4f 30%, #e9c46a 60%, #f4a261 80%, #e76f51 100%);
            background-size: 400% 400%;
            animation: gradient-shift 25s ease infinite;
        }
        .hero[data-theme="back_to_school"]::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image:
                repeating-linear-gradient(0deg, transparent, transparent 28px, rgba(255,255,255,0.03) 28px, rgba(255,255,255,0.03) 29px),
                repeating-linear-gradient(90deg, transparent, transparent 28px, rgba(255,255,255,0.03) 28px, rgba(255,255,255,0.03) 29px);
            pointer-events: none;
            z-index: 0;
        }
        .hero[data-theme="back_to_school"] .theme-badge {
            display: inline-block;
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(8px);
            padding: 8px 20px;
            border-radius: 50px;
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .hero[data-theme="fall_essentials"] {
            background: linear-gradient(135deg, #5c3a21 0%, #8b5a2b 25%, #d4a373 50%, #cc8b5c 75%, #a0522d 100%);
            background-size: 400% 400%;
            animation: gradient-shift 20s ease infinite;
        }
        .hero[data-theme="halloween"] {
            background: linear-gradient(135deg, #0d0221 0%, #1a0a3e 25%, #ff6b35 50%, #1a0a3e 75%, #0d0221 100%);
            background-size: 400% 400%;
            animation: gradient-shift 15s ease infinite;
        }
        .hero[data-theme="holiday_gifts"] {
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 25%, #1a7a1a 50%, #991b1b 75%, #dc2626 100%);
            background-size: 400% 400%;
            animation: gradient-shift 18s ease infinite;
        }
        .hero[data-theme="thanksgiving_host"] {
            background: linear-gradient(135deg, #92400e 0%, #b45309 25%, #f59e0b 50%, #b45309 75%, #78350f 100%);
            background-size: 400% 400%;
            animation: gradient-shift 22s ease infinite;
        }

        /* ── Subtle Animated Background Behind Product Cards ── */
        .products-section {
            position: relative;
            overflow: hidden;
        }
        .products-section::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 0;
        }
        /* Back to School: subtle floating dots */
        .hero[data-theme="back_to_school"] ~ .products-section::before {
            background-image:
                radial-gradient(circle at 20% 30%, rgba(22, 163, 74, 0.03) 1px, transparent 1px),
                radial-gradient(circle at 80% 60%, rgba(244, 162, 97, 0.03) 1px, transparent 1px),
                radial-gradient(circle at 40% 80%, rgba(233, 196, 106, 0.03) 1px, transparent 1px),
                radial-gradient(circle at 60% 20%, rgba(231, 111, 81, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            animation: float-dots 30s linear infinite;
        }
        @keyframes float-dots {
            0% { transform: translateY(0) rotate(0deg); }
            100% { transform: translateY(-60px) rotate(0.5deg); }
        }
        /* Fall: floating dots */
        .hero[data-theme="fall_essentials"] ~ .products-section::before {
            background-image:
                radial-gradient(circle at 15% 25%, rgba(212, 163, 115, 0.04) 0, rgba(212, 163, 115, 0.04) 4px, transparent 4px),
                radial-gradient(circle at 85% 45%, rgba(160, 82, 45, 0.04) 0, rgba(160, 82, 45, 0.04) 3px, transparent 3px),
                radial-gradient(circle at 50% 75%, rgba(204, 139, 92, 0.03) 0, rgba(204, 139, 92, 0.03) 5px, transparent 5px);
            background-size: 80px 80px;
            animation: float-dots 35s linear infinite;
        }
        /* Halloween: subtle floating dots */
        .hero[data-theme="halloween"] ~ .products-section::before {
            background-image:
                radial-gradient(circle at 30% 40%, rgba(255, 107, 53, 0.03) 0, rgba(255, 107, 53, 0.03) 2px, transparent 2px),
                radial-gradient(circle at 70% 60%, rgba(255, 107, 53, 0.03) 0, rgba(255, 107, 53, 0.03) 3px, transparent 3px);
            background-size: 50px 50px;
            animation: float-dots 20s linear infinite;
        }
        /* Holiday: floating sparkle dots */
        .hero[data-theme="holiday_gifts"] ~ .products-section::before {
            background-image:
                radial-gradient(circle at 40% 30%, rgba(220, 38, 38, 0.03) 1px, transparent 1px),
                radial-gradient(circle at 60% 70%, rgba(26, 122, 26, 0.03) 1px, transparent 1px),
                radial-gradient(circle at 20% 60%, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            background-size: 40px 40px;
            animation: float-dots 25s linear infinite;
        }
        /* Thanksgiving: warm floating dots */
        .hero[data-theme="thanksgiving_host"] ~ .products-section::before {
            background-image:
                radial-gradient(circle at 50% 50%, rgba(245, 158, 11, 0.03) 0, rgba(245, 158, 11, 0.03) 3px, transparent 3px),
                radial-gradient(circle at 80% 20%, rgba(146, 64, 14, 0.03) 0, rgba(146, 64, 14, 0.03) 2px, transparent 2px);
            background-size: 70px 70px;
            animation: float-dots 28s linear infinite;
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
        /* Preference checkbox options */
        .nl-prefs {
            display: flex; flex-direction: column; gap: 8px; margin: 14px auto 0;
            max-width: 440px; text-align: left;
        }
        .nl-pref-option {
            display: flex; align-items: flex-start; gap: 10px;
            padding: 10px 14px; border: 1.5px solid #e5e7eb; border-radius: 10px;
            cursor: pointer; transition: all 0.2s; font-size: 0.88rem;
            background: #fafafa;
        }
        .nl-pref-option:hover { border-color: #ff6b6b; background: #fff5f5; }
        .nl-pref-option input[type="checkbox"] { margin-top: 3px; accent-color: #ff6b6b; }
        .nl-pref-option span { color: #4b5563; line-height: 1.4; }
        .nl-pref-option span strong { color: #1f2937; }

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
        .price-tag {
            font-size: 1.3rem;
            font-weight: 700;
            color: #16a34a;
            margin-bottom: 10px;
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

        /* ── Mobile Responsive ── */
        @media (max-width: 640px) {
            .hero { height: auto !important; min-height: 260px !important; padding: 2rem 1.2rem !important; }
            .hero h1 { font-size: 2rem; }
            .hero p { font-size: 1.05rem; }
            .cta-button { padding: 14px 28px; font-size: 1rem; }

            .section-title { font-size: 1.8rem; }
            .products-section { padding: 40px 12px; }

            .newsletter-section { padding: 30px 18px; margin: 30px 12px; }
            .newsletter-section h2 { font-size: 1.3rem; }
            .newsletter-form { flex-direction: column; gap: 10px; }
            .newsletter-form input[type="email"] { width: 100%; }
            .newsletter-form button { width: 100%; padding: 13px 20px; }

            .nl-prefs { max-width: 100%; }
            .nl-pref-option { padding: 8px 12px; font-size: 0.82rem; }

            .products-grid { grid-template-columns: 1fr; gap: 20px; }

            .product-card .content { padding: 16px; }
            .price-tag { font-size: 1.1rem; }

            footer { padding: 40px 16px 30px; }
            footer .footer-links { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
        }
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
            <p>Honest picks and real comparisons, delivered to your inbox. Pick what you want to receive.</p>
            <form class="newsletter-form" id="wigNewsletterForm">
                <input type="email" id="newsletterEmail" placeholder="your@email.com" required>
                <button type="submit">Subscribe</button>
            </form>
            <div class="nl-prefs">
                <label class="nl-pref-option">
                    <input type="checkbox" id="homePrefPicks" checked>
                    <span><strong>Product picks & roundups</strong> — new worth-it finds, batch posts, and seasonal guides</span>
                </label>
                <label class="nl-pref-option">
                    <input type="checkbox" id="homePrefComparisons" checked>
                    <span><strong>Side-by-side comparisons</strong> — head-to-head articles comparing top products</span>
                </label>
            </div>
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
        const parts = [];
        if (document.getElementById('homePrefPicks').checked) parts.push('picks');
        if (document.getElementById('homePrefComparisons').checked) parts.push('comparisons');
        const prefs = parts.length === 0 ? 'picks' : parts.join(',');
        msg.className = 'newsletter-msg';
        msg.textContent = 'Subscribing...';
        try {
            const res = await fetch('/api/newsletter/signup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, preferences: prefs})
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

    /* ── Price Alert Modal ── */
    function openPriceAlert(asin, title) {
        document.getElementById('paModal').style.display = 'flex';
        document.getElementById('paAsin').value = asin;
        document.getElementById('paProduct').value = title;
        document.getElementById('paMsg').textContent = '';
        document.getElementById('paMsg').className = 'newsletter-msg';
    }
    function closePriceAlert() {
        document.getElementById('paModal').style.display = 'none';
    }
    document.getElementById('paForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const email = document.getElementById('paEmail').value.trim();
        const asin = document.getElementById('paAsin').value;
        const title = document.getElementById('paProduct').value;
        const msg = document.getElementById('paMsg');
        msg.className = 'newsletter-msg';
        msg.textContent = 'Subscribing...';
        try {
            const res = await fetch('/api/subscribe', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, asin, product_title: title})
            });
            const data = await res.json();
            if (data.success) {
                msg.className = 'newsletter-msg success';
                msg.textContent = data.message || "You're subscribed! We'll email you when the price drops.";
                document.getElementById('paEmail').value = '';
            } else {
                msg.className = 'newsletter-msg error';
                msg.textContent = data.message || 'Something went wrong.';
            }
        } catch(err) {
            msg.className = 'newsletter-msg error';
            msg.textContent = 'Service unavailable. Please try again later.';
        }
    });
    // Close modal on backdrop click
    document.getElementById('paModal').addEventListener('click', function(e) {
        if (e.target === this) closePriceAlert();
    });

    /* ── Card-wide click: toggle Why It's Worth It ── */
    document.querySelectorAll('.product-card').forEach(function(card) {
        card.addEventListener('click', function(e) {
            // Don't toggle if clicking the Amazon link or price alert link
            if (e.target.closest('.cta') || e.target.closest('.price-alert-link')) return;
            
            const content = this.querySelector('.content');
            const short = content.querySelector('.short-desc');
            const full = content.querySelector('.full-desc');
            const btn = content.querySelector('.toggle-btn');
            if (!full) return;
            
            if (full.style.display === 'block') {
                full.style.display = 'none';
                short.style.display = 'block';
                btn.textContent = 'Why It\u2019s Worth It \u2192';
            } else {
                full.style.display = 'block';
                short.style.display = 'none';
                btn.textContent = 'Show less \u2191';
            }
        });
        // Make the card cursor indicate it's clickable
        card.style.cursor = 'pointer';
    });
    </script>

    <!-- ── Price Alert Modal ── -->
    <div id="paModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:999;align-items:center;justify-content:center;">
      <div style="background:white;border-radius:16px;padding:32px;max-width:400px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.2);position:relative;">
        <button onclick="closePriceAlert()" style="position:absolute;top:12px;right:16px;background:none;border:none;font-size:1.4rem;cursor:pointer;color:#9ca3af;">×</button>
        <h3 style="margin-top:0;margin-bottom:8px;font-size:1.3rem;">🔔 Price Alert</h3>
        <p style="color:#6b7280;font-size:0.9rem;margin-bottom:16px;">We'll email you when this product's price drops. No spam, unsubscribe anytime.</p>
        <form id="paForm">
          <input type="hidden" id="paAsin">
          <input type="hidden" id="paProduct">
          <input type="email" id="paEmail" placeholder="your@email.com" required style="width:100%;padding:12px;border:2px solid #e5e7eb;border-radius:8px;font-size:1rem;margin-bottom:12px;box-sizing:border-box;">
          <button type="submit" style="width:100%;padding:12px;background:linear-gradient(135deg,#ff9a56,#ff6b6b);color:white;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;">Notify Me When Price Drops</button>
          <div id="paMsg" class="newsletter-msg" style="margin-top:8px;"></div>
        </form>
      </div>
    </div>

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
