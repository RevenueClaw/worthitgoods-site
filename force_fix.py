#!/usr/bin/env python3
"""Force-fix all product descriptions. Run THIS file - verified to persist."""
import json, shutil
from pathlib import Path

DATA = "data/sample_products.json"
BACKUP = "data/sample_products_backup_20260708.json"

# Read backup first
with open(BACKUP) as f:
    prods = json.load(f)

desc_fixes = {
    0: "This patriotic dog bandana is made from quality materials that hold up to outdoor play and repeated washing. The reversible design gives you two looks in one, and the fit stays comfortable on active dogs. A simple way to show some spirit that actually lasts.",
    1: "Filling water balloons the old way is tedious. This self-sealing design fills and ties 200+ balloons in minutes instead of an hour. More playing, less prep.",
    2: "A humorous take on Independence Day that gets laughs without being offensive. The print holds up wash after wash, and the cotton blend is comfortable enough for a full day at the BBQ. Quality humor that delivers.",
    3: "Outdoor decorations take a beating from weather, but this banner uses fade-resistant materials that keep colors bright all season long. At 71x44 inches, it makes a real statement on porches, fences, or walls. Easy to hang, hard to ignore.",
    4: "This patriotic car sign adds a festive touch to your 4th of July display. The wooden star design is more refined than plastic alternatives, and the LOVE message is universally appealing. Simple, tasteful, durable.",
    5: "These disposable forks bring the color without compromising on strength. Heavy-duty enough for burgers and BBQ sides, they won't snap or bend like cheap alternatives. Patriotic style that actually functions at the picnic table.",
    6: "A double-sided burlap garden flag with a charming patriotic cat design that is printed to last through sun and rain. The 12x18 inch size fits standard flag stands, and the artwork is cute without being tacky. A fun twist on traditional holiday decor.",
    7: "This paddle catch game set gets kids outside and active without screens. The oversized paddles make catching easy for younger kids, and the 4-player set means nobody sits out. Simple outdoor fun that actually works for mixed ages.",
    8: "Reusable non-woven tote bags with a patriotic print that is perfect for party favors or gift bags. They are sturdy enough to hold candy and small gifts, and guests can reuse them long after the celebration ends. Practical party favors that do not get thrown away.",
    9: "A 6-color set of bubble bottles that keeps kids entertained for hours at a fraction of the cost of single bottles. The wands produce big bubbles, and the color variety adds to the fun. Perfect for party bags, park trips, or backyard play dates.",
    10: "This 31.5x72 inch coloring tablecloth keeps kids entertained during holiday gatherings while protecting your table. The patriotic design is detailed enough to engage multiple kids at once, and the paper takes crayons and markers well. Quiet activity for the kids table.",
    11: "A bucket ball toss game that packs down into a carry case for beach trips, camping, or backyard parties. The weighted bases keep the buckets standing in light wind, and the gameplay is simple enough for all ages. Portable family fun.",
    12: "An embroidered windsock with fade-resistant construction that keeps its colors flying through sun and storms. The 40-inch length catches the breeze well, and the reinforced stitching prevents unraveling. Durable outdoor decor that actually earns its spot.",
    13: "Reusable smoothie pouches that eliminate single-use waste at pool parties, picnics, and beach days. The reclosable design means drinks do not spill in transit, and the assorted styles give everyone their pick. Eco-friendly convenience that actually works.",
    14: "A 1000-piece jigsaw puzzle with Kodak-quality image reproduction that makes the assembly experience satisfying. The pieces fit well without frustrating gaps, and the patriotic theme is perfect for summer family nights. Quality time in a box.",
    15: "An insulated tumbler that keeps drinks cold for 10 hours without the condensation mess of standard glassware. The 360-degree sippable lid is poolside-ready, and the shatterproof construction means no broken glass near the water. Better than a wine glass for real life.",
    16: "A patriotic porch goose costume that turns a simple lawn statue into a neighborhood conversation starter. The fabric is weather-resistant and fits standard 23-inch goose statues securely. Seasonal decor with personality.",
    17: "A 54-block wooden tower stacking game that builds up to 4 feet tall for maximum drama before the crash. The carry bag makes it beach and campsite-ready, and the included custom rules board adds variety to keep it fresh. Giant Jenga energy without the brand markup.",
    18: "This heavy-duty rechargeable spotlight is several times brighter than standard flashlights, with a beam that reaches across fields and down trails. USB rechargeable means no hunting for batteries, and the rugged build survives drops and weather. Serious illumination when you need it most.",
    19: "Patriotic multicolor Crocs that let you show some spirit without sacrificing comfort. The classic Crocs design means they are lightweight, easy to clean, and comfortable for all-day wear at the BBQ or parade. Summer footwear that does not take itself too seriously.",
    20: "A 60-inch flannel tortilla blanket that is soft enough for cozying up and big enough to wrap yourself in like a burrito. The 285GSM flannel is noticeably thicker than novelty blankets half the price. Self-care with a sense of humor.",
    21: "A pleated fan flag set that adds dimension and movement to your outdoor display. The brass grommets and zip ties make installation on porch railings or fences quick and secure. Better than flat flags for visual impact.",
    22: "An inflatable paddleboard that is stable enough for beginners yet responsive enough for experienced riders. The included kayak seat adds versatility, and the full accessory package means you are ready to hit the water right out of the box.",
    23: "A custom photo Hawaiian shirt that makes for an unforgettable gift at family gatherings or bachelor parties. The print quality is sharp and durable, and the fabric is breathable enough for real summer wear. The gift that keeps getting laughs.",
    24: "A rechargeable LED flying disc with 108 RGB lights that create stunning patterns after dark. Waterproof and durable enough for serious throws, it turns an evening park hang into something memorable. The frisbee upgrade you did not know existed.",
    25: "A double cotton hammock with a steel stand that sets up anywhere with no trees needed. The 450-pound capacity handles two adults, and the upgraded polyester end strings resist fraying longer than standard cotton. Backyard luxury in minutes.",
}

# Products 40-58 (index 39-57) - originally had Amazon copy not "why worth it" voice
for i in range(39, 58):
    p = prods[i]
    t = p.get("title","").lower()
    
    if "spotlight" in t:
        prods[i]["description"] = "This heavy-duty rechargeable spotlight is several times brighter than standard flashlights, with a beam that reaches across fields and down trails. USB rechargeable means no hunting for batteries, and the rugged build survives drops and weather. Serious illumination when you need it most."
    elif "screwdriver" in t:
        prods[i]["description"] = "One screwdriver that covers nearly everything you will encounter around the house. The ratcheting mechanism lets you drive screws without repositioning, and the bit storage in the handle means bits do not get lost. The tool you will reach for first."
    elif "squishy" in t or "toy" in t:
        prods[i]["description"] = "30 soft kawaii squishies in a variety pack perfect for party bags, classroom rewards, or desk stress relief. The assortment of cute styles means every pack is a surprise, and the soft texture is satisfying to squish. Small joy, big smiles."
    elif "slushie" in t or "slushi" in t:
        prods[i]["description"] = "No ice needed - the Ninja SLUSHi RapidChill Technology freezes liquid evenly for perfect slushies, margaritas, or frozen coffee drinks in minutes. It transforms a countertop appliance into a party centerpiece that actually gets used."
    elif "raspberry" in t or "retroflag" in t or "pi case" in t or "game5pi" in t:
        prods[i]["description"] = "A retro gaming case that turns your Raspberry Pi into a proper console with safe shutdown and reset support. The iconic design is a conversation starter, and the built-in cooling keeps your Pi running during marathon gaming sessions. Form and function, properly executed."
    elif "challenge coin" in t or "dumpster fire" in t:
        prods[i]["description"] = "This Dumpster Fire Challenge Coin combines humor with solid construction - a bold reminder that the strongest steel is forged in the craziest fires. The detailed enamel design makes it a desk-worthy conversation piece. The perfect gag gift for anyone surviving a tough year."
    elif "charger" in t and ("30w" in t or "uno" in t or "ugreen" in t):
        prods[i]["description"] = "30W GaN charging in a compact block that is small enough to take anywhere without the bulk of traditional chargers. Fast enough for iPhones and iPads, and the GaN technology runs cooler than older charger designs. Travel-friendly power delivery."
    elif "emergency food" in t or "freeze dried" in t:
        prods[i]["description"] = "A 20-serving emergency food supply that is actually shelf-stable for years and tastes decent when you need it most. The flood-safe bucket stores easily, and the freeze-dried preparation means just add water when the time comes. Practical preparedness without the prepper aesthetic."
    elif "golf" in t and "towel" in t:
        prods[i]["description"] = "A funny golf towel that is genuinely absorbent, with a hilarious message that gets laughs on the course. The microfiber material cleans clubs and balls effectively without scratching surfaces. Humor that holds up to repeated washing."
    elif "kinetic sand" in t:
        prods[i]["description"] = "Kinetic sand ice cream playset that keeps kids entertained for hours with mess-free sensory play. The moldable sand holds shapes surprisingly well, and the ice cream-themed tools add imaginative play. Screen-free fun that does not end up all over the floor."
    elif "100w" in t and "charger" in t:
        prods[i]["description"] = "100W GaN charger that can juice up a laptop, tablet, and phone simultaneously without overheating. The triple-port design means one charger replaces three bricks. Travel-friendly power for the whole family."
    elif "ninja" in t and "blend" in t:
        prods[i]["description"] = "A 1200-watt blender motor that actually has the power to crush ice and frozen fruit into silky smooth blends. The pitcher design minimizes the annoying vortex that leaves chunks at the top. Reliable blending power at a reasonable price."
    elif "docking station" in t and "phone" in t:
        prods[i]["description"] = "A wood phone docking station that keeps your daily carry organized in one spot. The natural wood finish looks clean on any desk or nightstand, and the multiple slots accommodate phone, watch, keys, and wallet. Morning routine simplified."
    elif "under armour" in t or "duffle" in t:
        prods[i]["description"] = "A durable duffle bag with smart organization that makes packing and unpacking painless. The padded shoulder strap stores away when not needed, and the large front pocket keeps essentials accessible. Built for the gym and beyond."
    elif "souper cube" in t or "freezer mold" in t:
        prods[i]["description"] = "Silicone freezer molds with lids that make meal prep actually practical. The generous portions are real servings, not tiny cubes, and the flexible silicone releases frozen food without a fight. The lid means no freezer burn between batches."
    elif "geekpi" in t or "pi 5" in t:
        prods[i]["description"] = "A purpose-built case for Raspberry Pi 5 that includes a PCIe adapter for NVMe storage upgrades. The cooling design keeps the Pi running cool even under load, and the compact form factor fits any desk setup. Essential for Pi power users."

# Products 59-78 - most already had decent descriptions, but let's fix #59 which had placeholder
p = prods[58]
t = p.get("title","").lower()
if "can mustache" in t:
    prods[58]["description"] = "Instant party upgrade - the Novelty Can Mustache Clip turns ordinary cans into funny faces for birthdays, BBQs, and bachelor parties. It is reusable, hilarious, and the easiest icebreaker you will ever own. The party prop that keeps on giving."

# Products 88-118 (index 87-117) - the "excellent value" filler batch
fixes_88_118 = {
    87: "Most kitchen towels are either decorative and useless or absorbent and ugly. This one manages to be both handsome and functional, with a weave that actually dries dishes without leaving lint. Good enough to hang on display, rugged enough for daily abuse.",
    88: "This web launcher spider string shooter delivers chaos and giggles with every shot. Safe for indoor and outdoor play, easy to reload, and hours of entertainment for kids. Pure silly fun.",
    89: "A travel backpack that balances organization with comfort for long days exploring. The compartments are thoughtfully laid out for tech and clothes, and the padding distributes weight evenly. The kind of bag that makes travel less stressful.",
    90: "An 80-hour rechargeable neck light that keeps your hands free while illuminating exactly what you are looking at. Perfect for reading in bed, working on projects, or walking the dog at night. The battery life means weeks between charges.",
    91: "The Victorinox Tinker is the gold standard of everyday carry tools for good reason. Quality steel, precise fit and finish, and a tool selection that handles 90% of daily needs without being bulky. The original multitool that has never been bettered.",
    92: "A coffee mug that dog lovers will actually want to display. The print is crisp and dishwasher-safe, and the 12oz capacity is the perfect morning serving size. The kind of gift that gets used every single day.",
    93: "A tall floor vase that fills empty corners with intentional style. The finish and proportions work with modern or traditional decor, and the stable base means it will not tip with fresh flowers. Better than leaving that corner empty.",
    94: "This Cerakote trim coat restores faded plastic trim on cars, trucks, and SUVs to a like-new finish that lasts through washes and weather. The ceramic formulation bonds at the molecular level for durability that spray-on products cannot match.",
    95: "A traditional weather station with precision analog instruments that do not need batteries or apps. The barometer, thermometer, and hygrometer are accurate enough for practical use and handsome enough to justify wall space. Timeless and functional.",
    96: "DND dice embedded directly into handmade beer glasses for geeky barware that actually looks good. Each one is unique, holds a proper pour, and the quality is good enough for daily use. The conversation starter that earns its cabinet space.",
    97: "A card that actually makes someone laugh without trying too hard. Printed on substantial cardstock that feels quality in hand, with a design that is clever without being mean. The kind of card that ends up on the fridge.",
    98: "A witty dish towel that brings personality to your kitchen while actually drying dishes. The linen-cotton blend absorbs well and washes clean without fading. Functional humor for people who cook.",
    99: "A birthday card that roars with personality. The design is playful without being childish, making it appropriate for kids and adults alike. Quality cardstock and a clever punchline make it a card worth keeping.",
    100: "Artisan-style ceramic bowls with a matte finish that feels substantial and intentional. The durable glaze means they will survive daily use and dishwasher cycles without losing their look. Everyday tableware that elevates the meal.",
    101: "A unique home accent piece that adds character to any room. The design is distinctive without being loud, and the quality of construction ensures it will hold up over time. The kind of piece that makes a space feel personal.",
    102: "Cat-themed socks that are soft enough for lounging but sturdy enough for real wear. The design is subtle enough for daily use, and the blend keeps its shape wash after wash. A small joy for cat people.",
    103: "A magnetic wooden chess set that lets you play anywhere without pieces sliding around. The board folds compactly for travel, and the pieces have a satisfying weight that feels right. Strategy without the setup anxiety.",
    104: "A handmade leather journal that makes you want to write something worth keeping. The paper takes fountain pen ink without bleeding, and the binding lies flat when open. An object of permanence in a disposable world.",
    105: "The Emotional Pickle is a quirky, lovable plush that is perfect for sending a smile. Soft, huggable, and guaranteed to lighten the mood of anyone who receives it. The sentimental gift that stands out.",
    106: "A premium leather messenger bag that combines classic style with modern functionality. The buffalo leather develops character with age, and the padded laptop compartment protects your gear. Built to last a decade.",
    107: "Handmade crochet chicken coasters that add personality to your table while protecting surfaces. Each one is crafted by hand, so no two are exactly alike. Functional folk art that brings warmth to every meal.",
    108: "100% pure Wagyu beef tallow for cooking that adds incredible depth of flavor to everything from roasted vegetables to perfect french fries. Higher smoke point than butter, richer taste than oils. The secret weapon of great home cooking.",
    109: "A smart battery charger that handles both 6V and 12V batteries with automatic maintenance. It detects battery health, will not overcharge, and can revive deeply discharged batteries. Set it and forget it battery care.",
    110: "Double-sided mounting tape that actually holds what you put up. The heavy-duty bond works on brick, wood, metal, and drywall without nails or screws. The go-to solution for hanging anything without making holes.",
    111: "An electric knife that makes carving roasts, slicing bread, and cutting through tough vegetables effortless. The serrated blades stay sharp and the ergonomic grip reduces hand fatigue. More useful than you would think.",
    112: "Whipped beef tallow for skin that is surprisingly effective as a moisturizer. Rich in fat-soluble vitamins, it absorbs without feeling greasy and calms dry patches better than many commercial creams. Old-school skincare that actually works.",
    113: "A dry erase board that looks good enough for your home office or kitchen. The surface erases cleanly without ghosting, and the magnetic function adds versatility. Organization that does not look like office surplus.",
    114: "A convertible clip fan that works on your desk, clips to a tent pole, or hangs from a stroller. The quiet motor will not disturb sleep, and the adjustable head directs air exactly where needed. Cooling that follows you around.",
    115: "A cold-process soap bar with natural oils that clean without stripping your skin. Free from the harsh detergents in commercial soap, it leaves skin feeling clean and moisturized. Simple ingredients, better results.",
    116: "Good kitchen shears are the most-used tool in any kitchen, yet most people make do with flimsy ones. These are built with proper stainless steel that stays sharp, and they come apart for easy cleaning. The workhorse your kitchen deserves.",
    117: "A unique home accent piece with a distinctive design that adds character to any room. The quality of construction ensures it will hold up over time. The kind of piece that makes a space feel personal.",
}

# Apply all fixes
count = 0
for idx, desc in {**desc_fixes, **fixes_88_118}.items():
    prods[idx]["description"] = desc
    count += 1

# Also fix remaining weak descriptions from products 39-57
for i in range(39, 58):
    p = prods[i]
    t = p.get("title","").lower()
    desc = p.get("description","")
    if len(desc) < 50 or "excellent value" in desc.lower() or "NO ICE NEEDED" in desc.upper() or desc.startswith("EXTRA BRIGHT"):
        print(f"  ⚠️ Still weak at index {i}: {p['title'][:40]}")
    else:
        count += 0  # Already counted above through range fix

# Final check before saving
bad_before = sum(1 for p in prods if "excellent value and quality" in p.get("description","").lower())
print(f"Bad descriptions before save: {bad_before}")

# SAVE
with open(DATA, "w") as f:
    json.dump(prods, f, indent=2)

# Verify
with open(DATA) as f:
    prods2 = json.load(f)

bad_after = sum(1 for p in prods2 if "excellent value and quality" in p.get("description","").lower())
short_after = sum(1 for p in prods2 if len(p.get("description","")) < 50)
print(f"Bad placeholders after save: {bad_after}")
print(f"Too-short descriptions: {short_after}")
print(f"Total fixes applied: {count}")
print(f"File size: {Path(DATA).stat().st_size} bytes")
print(f"\nSample:")
print(f"  Product 1: {prods2[0]['description'][:80]}")
print(f"  Product 89: {prods2[88]['description'][:80]}")
print(f"  Product 118: {prods2[117]['description'][:80]}")