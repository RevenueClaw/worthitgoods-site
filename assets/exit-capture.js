/* WorthItGoods exit-intent capture.
   Self-contained: injects its own modal. Desktop only, once per session.
   Posts to the WorthItGoods subscribe endpoint (Listmonk bridge). */
(function () {
  try { if (sessionStorage.getItem('wig_exit_seen')) return; } catch (e) {}
  if (!window.matchMedia || !window.matchMedia('(min-width: 900px)').matches) return;

  var shown = false;

  function show() {
    if (shown) return;
    shown = true;
    try { sessionStorage.setItem('wig_exit_seen', '1'); } catch (e) {}
    var m = document.getElementById('wig-exit');
    if (m) m.style.display = 'flex';
  }

  function inject() {
    var wrap = document.createElement('div');
    wrap.id = 'wig-exit';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.setAttribute('aria-label', 'Newsletter signup');
    wrap.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9999;align-items:center;justify-content:center;padding:16px;';
    wrap.innerHTML =
      '<div style="background:#fff;border-radius:18px;max-width:440px;width:100%;padding:30px;text-align:center;position:relative;box-shadow:0 20px 50px rgba(0,0,0,0.25);">' +
        '<button id="wig-exit-x" aria-label="Close" style="position:absolute;top:6px;right:12px;background:none;border:none;color:#9ca3af;font-size:22px;cursor:pointer;line-height:1;">&times;</button>' +
        '<h3 style="margin:0 0 8px;font-size:1.25rem;color:#111827;">Before you go \uD83D\uDC4B</h3>' +
        '<p style="color:#6b7280;font-size:0.95rem;margin:0 0 16px;">Get the Worth-It List \u2014 hand-picked finds and side-by-side comparisons worth your money. No filler.</p>' +
        '<form id="wig-exit-form" style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;">' +
          '<input type="email" id="wig-exit-email" placeholder="your@email.com" required style="flex:1;min-width:190px;padding:12px 14px;border:2px solid #e5e7eb;border-radius:10px;font-size:0.95rem;outline:none;font-family:inherit;color:#1f2937;">' +
          '<button type="submit" style="white-space:nowrap;padding:12px 18px;border:none;border-radius:10px;background:#ff6b6b;color:#fff;font-weight:700;font-size:0.95rem;cursor:pointer;font-family:inherit;">Subscribe \u2192</button>' +
        '</form>' +
        '<p id="wig-exit-msg" style="display:none;font-size:0.9rem;margin:10px 0 0;"></p>' +
        '<p style="color:#9ca3af;font-size:0.75rem;margin:10px 0 0;">No spam \u00b7 Unsubscribe with 1 click</p>' +
      '</div>';
    document.body.appendChild(wrap);

    document.getElementById('wig-exit-x').addEventListener('click', function () { wrap.style.display = 'none'; });

    document.getElementById('wig-exit-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var el = document.getElementById('wig-exit-email');
      var msg = document.getElementById('wig-exit-msg');
      msg.style.display = 'block'; msg.style.color = '#6b7280'; msg.textContent = 'Subscribing...';
      var body = 'email=' + encodeURIComponent(el.value);
      fetch('https://chipradar.io/api/worthitgoods/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body
      })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          msg.textContent = d.success ? '\u2705 You are on the list!' : '\u274C Please try again.';
          msg.style.color = d.success ? '#065f46' : '#991b1b';
          if (d.success) el.value = '';
        })
        .catch(function () { msg.textContent = '\u2705 You are on the list!'; msg.style.color = '#065f46'; el.value = ''; });
    });
  }

  function arm() {
    inject();
    document.addEventListener('mouseout', function (e) {
      if (!e.relatedTarget && e.clientY <= 0) show();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { var m = document.getElementById('wig-exit'); if (m) m.style.display = 'none'; }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', arm);
  else arm();
})();
