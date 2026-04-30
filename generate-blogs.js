const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const blogDir = 'blog';
const siteBlogDir = '_site/blog';

if (!fs.existsSync(blogDir)) fs.mkdirSync(blogDir, { recursive: true });
if (!fs.existsSync(siteBlogDir)) fs.mkdirSync(siteBlogDir, { recursive: true });

const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));

const categorizeProduct = (title, blurb, desc) => {
  const text = (title + ' ' + (blurb || '') + ' ' + (desc || '')).toLowerCase();
  if (text.match(/\b(kitchen|measure|jar|spatula|salt\s+cellar|scissor|pantry|utensil|tallow|dish\s+towel|measuring\s+cup)\b/i) && !text.match(/soap|towel|gift|watch|darth|star|govee|tool bag/i)) return 'kitchen';
  if (text.match(/\b(gift|keepsake|box|mug|vase|journal|coaster|chess|pickle|chicken|bowl)\b/i) && !text.match(/soap|towel|kitchen/i)) return 'homegifts';
  if (text.match(/\b(watch|smartwatch|lamp|cable|backpack|light\s+neck|charger|garmin|apple\s+watch)\b/i)) return 'techfitness';
  if (['tool bag', 'multitool', 'emergency kit', 'borescope', 'socket', 'survival', 'army knife', 'briefcase'].some(kw => text.includes(kw))) return 'outdoorsurvival';
  return 'general';
};

const parseProductDetails = (p) => {
  const desc = p.description || '';
  let why = 'Practical upgrade solving real problems with durability and value.';
  let pros = 'High quality, reliable performance.';
  let cons = 'Minor limitations in niche uses.';
  let bestFor = 'Everyday users and enthusiasts.';
  let short = (p.blurb || p.title).substring(0, 80) + '...';
  let vs = 'Better than typical alternatives in function and longevity.';

  if (desc.includes('Why It')) {
    const whyMatch = desc.match(/Why It's Worth It[:\\s]*([\\s\\S]*?)(?=Pros:|Cons:|Best|$) /);
    if (whyMatch) why = whyMatch[1].trim();
  }
  if (desc.includes('Pros')) {
    const prosMatch = desc.match(/Pros[:\\s]*([\\s\\S]*?)(?=Cons:|Best|$) /);
    if (prosMatch) pros = prosMatch[1].trim();
  }
  if (desc.includes('Cons')) {
    const consMatch = desc.match(/Cons[:\\s]*([\\s\\S]*?)(?=Best|$) /);
    if (consMatch) cons = consMatch[1].trim();
  }
  if (desc.includes('Best for')) {
    const bestMatch = desc.match(/Best for[:\s]*([\s\S]*?)(?=\[|$)/i);
    if (bestMatch) bestFor = bestMatch[1].trim();
  }

  return {
    name: p.title,
    short: short,
    why: why,
    pros: pros,
    cons: cons,
    bestFor: bestFor,
    vs: vs,
    image: p.image || '',
    affurl: p.affiliate_url || '/#products'
  };
};

const categoryBlogs = [
  { slug: '2026-04-29-best-kitchen-tools', title: 'Best Kitchen Tools Worth Buying in 2026', category: 'kitchen', desc: 'Curated kitchen essentials for prep, storage, cleaning.', introPara1: "Frustrated by flimsy tools? Durable standouts here.", introPara2: "Ergonomic, easy-clean, chef-approved.", introPara3: "Transform your kitchen." },
  { slug: '2026-04-29-top-gifts-home', title: 'Top Home Gifts Worth Buying in 2026', category: 'homegifts', desc: 'Decorative keepsakes and home joys.', introPara1: "Gifts blending beauty and utility.", introPara2: "Handcrafted, practical picks.", introPara3: "Perfect for gifting." },
  { slug: '2026-04-29-tech-fitness-gear', title: 'Top Tech Fitness Gear in 2026', category: 'techfitness', desc: 'Wearables, lights, organizers—no subs.', introPara1: "Tech for data and motivation.", introPara2: "Long battery, intuitive.", introPara3: "Upgrade routine." },
  { slug: '2026-04-29-outdoor-survival-essentials', title: 'Outdoor Survival Essentials 2026', category: 'outdoorsurvival', desc: 'Multitools, kits for trails.', introPara1: "Light, reliable outdoor gear.", introPara2: "EDC and emergency ready.", introPara3: "Gear up." },
  { slug: '2026-04-29-batch10-latest-picks', title: 'Batch 10 Latest Picks', category: 'kitchen', desc: 'Fresh vetted kitchen/home gems.', introPara1: "New quality arrivals.", introPara2: "Highlights from batch.", introPara3: "Versatile essentials." }
];

categoryBlogs.forEach(blog => {
  const catProds = products
    .map(p => ({...p, cat: categorizeProduct(p.title, p.blurb, p.description)}))
    .filter(p => p.cat === blog.category)
    .slice(0,5)
    .map(parseProductDetails);

  if (catProds.length === 0) {
    console.log(`Skipping ${blog.slug}: no ${blog.category} products`);
    return;
  }

  const advice = `Start with ${catProds[0].name.split(' ')[0]} for core needs; add others. Hand-wash where noted.`;
  const conclusion = `${catProds.length} category picks that deliver. Full grid has 50+.`;

  const intro = `<p>${blog.introPara1}</p><p>${blog.introPara2}</p>${blog.introPara3 ? `<p>${blog.introPara3}</p>` : ''}`;

  let content = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${blog.title} - WorthIt Goods</title>
<link rel="stylesheet" href="/style.css">
<meta name="description" content="${blog.desc}">
</head>
<body>
<header><nav><a href="/" class="logo">WorthItGoods</a><ul><li><a href="/">Home</a></li><li><a href="/blog.html">Blog</a></li></ul></nav></header>
<div class="hero">
<div class="hero-content">
<h1>${blog.title}</h1>
</div>
</div>
<article class="products-section">
<div class="section-header">
<h2>Introduction</h2>
${intro}
</div>
<h2>Top Picks</h2>
${catProds.map(p => `
<section class="product-highlight" style="margin-bottom:3rem;padding:2rem;border:1px solid #ddd;border-radius:12px;background:#fafafa;box-shadow:0 4px 12px rgba(0,0,0,.05);">
${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy" style="max-width:100%;height:auto;border-radius:8px;margin-bottom:1.5rem;box-shadow:0 4px 8px rgba(0,0,0,.1);">` : ''}
<h2>${p.name}</h2>
<p class="short" style="font-size:1.1em;font-style:italic;color:#555;margin-bottom:1.5rem;">${p.short}</p>
<h3 style="color:#ff6b35;">Why It's Worth It</h3>
<p style="line-height:1.6;margin-bottom:1.5rem;">${p.why}</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;margin-bottom:1.5rem;">
<div>
<h4 style="color:#28a745;">Pros</h4>
<p style="line-height:1.6;">${p.pros}</p>
</div>
<div>
<h4 style="color:#dc3545;">Cons</h4>
<p style="line-height:1.6;">${p.cons}</p>
</div>
</div>
<h4>Best For</h4>
<p style="line-height:1.6;font-weight:500;margin-bottom:1rem;">${p.bestFor}</p>
<h4>Vs Alternatives</h4>
<p style="line-height:1.6;">${p.vs}</p>
<a href="${p.affurl}" class="cta" style="display:inline-block;padding:1rem 2rem;background:#ff6b35;color:white;text-decoration:none;border-radius:8px;font-weight:bold;margin-top:1rem;">Shop on Amazon →</a>
</section>
`).join('')}
<div class="section-header" style="margin-top:3rem;padding:2rem;background:#f8f9fa;border-radius:12px;">
<h2>Buying Advice</h2>
<p style="line-height:1.6;font-size:1.1em;">${advice}</p>
</div>
<div class="section-header" style="margin-top:2rem;padding:2rem;background:#e9ecef;border-radius:12px;">
<h2>Conclusion</h2>
<p style="line-height:1.6;font-size:1.1em;">${conclusion}</p>
<a href="/#products" style="font-weight:bold;color:#ff6b35;">← Full Product Grid</a>
</div>
<p style="text-align:center;margin:3rem 0;"><a href="/blog.html" class="cta-button" style="display:inline-block;padding:1rem 2rem;background:#007bff;color:white;text-decoration:none;border-radius:8px;font-weight:bold;">Read More Posts</a></p>
</article>
<footer style="margin-top:4rem;padding:2rem;background:#333;color:white;text-align:center;">
<p>© 2026 WorthIt Goods. Amazon affiliate disclosure: We earn from qualifying purchases.</p>
</footer>
</body></html>`;

  fs.writeFileSync(path.join(blogDir, blog.slug + '.html'), content);
  fs.writeFileSync(path.join(siteBlogDir, blog.slug + '.html'), content);
});

console.log('Generated category-strict blogs with dynamic filtering/parsing. ls -lh blog/*.html');