const fs = require('fs');
const path = require('path');

const blogDir = 'blog';
const siteBlogDir = '_site/blog';

if (!fs.existsSync(blogDir)) fs.mkdirSync(blogDir, { recursive: true });
if (!fs.existsSync(siteBlogDir)) fs.mkdirSync(siteBlogDir, { recursive: true });

// Load products from sample_products.json for category-based blogs
const products = JSON.parse(fs.readFileSync('data/sample_products.json', 'utf8'));

// Load individual batch files for batch-specific blogs
const batch10Prods = JSON.parse(fs.readFileSync('data/new_batch12.json', 'utf8'));
const batch12Prods = JSON.parse(fs.readFileSync('data/new_batch12.json', 'utf8'));
const batch13Prods = JSON.parse(fs.readFileSync('data/new_batch15.json', 'utf8'));
const batch14Prods = JSON.parse(fs.readFileSync('data/new_batch14_readd.json', 'utf8'));

const categorizeProduct = (title, blurb, desc) => {
  const text = (title + ' ' + (blurb || '') + ' ' + (desc || '')).toLowerCase();
  const t = title.toLowerCase();
  
  // KITCHEN items - strong kitchen indicators OR kitchen tool patterns in title
  if (t.match(/\b(measur|spatula|salt\s+cellar|zest|grater|jar|utensil|tallow|cookie\s+jar|dish\s+towel)\b/) ||
      (text.match(/\b(kitchen|pantry|cook|chef|bake|measuring|spatula|grater|zester)\b/i) && 
       !text.match(/soap|watch|darth|govee|tool\s+bag|keychain|car|emergency|outdoor|survival/))) return 'kitchen';
  
  // TECH FITNESS - watches, fitness trackers
  if (text.match(/\b(watch|smartwatch|fitness|running|garmin|apple\s+watch|forerunner)\b/i) && 
      !text.match(/\b(cable|charger|backpack|lamp|emergency|tool|survival|socket)\b/i)) return 'techfitness';
  
  // OUTDOOR/SURVIVAL - camping, survival gear
  if (['multitool', 'emergency kit', 'survival kit', 'survival', 'army knife', 'swiss army', 'cooler', 'flashlight', 'spotlight'].some(kw => t.includes(kw)) || 
      (text.match(/\b(survival|cooler|flashlight|spotlight|emergency kit)\b/i) && 
       !text.match(/car|socket|borescope|kitchen|home|fitness|watch|running/))) return 'outdoorsurvival';
  
  // HOME GIFTS - decorative, keepsakes, mugs, games (but exclude kitchen car outdoor)
  if (text.match(/\b(coaster|chess|vase|journal|lamp|holder|decor|plush|crochet|blanket|mug|wine\s+glass|stemless|sunglasses|darth|vader|game|controller|geek|ethernet|cable|pi)\b/i) && 
      !text.match(/kitchen|car|emergency|tool|watch|survival|outdoor|socket/)) return 'homegifts';
  if (text.match(/\b(watch|smartwatch|fitness|running|garmin|apple\s+watch|forerunner)\b/i) && 
     !text.match(/\b(cable|charger|backpack|lamp|light\s+neck|emergency|tool|survival|borescope|socket)\b/)) return 'techfitness';
  if (['multitool', 'emergency kit', 'survival kit', 'survival', 'army knife', 'swiss army', 'cooler', 'tinker', '14-in-1', 'flashlight', 'spotlight'].some(kw => text.includes(kw)) && 
     !text.match(/car|socket|borescope|kitchen|home|fitness|watch|smartwatch|running|garmin|apple\s+watch|forerunner/)) return 'outdoorsurvival';
  return 'general';
};

const parseProductDetails = (p) => {
  const desc = p.description || '';
  let why = `Practical upgrade solving real problems with durability and value.`;
  let pros = `High quality, reliable performance.`;
  let cons = `Minor limitations in niche uses.`;
  let bestFor = `Everyday users and enthusiasts.`;
  let short = (p.blurb || p.description || p.title).substring(0, 80) + '...';
  let vs = `Better than typical alternatives in function and longevity.`;

  const whyMatch = desc.match(/Why It's Worth It[:\s]*([\s\S]*?)(?=Pros:|Cons:|Best for|\[Blurb|$)/i);
  if (whyMatch) why = whyMatch[1].trim().replace(/^:\s*/, '');

  const prosMatch = desc.match(/Pros[:\s]*([\s\S]*?)(?=Cons:|Best for|\[Blurb|$)/i);
  if (prosMatch) pros = prosMatch[1].trim();

  const consMatch = desc.match(/Cons[:\s]*([\s\S]*?)(?=Best for|\[Blurb|$)/i);
  if (consMatch) cons = consMatch[1].trim();

  const bestMatch = desc.match(/Best for[:\s]*([\s\S]*?)(?=\.|\[Blurb|$)/i);
  if (bestMatch) bestFor = bestMatch[1].trim();

  if (p.blurb) short = p.blurb.substring(0, 100) + (p.blurb.length > 100 ? '...' : '');

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

const parseBatchProduct = (p) => {
  return {
    name: p.title,
    short: (p.blurb || p.description || p.title).substring(0, 100) + '...',
    why: p.description || 'Practical upgrade solving real problems with durability and value.',
    pros: 'Key strengths: durable build, versatile use.',
    cons: 'Potential drawbacks: size/weight, niche fit.',
    bestFor: p.category ? `Ideal for ${p.category} enthusiasts.` : 'Everyday users and enthusiasts.',
    vs: 'Beats budget options in quality, features, longevity.',
    image: p.image || '',
    affurl: p.affiliate_url || '/#products'
  };
};

const categoryBlogs = [
  { slug: '2026-05-08-batch14-latest-picks', title: 'Batch 14: Newest Worth-It Picks', category: 'batch14', desc: 'Batch 14: Kinetic Sand toys, emergency kits, GaN chargers, Ninja blenders, wood docks, UA duffles, Souper Cubes, Pi cases.', introPara1: "Toys to tech, kitchen to makers.", introPara2: "Fresh vetted variety.", introPara3: "Grab these gems." },
  { slug: '2026-04-30-batch13-latest-picks', title: 'Batch 13: Freshest Worth-It Picks', category: 'batch13', desc: 'Batch 13: Flashlights, screwdrivers, squishy toys, slushie machines, Pi cases.', introPara1: "Quirky car/party/kitchen upgrades.", introPara2: "Instant fixes, laughs, clean.", introPara3: "Latest gems." },
  { slug: '2026-04-29-batch12-latest-picks', title: 'Batch 12: Newest Worth-It Picks', category: 'batch12', desc: 'Batch 12: Wine glasses, coolers, coasters, sunglasses, zesters.', introPara1: "Fun/utility mix from recent drop.", introPara2: "Party prep, geek tables, trails.", introPara3: "Solid starters." },
  { slug: '2026-04-29-batch10-latest-picks', title: 'Batch 10: Latest Worth-It Picks', category: 'batch10', desc: 'Fresh vetted kitchen/home gems.', introPara1: "New quality arrivals.", introPara2: "Highlights from batch.", introPara3: "Versatile essentials." },
  { slug: '2026-04-29-best-kitchen-tools', title: 'Best Kitchen Tools Worth Buying in 2026', category: 'kitchen', desc: 'Curated kitchen essentials for prep, storage, cleaning.', introPara1: "Frustrated by flimsy tools? Durable standouts here.", introPara2: "Ergonomic, easy-clean, chef-approved.", introPara3: "Transform your kitchen." },
  { slug: '2026-04-29-top-gifts-home', title: 'Top Home Gifts Worth Buying in 2026', category: 'homegifts', desc: 'Decorative keepsakes, coasters, and home joys.', introPara1: "Gifts blending beauty and utility.", introPara2: "Handcrafted, practical picks.", introPara3: "Perfect for gifting." },
  { slug: '2026-04-29-tech-fitness-gear', title: 'Top Tech Fitness Gear in 2026', category: 'techfitness', desc: 'Wearables, lights, organizers—no subs.', introPara1: "Tech for data and motivation.", introPara2: "Long battery, intuitive.", introPara3: "Upgrade routine." },
  { slug: '2026-04-29-outdoor-survival-essentials', title: 'Outdoor Survival Essentials 2026', category: 'outdoorsurvival', desc: 'Multitools, kits, coolers for trails.', introPara1: "Light, reliable outdoor gear.", introPara2: "EDC and emergency ready.", introPara3: "Gear up." }
];

categoryBlogs.forEach(blog => {
  let catProds = [];
  let featuredImage = '';
  let advice = '';

  if (blog.category === 'batch14') {
    catProds = batch14Prods.map(parseBatchProduct);
    advice = `Batch 14 highlights: Kinetic Sand for kid creativity, Emergency Shart Kit for mishap prep, 100W GaN Charger for multi-device power, Ninja BlendPro for kitchen power, Wood Dock for desk org, UA Duffle for gym hauls, Souper Cubes for meal prep, GeeekPi Case for Pi projects. Playful to pro; mess-free, portable, durable.`;
  } else if (blog.category === 'batch13') {
    catProds = batch13Prods.slice(0, 5).map(parseBatchProduct);
    advice = `Batch 13 showcases: Rechargeable Spotlight for outdoor adventures, Klein Tools Screwdriver for DIY, Squishy Toys for stress relief, Ninja SLUSHi for frozen treats, RETROFLAG Pi Case for retro gaming. Versatile fun/practical; compact, rechargeable.`;
  } else if (blog.category === 'batch12' || blog.category === 'batch10') {
    catProds = batch12Prods.map(parseBatchProduct);
    advice = `Batch 12 variety: Funny Stemless Wine Glass for parties, Coleman Cooler for trails, PCB Circuit Coasters for tech tables, Heat Wave Sunglasses for style, Deiss PRO Zester for chefs. Fun/utility mix; store dry, dishwasher ok.`;
  } else {
    // Category-based blogs - skip Father's Day products (0-14) and batch products (15-37) without proper categories
    catProds = products
      .slice(38)
      .map(p => ({...p, cat: categorizeProduct(p.title, p.blurb, p.description) }))
      .filter(p => p.cat === blog.category)
      .slice(0, 6)
      .map(parseProductDetails);
    
    if (blog.category === 'techfitness') {
      advice = `Kick off with the Apple Watch Series 9 for heart rate, steps, sleep, and notifications without subscriptions. Runners, grab the Garmin Forerunner 265 for precise GPS tracking. Match your phone OS, verify 24+ hour battery, ensure comfy fit.`;
    } else if (blog.category === 'outdoorsurvival') {
      advice = `Start with the Coleman Snap N Go Cooler for collapsible storage on trips. Add the Victorinox Tinker Swiss Army Knife for precise cutting and the 14-in-1 Survival Kit for fire/shelter basics. Prioritize lightweight, rust-resistant gear.`;
    } else if (blog.category === 'kitchen') {
      advice = `Start with the Angled Measuring Cup Set for precise baking. Add the Splatypus Jar Spatula to get every last bit from jars. The Radicaln Marble Salt Cellar adds elegance. Glass Cookie Jars keep pantry items fresh. Look for ergonomic handles and dishwasher-safe materials.`;
    } else if (blog.category === 'homegifts') {
      advice = `Start with PCB Circuit Board Coasters for a geeky touch. The Govee RGBIC Smart Table Lamp adds ambiance. Star Wars fans will love the Darth Vader Phone Holder. Look for gifts that blend beauty and utility—handcrafted, practical picks.`;
    } else {
      advice = `Start with ${catProds[0]?.name.split(' ')[0] || 'featured picks'} for core needs; add others for depth.`;
    }
  }

  if (catProds.length === 0) {
    console.log(`Skipping ${blog.slug}: no ${blog.category} products`);
    return;
  }
  
  featuredImage = catProds[0]?.image || '';
  const conclusion = `There you have it – ${catProds.length} no-nonsense standouts that punch above their weight. We've filtered the hype for real-world winners. Dive into the full product grid for more!`;
  const intro = `<p>${blog.introPara1}</p><p>${blog.introPara2}</p>${blog.introPara3 ? `<p>${blog.introPara3}</p>` : ''}`;

  let content = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${blog.title} - WorthIt Goods</title>
<meta property="og:title" content="${blog.title}">
<meta property="og:description" content="${blog.desc}">
<meta property="og:image" content="${featuredImage || 'https://www.worthitgoods.com/assets/og-image.jpg'}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="https://www.worthitgoods.com/blog/${blog.slug}.html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="WorthItGoods">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${blog.title}">
<meta name="twitter:description" content="${blog.desc}">
<meta name="twitter:image" content="${featuredImage || 'https://www.worthitgoods.com/assets/og-image.jpg'}">
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
<a href="${p.affurl}" target="_blank" class="cta" style="display:inline-block;padding:1rem 2rem;background:#ff6b35;color:white;text-decoration:none;border-radius:8px;font-weight:bold;margin-top:1rem;">Shop on Amazon →</a>
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

  const blogPath = path.join(blogDir, `${blog.slug}.html`);
  const siteBlogPath = path.join(siteBlogDir, `${blog.slug}.html`);
  
  fs.writeFileSync(blogPath, content);
  fs.writeFileSync(siteBlogPath, content);
  console.log(`Generated ${blog.slug}.html with ${catProds.length} products`);
});

console.log('All blogs regenerated successfully!');