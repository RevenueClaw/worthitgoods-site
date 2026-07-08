#!/usr/bin/env python3
"""
WorthItGoods — Description Enhancer
Generates compelling product descriptions for weak/placeholder entries
using keyword analysis of the product title.
"""

import json
import re
import shutil
from pathlib import Path

DATA_FILE = "data/sample_products.json"
BACKUP_FILE = "data/sample_products_backup_20260708.json"


def categorize(title, blurb=""):
    """Determine product category from title keywords."""
    t = title.lower()
    b = blurb.lower()
    text = f"{t} {b}"
    
    if any(w in text for w in ["shirt", "t-shirt", "tee ", "clog", "crocs", "hat", "cap", "socks", "apron", "sleeve", "sweatshirt"]):
        return "apparel"
    if any(w in text for w in ["dog", "cat", "pet", "goose", "lawn statue", "porch goose"]):
        return "pets"
    if any(w in text for w in ["balloon", "bubble", "toss", "game", "puzzle", "flying disc", "hammock", "paddle board", "paddleboard", "squishy", "slushie", "tower stacking", "coloring", "toy"]):
        return "outdoor"
    if any(w in text for w in ["decorations", "banner", "flag", "windsock", "bunting", "vase", "coaster", "lamp", "journal", "keepsake", "clock", "weather station", "dry erase"]):
        return "home_decor"
    if any(w in text for w in ["kitchen", "spatula", "measuring cup", "measur", "cookie jar", "jar", "salt cellar", "bowl", "grater", "zester", "cutlery", "knife", "scissors", "utensil", "mixing", "scoop", "towel", "tallow", "mug", "soup", "coffee"]):
        return "kitchen"
    if any(w in text for w in ["blanket", "throw", "pillow", "plush", "crochet"]):
        return "home"
    if any(w in text for w in ["tool", "screwdriver", "socket", "wrench", "drill", "power tool", "organizer", "tool bag", "tape", "clamp", "ratchet"]):
        return "tools"
    if any(w in text for w in ["car", "auto", "jump starter", "emergency kit", "license plate", "charger", "battery"]):
        return "automotive"
    if any(w in text for w in ["watch", "smartwatch", "garmin", "forerunner", "apple watch"]):
        return "tech"
    if any(w in text for w in ["raspberry pi", "pi case", "borescope", "cable", "charger", "usb-c", "usb c", "gan"]):
        return "electronics"
    if any(w in text for w in ["survival", "flashlight", "spotlight", "cooler", "lunchbox", "pocket knife", "swiss army", "multitool", "camping"]):
        return "outdoor_gear"
    if any(w in text for w in ["golf", "sunglasses", "fan", "neck light"]):
        return "lifestyle"
    if any(w in text for w in ["card", "gift", "magnetic tiles", "stem", "toy"]):
        return "gifts"
    return "general"


def gen_description(title, blurb, category):
    """Generate a good 'Why It's Worth It' description based on title analysis."""
    t = title.lower()
    
    # --- APPLICABLE ---
    if any(w in t for w in ["t-shirt", "tee ", "shirt", "apron", "clog", "crocs"]):
        return f"This {title[:30].strip()} isn't just about the look—it's made from quality materials that hold up wash after wash while keeping the design sharp. Comfortable enough for everyday wear, it's the kind of thing you reach for again and again. A small upgrade to your daily routine that actually delivers."
    
    # --- PETS ---
    if any(w in t for w in ["dog bandana", "cat garden flag", "porch goose", "dog", "cat", "pet"]):
        return f"Most pet accessories look cute for five minutes then fall apart, but this one is built to last through outdoor play and repeat use. It adds personality without sacrificing durability—something both you and your pet will appreciate. A simple way to make your pet stand out that actually holds up."
    
    # --- OUTDOOR ---
    if any(w in t for w in ["balloon", "water balloon"]):
        return f"Anyone who's filled water balloons the old way knows the pain. This self-sealing design cuts setup time from an hour to minutes, so you spend more time playing and less time tying knots. It's one of those innovations that makes you wonder why nobody thought of it sooner."
    if any(w in t for w in ["toss", "catch", "paddle", "yard game", "lawn game", "tower stacking"]):
        return f"Backyard games often end up collecting dust because they're too complicated or don't hold up. This one is the opposite—it's simple to learn, built from quality materials that survive being knocked around, and brings people together without needing a phone or screen. The kind of fun that actually works for mixed ages."
    if any(w in t for w in ["puzzle", "jigsaw"]):
        return f"A 1000-piece puzzle is the perfect way to unplug for an evening, and this one delivers with crisp image quality and pieces that fit satisfyingly together without frustrating gaps. Thick board construction means it'll survive multiple assemblies. Quality time, literally."
    if any(w in t for w in ["paddleboard", "paddle board", "sup"]):
        return f"A good paddleboard makes the difference between a fun day on the water and a frustrating one. This inflatable design is stable enough for beginners yet responsive enough for experienced riders, and packs down small enough to throw in the trunk. The included kayak seat is a bonus that adds another way to enjoy it."
    if any(w in t for w in ["hammock", "stand"]):
        return f"Nothing beats a lazy afternoon in a good hammock, and this double-sized cotton one with a steel stand means you don't need trees to enjoy it. The 450lb capacity handles two people easily, and the carry bag makes it portable for camping or the beach. Quality relaxation that sets up anywhere."
    if any(w in t for w in ["flying disc", "led"]):
        return f"This isn't your standard frisbee—the built-in RGB LEDs make it visible after dark, turning evening park hangs into something magical. Rechargeable, waterproof, and durable enough for serious throws, it's the kind of simple innovation that makes you want to go outside."
    
    # --- HOME DECOR ---
    if any(w in t for w in ["flag", "banner", "windsock", "bunting"]):
        return f"Outdoor decorations take a beating from sun and weather, but this one is built with fade-resistant materials that keep it looking fresh season after season. Easy to hang with reinforced grommets, it's a simple way to show some spirit without cheaping out on quality."
    if any(w in t for w in ["lamp", "table lamp", "govee"]):
        return f"Most smart lamps are either dim or complicated. This one nails both brightness and ease with multi-color segments, adjustable white balance from warm to cool, and app/voice control that actually works. It transforms a room's mood without requiring a tech degree to set up."
    if any(w in t for w in ["vase", "bowl", "floor vase"]):
        return f"Finding decor that looks intentional rather than filler is hard. This piece has a clean, artisan feel that works with modern or traditional spaces, and the quality of materials means it won't chip or fade like cheap alternatives. Simple, elegant, actually worth the shelf space."
    if any(w in t for w in ["coaster", "circuit board"]):
        return f"These aren't your typical drink coasters—they're made from real circuit boards, so every set has a unique look that actually sparks conversation. They handle hot and cold drinks without warping and wipe clean in seconds. Functional art for your coffee table."
    if any(w in t for w in ["clock", "weather station"]):
        return f"This traditional weather station combines classic analog style with reliable precision instruments. The barometer, thermometer, and hygrometer give you real-time readings without batteries or apps. A timeless addition to any wall that's both functional and handsome."
    if any(w in t for w in ["journal", "leather journal"]):
        return f"In a world of screens, a quality journal invites you to slow down. This handmade leather one has thick, fountain-pen-friendly paper and a durable binding that lies flat when open. It's the kind of object that makes you want to write something worth keeping."
    if any(w in t for w in ["dry erase", "whiteboard"]):
        return f"Most whiteboards look like office surplus. This magnetic dry erase board has a clean, modern aesthetic that actually looks good in a home office or kitchen, and the surface erases cleanly without ghosting. Practical without being ugly."
    
    # --- KITCHEN ---
    if any(w in t for w in ["spatula", "splatypus", "scraper", "turner"]):
        return f"The Splatypus jar spatula turns a mundane task—scraping the last bits from a jar—into a satisfying experience. Its flexible, friendly design reaches corners and curves that rigid spatulas miss, saving you from wasting the good stuff at the bottom. One of those small kitchen tools you never knew you needed until you have it."
    if any(w in t for w in ["coffee", "mug", "cup"]):
        return f"A good mug makes your morning coffee feel intentional. This one has the right weight, a comfortable handle, and holds enough for a proper serving without getting cold too fast. Small details like the finish and feel in hand make it noticeably better than the standard cabinet filler."
    if any(w in t for w in ["measuring", "measur"]):
        return f"Patented angled measuring cups let you read measurements from above instead of bending down to check the line—a small innovation that makes baking noticeably easier. The clear, durable plastic handles heat and cold without cracking. The kind of upgrade you didn't know you needed until you use them once."
    if any(w in t for w in ["zester", "grater", "cheese grater"]):
        return f"A razor-sharp stainless blade that won't rust and an ergonomic handle that stays comfortable even after extended use make this grater stand out from the pack. The curved design channels force efficiently, so you're not wrestling with your ingredients. Simple, well-made, and noticeably sharper than the grocery store alternatives."
    if any(w in t for w in ["cookie", "jar"]):
        return f"These 1-gallon glass jars with airtight lids end the chaos of half-open bags spilling in your pantry. A full 5lb bag of flour or sugar fits perfectly, and the clear glass lets you see exactly what's left at a glance. The simple upgrade that makes meal prep less frustrating."
    if any(w in t for w in ["knife", "cutlery", "scissors", "kitchen scissors"]):
        return f"Good kitchen shears are one of the most-used tools in any kitchen, yet most people make do with flimsy ones that dull fast. These are built with proper stainless steel blades that stay sharp through heavy use and come apart for easy cleaning. The workhorse your kitchen deserves."
    if any(w in t for w in ["tallow", "beef tallow", "soap"]):
        return f"This cold-process bar uses natural oils without the harsh detergents found in most commercial soaps. Hand-cut and slow-cured, each bar lasts longer than the grocery store alternatives while leaving skin feeling clean, not stripped. Simple ingredients done right."
    if any(w in t for w in ["towel", "dish towel"]):
        return f"Most kitchen towels are either decorative and useless or absorbent and ugly. This one manages to be both handsome and functional, with a weave that actually dries dishes without leaving lint. Good enough to hang on display, rugged enough for daily abuse."
    if any(w in t for w in ["bowl", "ceramic", "matte"]):
        return f"Artisan-style ceramic bowls that look handmade without the artisan price tag. The matte finish feels substantial in hand, and the durable glaze means they'll survive the dishwasher. The kind of everyday tableware that makes a simple meal feel a little more intentional."
    if any(w in t for w in ["utensil", "utensil rest", "crab"]):
        return f"This playful utensil rest from an award-winning design studio solves a real problem—where to put your spoon while cooking. The silicone construction handles heat without melting, and the clever crab design adds personality to your counter. Functional and fun, without being gimmicky."
    if any(w in t for w in ["blender", "ninja"]):
        return f"A 1200-watt motor that actually has the power to crush ice and frozen fruit into silky smooth blends without straining. The pitcher design minimizes the annoying vortex that leaves chunks at the top. Reliable power at a price that doesn't require financing."
    if any(w in t for w in ["ice cream", "slushie", "frozen"]):
        return f"No ice needed—this machine's RapidChill technology freezes liquid evenly for perfect slushies, margaritas, or frozen coffee drinks in minutes. It transforms a countertop appliance into a party centerpiece that actually gets used, not just displayed."
    if any(w in t for w in ["freezer mold", "souper cube"]):
        return f"These silicone freezer trays with lids make batch cooking actually practical. The portion sizes are generous enough for a real meal, and the flexible silicone releases frozen blocks without the usual wrestling match. The lid means no freezer burn between use."
    if any(w in t for w in ["burrito", "tortilla", "blanket"]):
        return f"A 60-inch flannel tortilla blanket that's soft enough for cozying up on the couch and big enough to actually wrap yourself in like a burrito. The 285GSM flannel is noticeably thicker and softer than novelty blankets half the price. Self-care with a sense of humor."
    if any(w in t for w in ["salt cellar"]):
        return f"This 4-inch marble salt cellar elevates a basic kitchen staple into something you'd leave out on the counter. The natural stone keeps salt dry and clump-free, and the lid keeps out dust. A small touch that makes cooking feel more intentional."
    
    # --- TOOLS ---
    if any(w in t for w in ["screwdriver", "ratcheting"]):
        return f"One screwdriver that covers nearly everything—bits for electronics, appliances, and general household fixes all stored in the handle. The ratcheting mechanism lets you drive screws without repositioning, saving time on bigger projects. The kind of tool you reach for instead of digging through the toolbox."
    if any(w in t for w in ["socket", "10mm"]):
        return f"We all know the joke about losing 10mm sockets—now try a quality one that stays put with a 12-point design that grips tight without rounding bolts. Chrome finish resists corrosion through years of garage use. The right tool for the job that won't vanish mid-project."
    if any(w in t for w in ["tool bag", "tool box", "organizer"]):
        return f"A wall-mount power tool organizer solves the universal problem of cluttered workbenches. With dedicated slots, hooks, and a drill bit rack, it keeps everything accessible and off your workspace. The kind of organization upgrade that makes you want to start projects just to use your tidy setup."
    if any(w in t for w in ["multitool", "multi-tool", "pen"]):
        return f"This 6-in-1 multitool pen packs screwdriver bits, a ruler, a level, and a stylus into a form factor that lives in your pocket or bag. It replaces the need to hunt for the right tool for small fixes around the house or office. Engineered smart, not bulky."
    if any(w in t for w in ["all purpose tape", "gorilla tape", "mounting tape"]):
        return f"Double-sided mounting tape that actually holds what you stick to it—even on rough surfaces. The heavy-duty bond works on brick, wood, metal, and drywall without needing nails or screws. The go-to solution for mounting anything without making holes."
    
    # --- AUTOMOTIVE ---
    if any(w in t for w in ["jump starter", "jump-n-carry", "boost"]):
        return f"Dead battery? No need to flag down a stranger with jumper cables. This jump starter is a self-contained power pack that starts your car without needing a second vehicle. Portable enough to keep in the trunk, powerful enough to start a truck. Peace of mind you can carry."
    if any(w in t for w in ["emergency kit", "car emergency"]):
        return f"Unlike flimsy roadside kits with tools that break on first use, this one includes genuinely useful gear—sturdy jumper cables, a proper first aid kit, and tools that won't snap under pressure. Compact enough to stow under a seat but complete enough to handle real emergencies."
    if any(w in t for w in ["license plate", "plate frame"]):
        return f"One of those products you never knew you needed until you installed it. These silicone license plate frames eliminate the annoying rattle from your plate while protecting the edges from rust and vibration damage. Weatherproof, no-drill, and instantly noticeable in the quiet."
    if any(w in t for w in ["wash", "wax", "clay bar", "microfiber", "chenille"]):
        return f"This complete clay bar system removes the embedded contaminants—overspray, brake dust, industrial fallout—that regular washing leaves behind. Smoothing the paint surface before wax means your finish actually shines instead of just looking clean. The difference between a wash and a detail."
    
    # --- TOYS/GAMES/GIFTS ---
    if any(w in t for w in ["magnetic tile", "stem"]):
        return f"70 magnetic tiles with 5 different shapes plus an idea book means hours of open-ended creative play. The magnets are strong enough to build stable structures but easy enough for small hands to separate. Screen-free creativity that grows with your child."
    if any(w in t for w in ["squishy", "plush"]):
        return f"30-pack of kawaii squishies that are small enough to fit in a party bag or desk drawer but cute enough to be a hit on their own. The random assortment means every pack is a surprise. An easy win for goodie bags, classroom rewards, or stress relief."
    if any(w in t for w in ["card", "birthday", "thinking of you", "funny"]):
        return f"A funny card that actually delivers the punchline without trying too hard. Printed on thick, quality cardstock that feels substantial in hand—not the flimsy paper most cards use. The kind of card someone keeps on their fridge long after their birthday."
    if any(w in t for w in ["dice", "dnd", "beer glass"]):
        return f"DND dice embedded directly into handmade beer glasses—a geeky twist on barware that actually looks good and holds a proper pour. Handmade means each one is unique, and the glass quality is good enough for daily use, not just display."
    if any(w in t for w in ["chess"]):
        return f"A magnetic wooden chess set that stays put during travel or outdoor games. The pieces have a satisfying weight, the board folds up compactly, and the magnets are strong enough to keep the board intact when you tilt it. Strategy without the setup anxiety."
    
    # --- TECH ---
    if any(w in t for w in ["watch", "forerunner", "garmin"]):
        return f"The Garmin Forerunner 265 gives serious runners the training insights they actually need without the smartwatch fluff. The bright AMOLED screen is readable in direct sun, and the battery lasts through marathon training blocks. Data-rich guidance without unnecessary complexity."
    if any(w in t for w in ["apple watch"]):
        return f"The S9 chip's double-tap gesture lets you interact without touching the screen—useful when your hands are full. The superbright display is noticeably better outdoors, and the health tracking suite covers everything from sleep to workouts. Your most-worn accessory that actually earns its wrist real estate."
    if any(w in t for w in ["charger", "usb-c", "gan"]):
        return f"GaN technology delivers high-speed charging in a fraction of the size of traditional laptop bricks. This 100W charger can juice up a laptop, tablet, and phone simultaneously without overheating. The travel-friendly size means it actually comes with you instead of staying plugged in at home."
    if any(w in t for w in ["raspberry pi", "pi case", "retroflag", "game5pi"]):
        return f"A purpose-built case that transforms your Raspberry Pi into a retro gaming console with proper ventilation and safe shutdown support. The iconic design is a conversation starter, and the build quality protects your Pi from the usual desk hazards. Form and function, properly executed."
    if any(w in t for w in ["borescope", "inspection camera"]):
        return f"A 16.5-foot waterproof borescope camera with a built-in 4.3-inch screen—no phone or Bluetooth needed. It reaches into walls, drains, and engine compartments to inspect hidden spaces. The kind of diagnostic tool that pays for itself the first time you use it to find a problem."
    
    # --- OUTDOOR GEAR ---
    if any(w in t for w in ["survival", "kit"]):
        return f"This 14-in-1 survival kit packs the essentials—cutting, fire, shelter, signaling—into a compact pouch that lives in your glovebox or backpack. Each component is genuinely useful, not just a box-checker, and the quality won't let you down when you need it. Practical preparedness without the tacticool weight."
    if any(w in t for w in ["flashlight", "spotlight", "rechargeable"]):
        return f"This heavy-duty rechargeable spotlight is several times brighter than standard flashlights, with a beam that reaches across a field. Rechargeable means no hunting for batteries when you need it most, and the rugged build survives drops and weather."
    if any(w in t for w in ["cooler", "lunchbox", "carhartt"]):
        return f"A Carhartt cooler built to the same standards as their workwear—it handles job sites, camping trips, and tailgates without showing wear. Keeps food cold for hours while the tough exterior shrugs off drops and scrapes. Buy it for the durability, keep using it because it works."
    
    # --- LIFESTYLE ---
    if any(w in t for w in ["golf", "towel"]):
        return f"A funny golf towel that's actually absorbent and large enough to clean clubs and balls. The humor is a bonus—the quality microfiber material does the real work of keeping your gear clean on the course. Functional, funny, and holds up to repeated washing."
    if any(w in t for w in ["sunglasses", "lazer"]):
        return f"Holographic lenses that revive 90s rave vibes with a modern build that's lightweight and wearable. The friction-fit design stays put without pinching, and the UV protection means you're not sacrificing eye safety for style. Party-ready optics that actually work."
    if any(w in t for w in ["fan", "turbo fan", "neck fan"]):
        return f"A 190g 3-in-1 fan that works as a handheld, neck-worn, or desktop fan—making it versatile enough for commutes, travel, or the office. The battery lasts through a full day of use, and the quiet operation means you won't annoy everyone nearby."
    
    # --- FALLBACK ---
    return None


def is_weak(desc, title, blurb):
    """Check if description needs improvement."""
    if not desc or len(desc) < 40:
        return True
    bad = ["offers excellent value and quality", "it's designed to be reliable and functional",
           "makes it a great choice for your needs", "excellent value and quality"]
    for pat in bad:
        if pat in desc.lower():
            return True
    # Short generic
    if len(desc.split()) < 10:
        return True
    return False


def main():
    print(f"\n{'='*60}")
    print("WorthItGoods — Description Enhancer (Keyword-Based)")
    print(f"{'='*60}\n")
    
    # Check backup exists
    if not Path(BACKUP_FILE).exists():
        shutil.copy2(DATA_FILE, BACKUP_FILE)
        print(f"✅ Backup created: {BACKUP_FILE}\n")
    
    with open(DATA_FILE) as f:
        products = json.load(f)
    
    # Find weak products
    weak = [(i, p) for i, p in enumerate(products) if is_weak(p.get("description",""), p.get("title",""), p.get("blurb",""))]
    print(f"Found {len(weak)} products needing description fixes\n")
    
    fixed_blurb = 0
    fixed_desc = 0
    
    for idx, (i, p) in enumerate(weak):
        title = p.get("title", "")
        blurb = p.get("blurb", "")
        cat = categorize(title, blurb)
        old_desc = p.get("description", "")
        
        print(f"  [{idx+1}/{len(weak)}] #{i+1} ({cat}): {title[:50]}...")
        
        new_desc = gen_description(title, blurb, cat)
        
        if new_desc:
            products[i]["description"] = new_desc
            fixed_desc += 1
            print(f"    ✅ desc updated")
        else:
            # Fallback: extract from title
            words = title.split()
            if len(words) > 3:
                short = ' '.join(words[:4])
                fallback = f"A quality {short.lower()} that delivers on its promise without the hype. Well-made, thoughtfully designed, and genuinely useful in everyday life."
                products[i]["description"] = fallback
                print(f"    ⚠️ fallback used")
        
        # Also fix blurb if it's just the Amazon subtitle
        if blurb and len(blurb) > 20 and len(blurb.split()) < 4:
            desc = products[i].get("description", "")
            new_blurb = desc.split(".")[0].strip() + "."
            if len(new_blurb) > 15:
                products[i]["blurb"] = new_blurb
                fixed_blurb += 1
                print(f"    ✅ blurb updated")
    
    # Save
    with open(DATA_FILE, 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Done!")
    print(f"  Descriptions fixed: {fixed_desc}")
    print(f"  Blurbs improved:    {fixed_blurb}")
    print(f"  Total weak found:   {len(weak)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
