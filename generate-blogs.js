const fs = require('fs');
const path = require('path');

const productsDataPath = 'data/sample_products.json';
const blogDir = 'blog';
const siteBlogDir = '_site/blog';

if (!fs.existsSync(blogDir)) fs.mkdirSync(blogDir, { recursive: true });
if (!fs.existsSync(siteBlogDir)) fs.mkdirSync(siteBlogDir, { recursive: true });

const products = JSON.parse(fs.readFileSync(productsDataPath, 'utf8'));

const findProduct = (searchTitle) => {
  return products.find(p => p.title.toLowerCase().includes(searchTitle.toLowerCase()) || searchTitle.toLowerCase().includes(p.title.toLowerCase())) || {};
};

// Define 5 blogs with ONLY thematically relevant products from data
const blogs = [
  {
    slug: '2026-04-29-best-kitchen-tools',
    title: 'Best Kitchen Tools Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Proven kitchen essentials: measuring, storage, seasoning—tools that make cooking precise, organized, and stylish.',
    intro: `Kitchen clutter and imprecise tools lead to ruined recipes and frustration. We've focused exclusively on genuine kitchen heroes: items for measuring, storing bulk staples, and quick seasoning. Curated from top-rated options that deliver daily value without gimmicks.`,
    products: [
      {
        name: 'Radicaln Marble Salt Cellar with Lid 4"',
        short: 'Elegant pinch bowl keeps salt fresh and dry.',
        why: `No more clumpy shakers—this natural marble cellar with stone lid provides quick one-handed access to dry, fresh salt for perfect seasoning every time. Its hefty 4-inch design adds subtle elegance to counters while being practical for daily cooks.`,
        pros: `Moisture-proof lid; stylish stone decor; easy grip for pinches.`,
        cons: `Hand-wash preferred; smaller capacity needs refills.`,
        bestFor: `Home chefs wanting functional style.`,
        vs: `Superior to shakers (no mess/clumps); classier than plastic bowls.`
      },
      {
        name: 'Angled Measuring Cup Set',
        short: 'Eye-level accuracy ends spills and guesswork.',
        why: `Patented angles let you measure liquids from above—no bending or squinting. Essential set (1-4 cups/quart) for baking/cooking precision, a staple that prevents recipe failures.`,
        pros: `Spill-resistant; multiple sizes; durable plastic.`,
        cons: `Hand-wash for best care; not glass-like premium feel.`,
        bestFor: `Bakers and precise cooks.`,
        vs: `Eye-level beats standard cups; portable vs scales.`
      },
      {
        name: '1 Gallon Glass Cookie Jars with Lids',
        short: 'Airtight bulk storage for flour, sugar, snacks.',
        why: `Fit entire 5lb bags in these clear 3.8L glass jars—airtight lids keep contents fresh, stackable design organizes pantries effortlessly while letting you see inventory at a glance.`,
        pros: `Huge capacity; visible airtight seal; shelf aesthetic.`,
        cons: `Heavy when full.`,
        bestFor: `Bulk cooks and pantry organizers.`,
        vs: `Clear glass > opaque plastics; pro storage at home price.`
      }
    ],
    advice: `Prioritize measuring cups for basics, salt cellar for speed, jars for bulk. Hand-wash glass/stone. Bundle for savings. See grid for towels/scissors complements.`,
    conclusion: `These kitchen-focused tools streamline prep and elevate your space. Explore full grid for 50+ vetted items. Favorites? Comment!`
  },
  {
    slug: '2026-04-29-outdoor-survival-essentials',
    title: 'Best Outdoor Survival Essentials Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Trail-ready multitools, kits, and diagnostics—compact gear for real emergencies.',
    intro: `Outdoor mishaps happen fast. These survival picks are compact, multi-use, and field-proven: pens that fix, kits that save, tools that diagnose—pure essentials, no fluff.`,
    products: [
      {
        name: '6 Tools IN ONE Versatile Multitool Pen',
        short: 'Pocket EDC with level, ruler, drivers.',
        why: `Disguised as a pen: screwdriver, level, ruler, stylus—fixes trailside gear or camps without bulk. Always carried, endlessly useful.`,
        pros: `Ultra-portable; 6 functions.`,
        cons: `Light-duty only.`,
        bestFor: `Hikers/campers.`,
        vs: `Handier than full multitools.`
      },
      {
        name: 'Pink Car Emergency Kit',
        short: 'Roadside rescue: cables, aid, flare.',
        why: `10ft jumpers, first aid, tire tools, bright case—trunk essential for breakdowns. Visible pink speeds access.`,
        pros: `Complete; easy-find.`,
        cons: `Annual checks needed.`,
        bestFor: `Drivers/trips.`,
        vs: `Kit > piecemeal.`
      },
      {
        name: 'Inspection Borescope Camera with 4.3" IPS Screen',
        short: '16.5ft waterproof scope for inspections.',
        why: `Standalone screen, IP67 camera—peers into engines/pipes trailside. No phone required.`,
        pros: `Long reach; clear view.`,
        cons: `Tight spots challenging.`,
        bestFor: `Mechanics/outdoorsmen.`,
        vs: `Independent > app-based.`
      }
    ],
    advice: `Pen daily; kit for cars/trips. Practice use. Layer with grid lights/bags.`,
    conclusion: `Lightweight readiness for adventures. Full grid has more. Share tips!`
  },
  {
    slug: '2026-04-29-tech-fitness-gear',
    title: 'Top Tech Fitness Gear Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Wearables and smart lights: data-driven fitness without subs.',
    intro: `Real fitness tech tracks meaningfully. Apple/Garmin watches for metrics, Govee for gym vibes—ecosystem-smart picks.`,
    products: [
      {
        name: 'Apple Watch Series 9',
        short: 'S9 chip, double-tap, all-day health.',
        why: `Bright display, gesture control, crash/sleep tracking—iPhone sync perfection.`,
        pros: `Safety features; intuitive.`,
        cons: `iOS-locked; cost.`,
        bestFor: `Apple fitness fans.`,
        vs: `Gestures > old models.`
      },
      {
        name: 'Garmin Forerunner 265 Running Smartwatch',
        short: '13-day battery, AMOLED runner metrics.',
        why: `GPS 20hrs, no-fee insights—sunlight-readable for training.`,
        pros: `Battery king; deep data.`,
        cons: `Learning curve.`,
        bestFor: `Runners.`,
        vs: `Endurance > rivals.`
      },
      {
        name: 'Govee RGBIC Smart Table Lamp',
        short: 'RGB segments for workout ambiance.',
        why: `500lm, app whites/colors—gym mood setter.`,
        pros: `Versatile lighting.`,
        cons: `App setup.`,
        bestFor: `Home gyms.`,
        vs: `Dynamic > static.`
      }
    ],
    advice: `Ecosystem match. Weekly charge. Grid for straps.`,
    conclusion: `Actionable fitness upgrades. More in grid.`
  },
  {
    slug: '2026-04-29-top-gifts-home',
    title: 'Top Home Gifts Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Artisan boxes, jars, tiles—thoughtful home upgrades.',
    intro: `Gifts that charm and function: wood heirlooms, storage, kid creativity.`,
    products: [
      {
        name: 'Samhita Handmade Mango Wood Tree of Life Keepsake Box',
        short: 'Carved wood for treasures.',
        why: `Symbolic Tree of Life, vintage mango—jewelry/letters holder ages well.`,
        pros: `Artisan unique; sturdy.`,
        cons: `Small items.`,
        bestFor: `Housewarmings.`,
        vs: `Heirloom > cheap.`
      },
      {
        name: '1 Gallon Glass Cookie Jars with Lids',
        short: `Pantry's new best friend.`,
        why: `5lb bulk fit, airtight clear—organizes stylishly.`,
        pros: `Fresh seal; visible.`,
        cons: `Weight.`,
        bestFor: `Bakers/gifters.`,
        vs: `Glass > plastic.`
      },
      {
        name: 'STEM Magnetic Tiles 70-Piece Set with Idea Book',
        short: `Creative building for kids.`,
        why: `5 shapes + book: STEM fun, strong magnets.`,
        pros: `Educational durable.`,
        cons: `Storage.`,
        bestFor: `Parents.`,
        vs: `Full set > mini.`
      }
    ],
    advice: `Note personalize. Grid complements.`,
    conclusion: `Lasting gifts. See more.`
  },
  {
    slug: '2026-04-29-batch10-latest-picks',
    title: 'Batch 10 Latest Picks Worth It',
    date: '2026-04-29',
    desc: `Newest vetted gems: sockets, tiles, more.`,
    intro: `Fresh batch standouts—diverse utility.`,
    products: [
      {
        name: 'CRAFTSMAN Shallow Socket, Metric, 1/2-Inch Drive, 10mm, 12-Point',
        short: `Forever 10mm solution.`,
        why: `Tight grip, corrosion-free—garage must.`,
        pros: `No-slip; warranty.`,
        cons: `Single size.`,
        bestFor: `Mechanics.`,
        vs: `Pro > cheap.`
      },
      {
        name: 'STEM Magnetic Tiles 70-Piece Set with Idea Book',
        short: `STEM builds galore.`,
        why: `70 pcs inspire—safe magnets.`,
        pros: `Fun learning.`,
        cons: `Storage.`,
        bestFor: `Kids.`,
        vs: `Varied > basic.`
      }
    ],
    advice: `Sets save. Grid context.`,
    conclusion: `New wins ready. Grid all.`
  }
];

blogs.forEach(blog => {
  blog.products = blog.products.map(p => {
    const prod = findProduct(p.name);
    p.image = prod.image || '';
    p.affurl = prod.affiliate_url || '/#products';
    return p;
  });

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
      <p>${blog.intro}</p>
    </div>
    <h2>Our Top Picks</h2>
${blog.products.map(p => `
    <section class="product-highlight" style="margin-bottom: 3rem; padding: 2rem; border: 1px solid #ddd; border-radius: 12px; background: #fafafa; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      ${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy" style="max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">` : ''}
      <h2 style="margin-top: 0;">${p.name}</h2>
      <p class="short" style="font-size: 1.1em; font-style: italic; color: #555; margin-bottom: 1.5rem;">${p.short}</p>
      <section class="why-section">
        <h3 style="color: #ff6b35;">Why It's Worth It</h3>
        <p style="line-height: 1.6; margin-bottom: 1.5rem;">${p.why}</p>
      </section>
      <section class="pros-cons" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem;">
        <div>
          <h4 style="color: #28a745;">Pros</h4>
          <p style="line-height: 1.6;">${p.pros}</p>
        </div>
        <div>
          <h4 style="color: #dc3545;">Cons</h4>
          <p style="line-height: 1.6;">${p.cons}</p>
        </div>
      </section>
      <section style="margin-bottom: 1.5rem;">
        <h4>Best For</h4>
        <p style="line-height: 1.6; font-weight: 500;">${p.bestFor}</p>
        <h4>Vs Alternatives</h4>
        <p style="line-height: 1.6;">${p.vs}</p>
      </section>
      <a href="${p.affurl}" class="cta" style="display: inline-block; padding: 1rem 2rem; background: #ff6b35; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 8px rgba(255,107,53,0.3);">Shop on Amazon →</a>
    </section>
`).join('')}
    <div class="section-header" style="margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 12px;">
      <h2>Buying Advice</h2>
      <p style="line-height: 1.6; font-size: 1.1em;">${blog.advice}</p>
    </div>
    <div class="section-header" style="margin-top: 2rem;">
      <h2>Final Thoughts</h2>
      <p style="line-height: 1.6;">${blog.conclusion}</p>
      <a href="/#products" style="font-weight: bold; color: #ff6b35;">← Full Product Grid</a>
    </div>
    <p style="text-align: center; margin: 3rem 0;"><a href="/blog.html" class="cta-button" style="display: inline-block; padding: 1rem 2rem; background: #007bff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">More Posts</a></p>
  </article>
  <footer style="margin-top: 4rem; padding: 2rem; background: #333; color: white; text-align: center;">
    <p>© 2026 WorthIt Goods. Amazon affiliate: commissions from purchases.</p>
  </footer>
</body>
</html>`;

  fs.writeFileSync(path.join(blogDir, `${blog.slug}.html`), content);
  fs.writeFileSync(path.join(siteBlogDir, `${blog.slug}.html`), content);
});

console.log('Regenerated 5 blogs with category-relevant products only (e.g. Kitchen: salt/measuring/jars). Enriched images/URLs. ls -lh blog/ for sizes.');
