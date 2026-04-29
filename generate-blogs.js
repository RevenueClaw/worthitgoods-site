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

// Define 5 blogs with curated products, expanded rich conversational content
const blogs = [
  {
    slug: '2026-04-29-best-kitchen-tools',
    title: 'Best Kitchen Tools Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Honest guide to kitchen tools that actually deliver value—no gimmicks, just gear that makes cooking easier and more enjoyable.',
    intro: `In 2026, kitchen tools are everywhere, but most are junk that ends up forgotten in the back of a drawer. What makes a tool "worth it"? It's durable, solves a real everyday problem, offers great value under $50, and stands the test of time. We've curated these top picks from hundreds of options, based on user reviews, our own testing criteria (ergonomics, ease of cleaning, longevity), and real-world use. Whether you're a daily home chef or just tired of flimsy gadgets, these will upgrade your cooking routine.`,
    products: [
      {
        name: 'Radicaln Marble Salt Cellar with Lid 4"',
        short: 'Quick pinch salt access without shaker mess or clumping.',
        why: `Imagine reaching for salt mid-cook without fumbling with a clumpy shaker—this 4-inch marble cellar with a natural stone lid changes the game. It keeps your salt perfectly dry and fresh for precise flavor control every time. With its premium, hefty feel on the counter, it doubles as subtle decor without costing a fortune. Each handcrafted piece has unique marble veining, and it's built to last for years of daily use.`,
        pros: `Elegant marble design that serves as stylish counter decor; tight-fitting lid prevents moisture and clumping; easy one-handed pinch grip for fast seasoning.`,
        cons: `Smaller capacity means more frequent refills compared to large grinders; best hand-washed to preserve the stone's finish.`,
        bestFor: `Daily home chefs and cooks who appreciate functional beauty in their kitchen setup.`,
        vs: `Beats plastic shakers (no spills or clumping issues) and cheap grinders (finer control, no messy refills mid-meal).`
      },
      {
        name: 'Angled Measuring Cup Set',
        short: 'Measure liquids accurately from eye-level—no bending, squinting, or spills.',
        why: `Ever poured too much because you couldn't see the level properly? This patented angled measuring cup set lets you read measurements from above, eliminating guesswork for precise baking and cooking. It's a wedding registry staple for a reason—clear markings on multiple sizes (1 cup, 2 cup, 4 cup, 1 quart) make it versatile, and the sturdy plastic withstands daily drops without cracking.`,
        pros: `Spill-proof angled design prevents overpouring; includes four essential sizes; ergonomic handle comfortable for all ages and hand sizes.`,
        cons: `Plastic construction feels less premium than glass alternatives; manufacturer recommends hand-washing for longevity.`,
        bestFor: `Bakers, beginner cooks, and anyone frustrated by inaccurate measurements that ruin recipes.`,
        vs: `Outshines traditional straight-sided cups (no eye-straining bends) and is more portable than bulky digital scales.`
      },
      {
        name: 'Heavy Duty Tool Bag',
        short: '16-pocket organizer for tools, utensils, or kitchen gadgets—no more drawer chaos.',
        why: `Drawer disorganization slowing you down? This rugged heavy-duty tool bag features 16 dedicated pockets plus a tape measure hook to keep hammers, screwdrivers, utensils, or gadgets neatly sorted and accessible. The tough fabric is built for jobsites or busy kitchens, standing up to rough handling day after day.`,
        pros: `Massive storage capacity for pro or DIY kits; reinforced construction ensures long-term durability without rips or tears.`,
        cons: `Can feel bulky when fully loaded with gear.`,
        bestFor: `Handymen, contractors, or organized kitchen enthusiasts needing portable storage.`,
        vs: `Crushes messy loose drawers (instant access to everything) and outperforms flimsy fabric organizers that fall apart quickly.`
      },
      {
        name: "Meguiar's Ultimate Wash and Wax",
        short: '2-in-1 cleaner and shine for appliances, counters, and stainless steel.',
        why: `Want that showroom sparkle on your fridge or counters without harsh chemicals? This pH-neutral wash and wax cleans, shines, and protects in one easy step—safe for all kitchen surfaces with no swirl marks or streaks. Perfect for quick maintenance between deep cleans, leaving everything glossy and protected.`,
        pros: `Efficient 2-in-1 formula saves time and effort; gentle on delicate finishes like stainless steel.`,
        cons: `Foamy residue requires thorough rinsing for best results.`,
        bestFor: `Homeowners focused on easy kitchen and appliance maintenance.`,
        vs: `Saves time over buying separate cleaners and waxes; delivers professional results at home.`
      },
      {
        name: 'Splatypus Jar Spatula',
        short: 'Flexible scraper gets every last bit from jars—no waste.',
        why: `Tired of leaving peanut butter or mayo behind in the jar? This cleverly shaped spatula flexes into every corner for zero-waste scraping, saving money and reducing frustration over time. Dishwasher-safe and tough enough for daily use on sticky jars of spreads, sauces, or condiments.`,
        pros: `Maximizes every drop of product for real savings; fully dishwasher-safe for easy cleanup.`,
        cons: `Extremely sticky residues may need a quick soak beforehand.`,
        bestFor: `Frequent jar users like bakers and sauce lovers who hate waste.`,
        vs: `Outperforms spoons or knives (complete corner scrape without mess or injury risk).`
      }
    ],
    advice: `Start with the angled measuring cups for everyday precision, then add the marble salt cellar for elegant speed. Pro tips: Hand-wash stone and plastic items to maximize lifespan, and look for bundle sets for the best value. Pair these with our full 50+ product grid to build a kitchen you'll love using.`,
    conclusion: `These reliable tools cut out kitchen frustration and add real joy to every meal prep. They're not just gadgets—they're upgrades that pay off daily. Dive into the full product grid for 50+ more vetted picks. Questions or favorites? Drop a comment below!`
  },
  {
    slug: '2026-04-29-outdoor-survival-essentials',
    title: 'Best Outdoor Survival Essentials Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Compact, reliable gear for hikes, camping, and emergencies—multi-use tools that pack light but perform under pressure.',
    intro: `Mother Nature doesn't send advance warnings, so your gear needs to be ready when you are. We've selected these compact essentials that multitask effectively, survive rough abuse, and come backed by real-user proof from harsh conditions. No bulky nonsense—just smart picks that keep you safe, sorted, and moving on hikes, camps, or roadside stops.`,
    products: [
      {
        name: '6 Tools IN ONE Versatile Multitool Pen',
        short: 'EDC multitool disguised as an everyday pen.',
        why: `This slim pen hides 6 essential tools (screwdriver bits, ruler, bubble level, stylus)—ideal for quick trail fixes, camp setups, or office tweaks without lugging a toolbox. It's pocket-friendly engineering at its best, fitting seamlessly into your daily carry while handling light tasks reliably.`,
        pros: `Ultra-compact design you'll actually carry; combines endless functions into one sleek item.`,
        cons: `Small tool sizes best for light-duty tasks only, not heavy construction.`,
        bestFor: `Hikers, campers, engineers, and on-the-go DIYers.`,
        vs: `More versatile than bulky multitools; always with you unlike full kits.`
      },
      {
        name: '14-in-1 Survival Kit',
        short: 'All-in-one essentials for fire, shelter, cutting, and navigation.',
        why: `One compact pouch covers the basics: wire saw, fire starter, compass, whistle, and more—perfect for hikes, overnights, or car kits. Organized layout deploys fast in stress, lightweight enough for daypacks without weighing you down.`,
        pros: `Comprehensive coverage in a single lightweight package; proven in real emergencies.`,
        cons: `Requires practice to use tools efficiently under pressure.`,
        bestFor: `Outdoor adventurers, hikers, and emergency preppers.`,
        vs: `One organized kit beats scrambling for scattered individual items.`
      },
      {
        name: 'Pink Car Emergency Kit',
        short: 'Roadside must-haves in a highly visible pink case.',
        why: `Jumper cables (10ft), first aid basics, LED flare, tire gauge, and more—bright pink makes it impossible to miss in your trunk. Covers common breakdowns quickly, thoughtful for solo drivers or gifting to newbies.`,
        pros: `Complete set for most scenarios; easy-to-spot color speeds access.`,
        cons: `Check/replace batteries and flares annually for reliability.`,
        bestFor: `Frequent drivers, road-trippers, and safety-conscious families.`,
        vs: `Full ready kit vs buying pieces separately over time.`
      },
      {
        name: 'Inspection Borescope Camera with 4.3" IPS Screen',
        short: 'Waterproof camera for peeking into tight spaces—16.5ft cable.',
        why: `Diagnose engine issues, plumbing clogs, or trailside repairs without disassembly. Standalone 4.3-inch IPS screen (no phone needed) delivers clear views, portable for field use with IP67 waterproof camera head.`,
        pros: `Generous cable length; bright screen works standalone.`,
        cons: `Very narrow passages can be tricky to navigate.`,
        bestFor: `Mechanics, campers, and DIY troubleshooters.`,
        vs: `No app/phone dependency unlike Bluetooth models.`
      }
    ],
    advice: `Carry the multitool pen daily as EDC; add the full kit for overnights or remote trips. Test all gear yearly, layer smart clothing over gadgets, and practice deployment. Check our grid for complementary items like lights or bags.`,
    conclusion: `Stay prepared without extra weight—these essentials deliver peace of mind on every adventure. Browse the full product grid for 50+ more outdoor-tested gems. Share your go-to gear in the comments!`
  },
  {
    slug: '2026-04-29-tech-fitness-gear',
    title: 'Top Tech Fitness Gear Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Smart trackers and wearables that provide real insights and motivation—no subscriptions required.',
    intro: `Fitness tech has exploded, but too many devices track vanity metrics without delivering value. These picks offer actionable data, exceptional battery life, and seamless integration for serious athletes and casual users alike. Curated for reliability in workouts, runs, and daily health monitoring.`,
    products: [
      {
        name: 'Apple Watch Series 9',
        short: 'Health and fitness powerhouse with innovative double-tap gesture.',
        why: `Powered by the S9 chip, this watch features a super-bright always-on display and double-tap for no-touch control during runs or lifts. Tracks heart rate, sleep, crashes, and more with all-day battery—perfect iPhone companion for wellness without constant charging.`,
        pros: `Intuitive gestures and safety features like fall detection; seamless Apple ecosystem integration.`,
        cons: `Best in iOS ecosystem; premium price point.`,
        bestFor: `Apple users prioritizing health and convenience.`,
        vs: `Gesture controls beat button-mashing; brighter screen than predecessors.`
      },
      {
        name: 'Garmin Forerunner 265 Running Smartwatch',
        short: "Runner's essential with AMOLED display and marathon GPS battery.",
        why: `Up to 13 days smartwatch mode or 20 hours GPS tracking on one charge, sunlight-readable AMOLED touchscreen, and button controls for sweaty gloves. Detailed metrics (pace, HR zones, recovery) without monthly fees—built for serious training.`,
        pros: `Exceptional battery crushes competitors; deep training insights.`,
        cons: `Interface has a learning curve for new users.`,
        bestFor: `Dedicated runners, triathletes, and data-driven athletes.`,
        vs: `Battery life and no-subs model outperform most smartwatches.`
      },
      {
        name: 'Govee RGBIC Smart Table Lamp',
        short: 'Customizable mood lighting for home gym or workout vibes.',
        why: `RGBICWW tech creates segmented multi-color effects, 500 lumens brightness, and adjustable whites (2700K-6500K)—app/voice control sets energizing scenes for workouts or recovery. Compact table design fits any space.`,
        pros: `Versatile colors and brightness levels; easy smart home integration.`,
        cons: `Initial app setup takes a few minutes.`,
        bestFor: `Home gym owners enhancing workout atmosphere.`,
        vs: `Segmented lights > basic single-color bulbs for immersion.`
      }
    ],
    advice: `Choose based on your ecosystem (Apple for simplicity, Garmin for depth). Charge weekly, pair with heart rate straps for accuracy, and use insights to adjust training—not just track.`,
    conclusion: `Elevate your fitness with gear that motivates through real data. Check the full grid for more tech and accessories. What's your must-have tracker? Let us know!`
  },
  {
    slug: '2026-04-29-top-gifts-home',
    title: 'Top Home Gifts Worth Buying in 2026',
    date: '2026-04-29',
    desc: 'Thoughtful, durable home accents and organizers that impress without being generic.',
    intro: `The best gifts blend utility, beauty, and sentiment—perfect for housewarmings, holidays, or "just because." These picks are handpicked for lasting appeal, practical use, and that wow factor guests notice.`,
    products: [
      {
        name: 'Samhita Handmade Mango Wood Tree of Life Keepsake Box',
        short: 'Artisan-engraved wood box for jewelry or mementos.',
        why: `Hand-carved Tree of Life design on warm mango wood with a vintage flame finish—stores small treasures like rings or notes with meaningful symbolism. Sturdy lid and natural grain age beautifully, becoming more personal over time.`,
        pros: `Unique handcrafted details; compact yet protective for valuables.`,
        cons: `Sized for small items only, not bulky storage.`,
        bestFor: `Sentimental gifters for birthdays or housewarmings.`,
        vs: `Artisan quality > mass-produced plastic boxes.`
      },
      {
        name: '1 Gallon Glass Cookie Jars with Lids',
        short: 'Airtight pantry jars for bulk flour, sugar, or snacks.',
        why: `Each 3.8L jar fits a full 5lb bag of staples like rice or cereal—clear glass lets you see contents at a glance, airtight lids keep everything fresh, and they stack neatly to end cluttered pantries.`,
        pros: `Generous capacity with perfect seal; aesthetic upgrade for shelves.`,
        cons: `Glass is heavy when fully loaded.`,
        bestFor: `Bakers, bulk shoppers, and kitchen organizers.`,
        vs: `Visible airtight storage > opaque plastic bins.`
      },
      {
        name: 'STEM Magnetic Tiles 70-Piece Set with Idea Book',
        short: 'Magnetic building tiles for endless STEM creativity.',
        why: `70 large pieces in 5 shapes plus an idea book spark hours of building—strong magnets hold firm for stable towers or vehicles, BPA-free for safe play, perfect for solo or group fun.`,
        pros: `Educational STEM boost; durable for repeated builds.`,
        cons: `Requires a storage solution for all pieces.`,
        bestFor: `Parents and kids 3+ fostering imagination.`,
        vs: `More shapes and capacity than smaller starter sets.`
      }
    ],
    advice: `Personalize with a handwritten note tying to the recipient's style. Opt for sets where possible for extra value, and consider pairing with complementary home items from our grid.`,
    conclusion: `These gifts create lasting memories and practical joy. Explore the full collection for more ideas tailored to any home. Tag a friend who needs this!`
  },
  {
    slug: '2026-04-29-batch10-latest-picks',
    title: 'Batch 10 Latest Picks: Hidden Gems Worth Adding to Cart',
    date: '2026-04-29',
    desc: 'Freshly added products blending utility, fun, and smart value from our newest batch.',
    intro: `Our latest product batch brings hidden gems we've vetted for real worth—practical upgrades, clever solves, and delightful surprises under $50. Here's the standout picks worth your attention.`,
    products: [
      {
        name: 'CRAFTSMAN Shallow Socket, Metric, 1/2-Inch Drive, 10mm, 12-Point',
        short: '"Where is my 10mm?"—solved forever.',
        why: `That eternal mechanic question answered: this chrome 10mm socket grips tight without slipping, 12-point design for quick starts, corrosion-resistant for garage longevity. Lifetime warranty backs it up.`,
        pros: `Secure hold prevents stripping; built tough with warranty.`,
        cons: `Single size (buy sets for full coverage).`,
        bestFor: `Mechanics and DIYers tired of lost or rounded bolts.`,
        vs: `Won’t slip like cheap imports; pro quality at home price.`
      },
      {
        name: 'STEM Magnetic Tiles 70-Piece Set with Idea Book',
        short: '70-piece magnets + ideas for creative building.',
        why: `Kickstart STEM learning with 70 magnetic tiles in 5 shapes and an idea book—build vehicles, towers, anything. Strong magnets ensure stability, safe materials for young builders.`,
        pros: `Sparks imagination and education; holds up to rough play.`,
        cons: `Bag or bin recommended for storage.`,
        bestFor: `Kids 3+, parents wanting screen-free fun.`,
        vs: `Larger set with more variety than basic kits.`
      }
    ],
    advice: `Prioritize must-solves like the socket for immediate wins. Bundle with similar tools for savings, and check the full grid for batch context.`,
    conclusion: `These new additions are ready to earn their keep. See all 50+ in the product grid and grab your favorites today. What caught your eye?`
  }
];

blogs.forEach(blog => {
  // Enrich each product with image and affiliate URL from JSON
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
      <h2>Buying Advice & Recommendations</h2>
      <p style="line-height: 1.6; font-size: 1.1em;">${blog.advice}</p>
    </div>
    <div class="section-header" style="margin-top: 2rem;">
      <h2>Final Thoughts</h2>
      <p style="line-height: 1.6;">${blog.conclusion}</p>
      <a href="/#products" style="font-weight: bold; color: #ff6b35;">← Back to Full Product Grid</a>
    </div>
    <p style="text-align: center; margin: 3rem 0;"><a href="/blog.html" class="cta-button" style="display: inline-block; padding: 1rem 2rem; background: #007bff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Read More Helpful Posts</a></p>
  </article>
  <footer style="margin-top: 4rem; padding: 2rem; background: #333; color: white; text-align: center;">
    <p>© 2026 WorthIt Goods. Amazon affiliate disclosure: We earn from qualifying purchases at no extra cost to you.</p>
  </footer>
</body>
</html>`;

  fs.writeFileSync(path.join(blogDir, `${blog.slug}.html`), content);
  fs.writeFileSync(path.join(siteBlogDir, `${blog.slug}.html`), content);
});

console.log('Generated 5 improved blog posts: richer conversational paragraphs, product images, enhanced spacing/layout with cards, pros/cons grids. Files: blog/*.html and _site/blog/*.html. Run ls -lh blog/ to check sizes.');
