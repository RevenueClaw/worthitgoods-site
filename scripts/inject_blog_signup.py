#!/usr/bin/env python3
"""Inject a compact newsletter signup block into WIG blog posts, comparisons,
and category pages — same POST endpoint and behavior as the canonical
wigNewsletterForm in generate-pages.js. Idempotent (marker comment), runs at
build time like inject_exit_capture.py, so hand-crafted posts get it too."""
import pathlib, re, sys

SITE = pathlib.Path(__file__).resolve().parent.parent / "_site"
MARKER = "WIG-SIGNUP-BLOCK"

BLOCK = """<!-- WIG-SIGNUP-BLOCK -->
<div id="wigSignupBlock" style="max-width:560px;margin:3rem auto 1rem;padding:1.6rem;background:linear-gradient(135deg,#fff7ed,#fef2f2);border:1.5px solid #fdba74;border-radius:14px;text-align:center">
  <h3 style="margin:0 0 .3rem;font-size:1.25rem;color:#111827">Get the good finds in your inbox 🎁</h3>
  <p style="margin:0 0 1rem;font-size:.92rem;color:#6b7280">Weekly hand-picked picks &amp; new comparisons. No spam, one-click unsubscribe.</p>
  <form id="wigSignupForm" style="display:flex;gap:.5rem;justify-content:center;flex-wrap:wrap" onsubmit="return false">
    <input id="wigSignupEmail" type="email" placeholder="your@email.com" required style="padding:.7rem 1rem;border:1.5px solid #e5e7eb;border-radius:8px;font-size:1rem;min-width:230px">
    <button type="submit" style="padding:.7rem 1.4rem;background:#c41e3a;color:#fff;border:0;border-radius:8px;font-weight:700;font-size:1rem;cursor:pointer">Subscribe</button>
  </form>
  <p id="wigSignupMsg" style="margin:.7rem 0 0;font-size:.9rem;color:#059669"></p>
</div>
<script>
(function(){
  var f=document.getElementById('wigSignupForm'); if(!f) return;
  f.addEventListener('submit', async function(){
    var el=document.getElementById('wigSignupEmail'), m=document.getElementById('wigSignupMsg');
    if(!el.value){return;}
    m.textContent='Subscribing...'; m.style.color='#6b7280';
    try{
      var res=await fetch('https://chipradar.io/api/worthitgoods/subscribe',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'email='+encodeURIComponent(el.value)});
      var d=await res.json();
      m.textContent=d.message||"You're on the list!"; m.style.color=d.success?'#059669':'#dc2626';
      if(d.success){el.value='';}
    }catch(e){m.textContent="Network hiccup \\u2014 try again in a sec";m.style.color='#dc2626';}
  });
})();
</script>
"""

def targets():
    dirs = [SITE / "blog", SITE / "comparisons", SITE / "categories", SITE / "best-of"]
    for d in dirs:
        if d.is_dir():
            yield from sorted(d.glob("*.html"))
            yield from sorted(p for sub in d.glob("*/") if sub.is_dir() for p in sub.glob("*.html"))

count = skipped = 0
for page in targets():
    html = page.read_text(errors="replace")
    if MARKER in html or "wigNewsletterForm" in html:
        skipped += 1
        continue
    # insert before the footer if present, else before </body>
    m = re.search(r"<footer\b", html, re.I)
    if m:
        html = html[:m.start()] + BLOCK + html[m.start():]
    else:
        m2 = re.search(r"</body>", html, re.I)
        if not m2:
            continue
        html = html[:m2.start()] + BLOCK + html[m2.start():]
    page.write_text(html)
    count += 1

print(f"signup block injected into {count} pages ({skipped} already had one)")
