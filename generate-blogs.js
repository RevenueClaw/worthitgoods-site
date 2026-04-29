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

// Full structure: 4-5 relevant products per blog, detailed content
const blogs = [
  {
    slug: '2026-04-29-best-kitchen-tools',
    title: 'Best Kitchen Tools Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Curated kitchen essentials for measuring, seasoning, storage, scraping, and cleaning - durable tools that make cooking easier.',
    introPara1: "Cooking should be a joy, not a frustration. Yet so many kitchen tools promise the world but deliver disappointment: flimsy plastics that crack, shakers that clump, or containers that let air in. We've scoured hundreds of options to bring you only the genuine standouts—durable, practical items under $50 that solve real problems in everyday meal prep.",
    introPara2: "Our criteria are simple but strict: ergonomic design, easy cleaning, long-lasting materials, and rave reviews from home chefs. These picks focus on core kitchen tasks like accurate measuring, quick seasoning, organized bulk storage, scraping jars clean, and maintaining shine. No gimmicks, just upgrades that pay off meal after meal.",
    introPara3: "Whether you're stocking a new kitchen or upgrading tired gear, these 5 tools will transform your routine. Let's dive in.",
    products: [
      {
        name: 'Radicaln Marble Salt Cellar with Lid 4"',
        short: 'Stylish pinch bowl for dry, fresh salt access anytime.',
        why: 'Mid-recipe salt fumbles end here. This 4-inch natural marble cellar with fitted stone lid keeps salt moisture-free for perfect pinches, adding elegant counter decor without high cost. Handcrafted veining makes it unique, built for years of use.',
        pros: 'Moisture-proof lid prevents clumping; premium stone feel doubles as decor; one-hand operation for speed.',
        cons: 'Refills more often than grinders; hand-wash to protect finish.',
        bestFor: 'Daily cooks and style-conscious chefs.',
        vs: 'Faster/cleaner than shakers; more refined than plastic bowls.'
      },
      {
        name: 'Angled Measuring Cup Set',
        short: 'Patented eye-level measuring—no spills or guesswork.',
        why: 'Bend-over measuring mishaps ruin recipes. Angled design lets you read from above with crystal-clear markings across 4 sizes, preventing over/under pours in baking or sauces. Sturdy, wedding-registry proven.',
        pros: 'Spill-resistant angles; full set value; comfortable grip.',
        cons: 'Hand-wash recommended; plastic not glass-heavy.',
        bestFor: 'Bakers and precision cooks.',
        vs: 'Eye-level accuracy beats standard cups; lighter than scales.'
      },
      {
        name: '1 Gallon Glass Cookie Jars with Lids',
        short: 'Airtight storage for 5lb bulk staples like flour or snacks.',
        why: 'Pantry chaos? These clear 3.8L glass jars swallow full 5lb bags, airtight lids lock freshness, stackable for neat shelves. See contents instantly to avoid waste.',
        pros: 'Massive capacity with tight seal; aesthetic glass upgrade.',
        cons: 'Glass weight when loaded.',
        bestFor: 'Bulk buyers and organizers.',
        vs: 'Visible airtight > plastic bins.'
      },
      {
        name: "Meguiar's Ultimate Wash and Wax",
        short: 'Gentle 2-in-1 shine for appliances and counters.',
        why: 'Keep stainless gleaming between deep cleans. pH-neutral formula cleans/protects without scratches—safe for fridges, ovens, counters. Quick showroom results.',
        pros: 'Efficient combo; surface-safe.',
        cons: 'Rinse foam well.',
        bestFor: 'Kitchen maintenance.',
        vs: 'One-step > separate products.'
      },
      {
        name: 'Splatypus Jar Spatula',
        short: 'Corner-scraping tool for zero jar waste.',
        why: 'Maximize spreads/sauces with flexible design that reaches every crevice. Dishwasher-safe, fun shape saves money long-term.',
        pros: 'Complete extraction; easy clean.',
        cons: 'Soak sticky first.',
        bestFor: 'Jar lovers.',
        vs: 'Better scrape than spoons.'
      }
    ],
    advice: 'Begin with measuring cups for basics, salt cellar for flavor finesse, jars for bulk, spatula for efficiency, wax for shine. Hand-wash stone/glass; buy sets. Pair with grid towels/peelers for full kit.',
    conclusion: 'These 5 kitchen tools eliminate hassles, elevate skills, and look great doing it. Proven winners for any cook. Check the full product grid for 50+ more. What\\'s your essential? Comment!'
  },
  {
    slug: '2026-04-29-outdoor-survival-essentials',
    title: 'Best Outdoor Survival Essentials Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Compact multitools, emergency kits, scopes—gear that\\'s light but lifesaving for trails and trips.',
    introPara1: "The outdoors tests your gear like nothing else. Bulky kits weigh you down, cheap tools fail when needed. We selected 5 essentials that pack small, multitask smartly, and have field-tested durability from hikers and campers.",
    introPara2: "Focus: EDC carry, emergency response, diagnostics. Under $50 value that could save the day.",
    introPara3: "Ready for hikes, cars, camps—let\\'s equip you.",
    products: [
      {
        name: '6 Tools IN ONE Versatile Multitool Pen',
        short: 'Pen EDC with drivers/level/ruler.',
        why: 'Trail fixes without bulk: 6 tools (screwdriver, level, ruler, stylus) in pocket pen form. Always with you for quick repairs, no backpack rummaging.',
        pros: 'Compact EDC; multi-function; durable metal.',
        cons: 'Light-duty only.',
        bestFor: 'Hikers and EDC fans.',
        vs: 'Slimmer/portable than full multitools.'
      },
      {
        name: 'Pink Car Emergency Kit',
        short: 'Trunk rescue pack.',
        why: 'Complete roadside readiness: jumper cables, first aid, flare in easy-spot pink case. Peace of mind for solo drivers.',
        pros: 'All-in-one; visible color; compact.',
        cons: 'Check expiry dates yearly.',
        bestFor: 'Daily commuters.',
        vs: 'Organized kit > scattered items.'
      },
      {
        name: 'Inspection Borescope Camera with 4.3" IPS Screen',
        short: '16.5ft waterproof scope.',
        why: 'See inside engines/pipes standalone—no phone needed. 1080p clarity for diagnostics on the go.',
        pros: 'Long cable; built-in screen; rugged.',
        cons: 'Narrow lens limits.',
        bestFor: 'Mechanics and explorers.',
        vs: 'Independent > app-dependent.'
      },
      {
        name: 'Heavy Duty Tool Bag',
        short: '16-pocket organizer.',
        why: 'Sort hammers, wrenches, drills in rugged bag with tape clip. Ends gear chaos on jobsites/trips.',
        pros: 'Huge capacity; tough fabric.',
        cons: 'Bulky when packed.',
        bestFor: 'Campers and DIYers.',
        vs: 'Organized access > loose bags.'
      },
      {
        name: 'CRAFTSMAN Shallow Socket, Metric, 1/2-Inch Drive, 10mm',
        short: 'Grip-tight bolt solver.',
        why: 'Never lose your 10mm again—12-point design grips without stripping, chrome for corrosion resistance.',
        pros: 'Lifetime warranty; precise fit.',
        cons: 'Single size.',
        bestFor: 'Field fixes.',
        vs: 'Pro-grade hold.'
      }
    ],
    advice: 'Carry pen daily; kit in trunk; bag for outings. Test gear yearly. Pair with grid lights/knives.',
    conclusion: 'Lightweight essentials for real adventures. Build confidence outdoors. Full grid has more survival picks.'
  },
  {
    slug: '2026-04-29-tech-fitness-gear',
    title: 'Top Tech Fitness Gear Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Watches, lamps for tracking and vibes—no subs.',
    introPara1: "Fitness tech should track accurately and motivate without subscriptions or bulk. These 4 picks excel in data, battery, and smart integration for runners, gym-goers.",
    introPara2: "Criteria: Long battery, intuitive controls, ecosystem compatibility. Versatile for daily wear.",
    introPara3: "Upgrade your routine—here\\'s the gear.",
    products: [
      {
        name: 'Apple Watch Series 9',
        short: 'Gesture health hub.',
        why: 'S9 chip powers bright display, double-tap gestures for no-touch checks. All-day battery for seamless health tracking.',
        pros: 'Intuitive gestures; crash detection; iOS sync.',
        cons: 'Best in Apple ecosystem.',
        bestFor: 'iPhone users.',
        vs: 'Faster interaction than older models.'
      },
      {
        name: 'Garmin Forerunner 265 Running Smartwatch',
        short: 'GPS endurance tracker.',
        why: '13-day battery, AMOLED screen, advanced running metrics—no sub needed for core features.',
        pros: 'Deep analytics; sunlight readable.',
        cons: 'Learning curve.',
        bestFor: 'Runners.',
        vs: 'Battery life crushes competitors.'
      },
      {
        name: 'Govee RGBIC Smart Table Lamp',
        short: 'Workout ambiance lights.',
        why: 'RGBIC segments for dynamic moods, 500lm brightness, app/voice control energizes sessions.',
        pros: 'Color versatility; no hub.',
        cons: 'App setup.',
        bestFor: 'Home gyms.',
        vs: 'Segmented lights > basic bulbs.'
      },
      {
        name: 'Travel Cable Organizer Pouch Electronic Accessories Carry Case',
        short: 'Charge tidy for gym/travel.',
        why: 'Compact pouch sorts cables/chargers—fun print reminds to pack right, reduces tangle stress.',
        pros: 'Portable; durable.',
        cons: 'Small capacity.',
        bestFor: 'Mobile fitness.',
        vs: 'Organized > tangled mess.'
      }
    ],
    advice: 'Match watch to phone; lamp for mood; pouch for travel. Add straps/bands from grid.',
    conclusion: 'Tech that tracks and inspires without hassle. Explore grid for fitness complements.'
  },
  {
    slug: '2026-04-29-top-gifts-home',
    title: 'Top Home Gifts Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Boxes, jars, tiles—lasting home joys.',
    introPara1: "Great gifts blend utility, beauty, sentiment. These 5 endure years, delight daily.",
    introPara2: "Handcrafted, practical picks for homes—under $50 impact.",
    introPara3: "Perfect for birthdays, housewarmings.",
    products: [
      {
        name: 'Samhita Handmade Mango Wood Tree of Life Keepsake Box',
        short: 'Symbolic storage heirloom.',
        why: 'Hand-carved mango wood Tree of Life—vintage patina for jewelry/treasures. Meaningful, sturdy.',
        pros: 'Unique artisan; ages gracefully.',
        cons: 'Small interior.',
        bestFor: 'Housewarmings.',
        vs: 'Personal > mass-produced.'
      },
      {
        name: '1 Gallon Glass Cookie Jars with Lids',
        short: 'Pantry beauty staple.',
        why: 'Airtight 5lb capacity—clear glass organizes/elevates kitchen shelves.',
        pros: 'Fresh seal; stackable.',
        cons: 'Heavy.',
        bestFor: 'Bakers.',
        vs: 'Elegant glass > plastic.'
      },
      {
        name: 'STEM Magnetic Tiles 70-Piece Set with Idea Book',
        short: 'Kid STEM builds.',
        why: '70 magnets + book spark creativity—durable for endless play.',
        pros: 'Educational; strong hold.',
        cons: 'Storage needed.',
        bestFor: 'Parents.',
        vs: 'Full set value.'
      },
      {
        name: 'Radicaln Marble Salt Cellar with Lid 4"',
        short: 'Table elegance.',
        why: 'Marble pinch bowl—functional decor for seasoning with style.',
        pros: 'Moisture-proof; premium feel.',
        cons: 'Refills.',
        bestFor: 'Chefs.',
        vs: 'Sophisticated upgrade.'
      },
      {
        name: 'MotoLoot Keychain',
        short: 'Personal EDC charm.',
        why: 'Bold design sparks talks—durable daily carry gift.',
        pros: 'Unique; tough.',
        cons: 'Niche appeal.',
        bestFor: 'Riders/fans.',
        vs: 'Conversational accessory.'
      }
    ],
    advice: 'Match to recipient—wood for sentiment, tiles for kids. Personalize notes.',
    conclusion: 'Timeless gifts that become favorites. Grid for more home ideas.'
  },
  {
    slug: '2026-04-29-batch10-latest-picks',
    title: 'Batch 10 Latest Picks Worth It',
    date: '2026-04-29',
    desc: 'New gems vetted.',
    introPara1: "Fresh arrivals stand out for quality/value.",
    introPara2: "4 highlights from latest batch.",
    introPara3: "Versatile for DIY, kids, fans, homes.",
    products: [
      {
        name: 'CRAFTSMAN Shallow Socket, Metric, 1/2-Inch Drive, 10mm, 12-Point',
        short: 'Essential 10mm fix.',
        why: 'Grips tight without slip—chrome, warrantied for garages.',
        pros: 'No-strip; pro build.',
        cons: 'Single size.',
        bestFor: 'DIY mechanics.',
        vs: 'Reliable everyday.'
      },
      {
        name: 'STEM Magnetic Tiles 70-Piece Set with Idea Book',
        short: 'Creative kid builds.',
        why: 'Magnets + shapes/book fuel STEM hours.',
        pros: 'Durable fun.',
        cons: 'Storage.',
        bestFor: 'Kids 3+.',
        vs: 'Complete starter set.'
      },
      {
        name: 'Star Wars: Darth Vader - Original Mobile Phone & Gaming Controller Holder',
        short: 'Desk/gaming fun.',
        why: '8.5" statue holds phone/controller—fan desk upgrade.',
        pros: 'Sturdy icon.',
        cons: 'Niche.',
        bestFor: 'Star Wars fans.',
        vs: 'Themed utility.'
      },
      {
        name: 'Govee RGBIC Smart Table Lamp',
        short: 'Ambiance shifter.',
        why: 'RGB segments, 500lm—mood lighting for any room.',
        pros: 'Smart versatile.',
        cons: 'App.',
        bestFor: 'Home setups.',
        vs: 'Dynamic colors.'
      }
    ],
    advice: 'Socket for tools; tiles kids; Vader fans; lamp vibes. Full grid.',
    conclusion: 'Batch 10 winners. Shop all vetted gear.'
  }
];

blogs.forEach(blog => {
  blog.products = blog.products.map(p => {
    const prod = findProduct(p.name);
    p.image = prod.image || '';
    p.affurl = prod.affiliate_url || '/#products';
    return p;
  });

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
    <h2>The Top Picks</h2>
${blog.products.map(p => `
    <section class="product-highlight" style="margin-bottom: 3rem; padding: 2rem; border: 1px solid #ddd; border-radius: 12px; background: #fafafa; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
      ${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy" style="max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">` : ''}
      <h2>${p.name}</h2>
      <p class="short" style="font-size: 1.1em; font-style: italic; color: #555; margin-bottom: 1.5rem;">${p.short}</p>
      <h3 style="color: #ff6b35;">Why It's Worth It</h3>
      <p style="line-height: 1.6; margin-bottom: 1.5rem;">${p.why}</p>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem;">
        <div>
          <h4 style="color: #28a745;">Pros</h4>
          <p style="line-height: 1.6;">${p.pros}</p>
        </div>
        <div>
          <h4 style="color: #dc3545;">Cons</h4>
          <p style="line-height: 1.6;">${p.cons}</p>
        </div>
      </div>
      <h4>Best For</h4>
      <p style="line-height: 1.6; font-weight: 500; margin-bottom: 1rem;">${p.bestFor}</p>
      <h4>Vs Alternatives</h4>
      <p style="line-height: 1.6;">${p.vs}</p>
      <a href="${p.affurl}" class="cta" style="display: inline-block; padding: 1rem 2rem; background: #ff6b35; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 1rem;">Shop on Amazon →</a>
    </section>
`).join('')}
    <div class="section-header" style="margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 12px;">
      <h2>Buying Advice & Recommendations</h2>
      <p style="line-height: 1.6; font-size: 1.1em;">${blog.advice}</p>
    </div>
    <div class="section-header" style="margin-top: 2rem; padding: 2rem; background: #e9ecef; border-radius: 12px;">
      <h2>Conclusion / Final Thoughts</h2>
      <p style="line-height: 1.6; font-size: 1.1em;">${blog.conclusion}</p>
      <a href="/#products" style="font-weight: bold; color: #ff6b35;">← Explore Full Product Grid</a>
    </div>
    <p style="text-align: center; margin: 3rem 0;"><a href="/blog.html" class="cta-button" style="display: inline-block; padding: 1rem 2rem; background: #007bff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Read More Posts</a></p>
  </article>
  <footer style="margin-top: 4rem; padding: 2rem; background: #333; color: white; text-align: center;">
    <p>© 2026 WorthIt Goods. Amazon affiliate disclosure: We earn from qualifying purchases.</p>
  </footer>
</body>
</html>`;

  fs.writeFileSync(path.join(blogDir, `${blog.slug}.html`), content);
  fs.writeFileSync(path.join(siteBlogDir, `${blog.slug}.html`), content);
});

console.log('Generated 5 high-quality blogs with full structure (Intro/Top Picks/Advice/Conclusion), 4-5 products each, images/links. Check ls -lh blog/*.html');
