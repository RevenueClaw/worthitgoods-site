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
  if (text.match(/\b(kitchen|measure|jar|spatula|salt\s+cellar|scissor|pantry|utensil|tallow|dish\s+towel|measuring\s+cup|cook|chef|bake|zest|grater)\b/i) && !text.match(/soap|towel|gift|watch|darth|star|govee|tool bag|coaster|chicken|keychain|car|emergency|ninja|blendpro|1200|kinetic|shart|gan|duffle|pi case|skin|face|whipped|beauty/i)) return 'kitchen';
  if (text.match(/\b(gift|keepsake|box|home|mug|vase|journal|coaster|chess|pickle|chicken|bowl|decor|floor|weather|station)\b/i) && !text.match(/soap|towel|kitchen|car|emergency|keychain|outdoor|tool|watch|survival|borescope|socket/i)) return 'homegifts';
  if (text.match(/\b(watch|smartwatch|fitness|running|garmin|apple\s+watch|forerunner)\b/i) && !text.match(/\b(cable|charger|backpack|lamp|light\s+neck|emergency|tool|survival|borescope|socket)\b/i)) return 'techfitness';
  if (['multitool', 'emergency kit', 'survival kit', 'survival', 'army knife', 'swiss army', 'cooler'].some(kw => text.includes(kw)) && !text.match(/\b(car|socket|borescope|kitchen|home|fitness|watch|smartwatch|running|garmin|apple\s+watch|forerunner)\b/i)) return 'outdoorsurvival';
  return 'general';
};

const parseProductDetails = (p) => {
  const desc = p.description || '';
  let why = `Practical upgrade solving real problems with durability and value for ${p.title.split(' ')[0].toLowerCase()}.`;
  let pros = `Key strengths: durable build, versatile use from ${(p.blurb || p.title || '').substring(0,50)}.`;
  let cons = `Potential drawbacks: size/weight for ${p.title.split(' ')[0].toLowerCase()}, niche fit.`;
  let bestFor = `Ideal for ${p.category || 'daily tasks'}: ${p.title.split(' ')[0]} users.`;
  let short = (p.blurb || p.title).substring(0, 80) + '...';
  let vs = `Beats budget ${p.title.split(' ')[0].toLowerCase()} options in quality, features, longevity.`;

  // Parse Why
  const whyMatch = desc.match(/Why It's Worth It[:\s]*([\s\S]*?)(?=Pros:|Cons:|Best for|\[Blurb|$)/i);
  if (whyMatch) why = whyMatch[1].trim().replace(/^:\s*/, '');

  // Parse Pros
  const prosMatch = desc.match(/Pros[:\s]*([\s\S]*?)(?=Cons:|Best for|\[Blurb|$)/i);
  if (prosMatch) pros = prosMatch[1].trim();

  // Parse Cons
  const consMatch = desc.match(/Cons[:\s]*([\s\S]*?)(?=Best for|\[Blurb|$)/i);
  if (consMatch) cons = consMatch[1].trim();

  // Parse Best for
  const bestMatch = desc.match(/Best for[:\s]*([\s\S]*?)(?=\.|\[Blurb|$)/i);
  if (bestMatch) bestFor = bestMatch[1].trim();

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
  { slug: '2026-05-08-batch14-latest-picks', title: 'Batch 14: Newest Worth-It Picks', category: 'batch14', desc: 'Batch 14: Kinetic Sand toys, emergency kits, GaN chargers, Ninja blenders, wood docks, UA duffles, Souper Cubes, Pi cases.', introPara1: "Toys to tech, kitchen to makers.", introPara2: "Fresh vetted variety.", introPara3: "Grab these gems." },
  { slug: '2026-04-30-batch13-latest-picks', title: 'Batch 13: Freshest Worth-It Picks', category: 'batch13', desc: 'Batch 13: Can mustaches, turbo fans, meat tenderizers, plate frames, wash mitts.', introPara1: "Quirky car/party/kitchen upgrades.", introPara2: "Instant fixes, laughs, clean.", introPara3: "Latest gems." },
  { slug: '2026-04-29-batch12-latest-picks', title: 'Batch 12: Newest Worth-It Picks', category: 'batch12', desc: 'Batch 12: Wine glasses, coolers, coasters, sunglasses, zesters.', introPara1: "Fun/utility mix from recent drop.", introPara2: "Party prep, geek tables, trails.", introPara3: "Solid starters." },
  { slug: '2026-04-29-best-kitchen-tools', title: 'Best Kitchen Tools Worth Buying in 2026', category: 'kitchen', desc: 'Curated kitchen essentials for prep, storage, cleaning.', introPara1: "Frustrated by flimsy tools? Durable standouts here.", introPara2: "Ergonomic, easy-clean, chef-approved.", introPara3: "Transform your kitchen." },
  { slug: '2026-04-29-top-gifts-home', title: 'Top Home Decor & Gifts for Enthusiasts in 2026', category: 'homegifts', desc: 'Decorative keepsakes, vases, weather stations, and home joys.', introPara1: "Gifts and decor blending beauty and utility.", introPara2: "Handcrafted, practical picks for home lovers.", introPara3: "Perfect for gifting or personalizing spaces." },
  { slug: '2026-04-29-tech-fitness-gear', title: 'Top Tech Fitness Gear in 2026', category: 'techfitness', desc: 'Wearables, lights, organizers—no subs.', introPara1: "Tech for data and motivation.", introPara2: "Long battery, intuitive.", introPara3: "Upgrade routine." },
  { slug: '2026-04-29-outdoor-survival-essentials', title: 'Outdoor Survival Essentials 2026', category: 'outdoorsurvival', desc: 'Multitools, kits for trails.', introPara1: "Light, reliable outdoor gear.", introPara2: "EDC and emergency ready.", introPara3: "Gear up." },
  { slug: '2026-04-29-batch10-latest-picks', title: 'Batch 10: Latest Worth-It Picks', category: 'kitchen', desc: 'Fresh vetted kitchen/home gems.', introPara1: "New quality arrivals.", introPara2: "Highlights from batch.", introPara3: "Versatile essentials." }
];

categoryBlogs.forEach(blog => {
  let catProds;
  if (blog.category === 'batch14') {
    catProds = products.slice(0,8).map(parseProductDetails);
  } else if (blog.category === 'batch13') {
    catProds = products.slice(8,13).map(parseProductDetails);
  } else if (blog.category === 'batch12') {
    catProds = products.slice(13,18).map(parseProductDetails);
  } else {
    catProds = products
      .map(p => ({...p, cat: categorizeProduct(p.title, p.blurb, p.description) }))
      .filter(p => p.cat === blog.category)
      .slice(0,10)
      .map(parseProductDetails);
  }

  if (catProds.length === 0) {
    console.log(`Skipping ${blog.slug}: no ${blog.category} products`);
    return;
  }

  let advice = `Start with ${catProds[0].name.split(' ')[0]} for core needs; add others for depth. Follow care instructions.`;
  if (blog.category === 'batch14') {
    advice = `Batch 14 highlights: Kinetic Sand for kid creativity, Emergency Shart Kit for mishap prep, 100W GaN Charger for multi-device power, Ninja BlendPro for kitchen power, Wood Dock for desk org, UA Duffle for gym hauls, Souper Cubes for meal prep, GeeekPi Case for Pi projects. Playful to pro; mess-free, portable, durable. Stock up for family/tech/kitchen.`;
  } else if (blog.category === 'batch13') {
    advice = `Batch 13 showcases quirky winners: Novelty Can Mustache Clip for party laughs, Portable Handheld Turbo Fan for instant cooling, KitchenAid Meat Tenderizer for grill prep, Silicone License Plate Frames to kill rattles, Chemical Guys Chenille Wash Mitts for swirl-free cars. Versatile fun/practical; clip easy, fans recharge, mitts rinse. Build kits for events/drives.`;
  } else if (blog.category === 'batch12') {
    advice = `Batch 12 variety: Funny Stemless Wine Glass for cheeky nights, Coleman Snap N Go Cooler for trails, PCB Circuit Coasters for tech tables, Heat Wave Lazer Sunglasses for raves, Deiss PRO Zester for chefs. Fun/utility mix; store dry, dishwasher ok. Home/party/outdoor starters.`;
  }
  if (blog.category === 'techfitness') {
    advice = `Kick off your fitness tech upgrade with the ${catProds[0].name} – it's the all-in-one powerhouse for heart rate, steps, sleep, and notifications without forcing subscriptions. Runners, grab the ${catProds[1]?.name || 'Garmin Forerunner 265'} next for precise GPS tracking and training insights. Skip cables or lamps here; focus on wearables. Pro tips: Match your phone OS (Apple for iPhone, Garmin for Android), verify 24+ hour battery from reviews, ensure comfy fit. These keep you motivated year-round without buyer's remorse.`;
  } else if (blog.category === 'outdoorsurvival') {
    advice = `Whether you're hitting the trails or prepping for the unexpected, start with the ${catProds[0]?.name || 'multitool'} as your everyday carry essential—it's compact and packs multiple tools for quick fixes on the go. Add the Coleman Snap N Go Cooler for collapsible storage on camping trips or picnics, keeping drinks/ice cold without bulk. Include the Victorinox Tinker Swiss Army Knife for precise cutting and the 14-in-1 Survival Kit for fire/shelter basics. Prioritize lightweight, rust-resistant gear. Practice deploying, store dry, pack layers. Stay prepared—safely.`;
  }
  const conclusion = `There you have it – ${catProds.length} no-nonsense ${blog.category.toUpperCase()} standouts that punch above their weight in durability and smarts. We've filtered the hype for real-world winners. Dive into the full 50+ product grid for more categories, or drop a comment: what's your must-have? Level up today.`;

  const intro = `<p>${blog.introPara1}</p><p>${blog.introPara2}</p>${blog.introPara3 ? `<p>${blog.introPara3}</p>` : ''}`;

  let content = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${blog.title} - WorthIt Goods</title>

<!-- Open Graph / Facebook -->
<meta property="og:title" content="${blog.title}">
<meta property="og:description" content="${blog.desc}">
<meta property="og:image" content="https://www.worthitgoods.com/assets/og-image.jpg?v=20260430">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="${blog.title} - WorthItGoods (Updated 2026-05-08)">
<meta name="robots" content="index, follow">
<meta property="og:url" content="https://www.worthitgoods.com/blog/${blog.slug}.html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="WorthItGoods">

<!-- Twitter Cards -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${blog.title}">
<meta name="twitter:description" content="${blog.desc}">
<meta name="twitter:image" content="https://www.worthitgoods.com/assets/og-image.jpg">

<meta name="description" content="${blog.desc}">
<link rel="stylesheet" href="/style.css">
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
<section class="product-highlight" style="max-width:650px;margin:0 auto 2.5rem auto;padding:1.5rem;border:1px solid #ddd;border-radius:12px;background:#fafafa;box-shadow:0 4px 12px rgba(0,0,0,.05);">
${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy" style="max-width:100%;max-height:280px;height:auto;object-fit:contain;display:block;margin:0 auto 1.5rem;border-radius:8px;box-shadow:0 4px 8px rgba(0,0,0,.1);">` : ''}
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
<div class="section-header" style="max-width:650px;margin:3rem auto 0;padding:1.5rem;background:#f8f9fa;border-radius:12px;">
<h2>Buying Advice</h2>
<p style="line-height:1.6;font-size:1.1em;">${advice}</p>
</div>
<div class="section-header" style="max-width:650px;margin:2rem auto 0;padding:1.5rem;background:#e9ecef;border-radius:12px;">
<h2>Conclusion</h2>
<p style="line-height:1.6;font-size:1.1em;">${conclusion}</p>
<a href="/#products" style="font-weight:bold;color:#ff6b35;">← Full Product Grid</a>
</div>
<p style="text-align:center;margin:3rem 0;"><a href="/blog.html" class="cta-button" style="display:inline-block;padding:1rem 2rem;background:#007bff;color:white;text-decoration:none;border-radius:8px;font-weight:bold;">Read More Posts</a></p>
</article>
<footer style="margin-top:4rem;padding:2rem;background:#333;color:white;text-align:center;">
<p>© 2026 WorthIt Goods. Amazon affiliate disclosure: We earn from qualifying purchases.</p>
</footer>
</body>
</html>`;

  fs.writeFileSync(path.join(blogDir, blog.slug + '.html'), content);
  fs.writeFileSync(path.join(siteBlogDir, blog.slug + '.html'), content);
});

console.log('Generated category-strict blogs with dynamic filtering/parsing. ls -lh blog/*.html');// Cache bust Fri May  8 21:40:27 EDT 2026
