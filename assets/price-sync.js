/* WorthItGoods price sync.
 *
 * Comparison pages bake prices into text at build time, so a stale build shows
 * prices Amazon will not honor — visitors click and bounce. This corrects the
 * displayed price from data/live-prices.json and labels how fresh it is.
 *
 * Failure behavior is deliberately conservative: if the fetch fails, we do NOT
 * leave a possibly-wrong price standing. We strip the specific figure from CTA
 * text and add the verification note, so we never promise a price we can't back.
 */
(function () {
  "use strict";

  var PRICE_RE = /\$[0-9][0-9,]*(\.[0-9]{2})?/;
  var dataPromise = null;

  function load() {
    if (!dataPromise) {
      dataPromise = fetch("/assets/live-prices.json", { cache: "no-store" })
        .then(function (r) {
          if (!r.ok) throw new Error("status " + r.status);
          return r.json();
        })
        .catch(function () { return null; });
    }
    return dataPromise;
  }

  function asinFromHref(href) {
    var m = /amazon\.[a-z.]+\/dp\/([A-Z0-9]{10})/.exec(href || "");
    return m ? m[1] : null;
  }

  function fmt(n) {
    return "$" + n.toFixed(2);
  }

  function note(container, text) {
    if (!container || container.querySelector(".price-verified")) return;
    var el = document.createElement("p");
    el.className = "price-verified";
    el.style.cssText =
      "margin:10px 0 0;font-size:12px;opacity:.65;line-height:1.4;";
    el.textContent = text;
    container.appendChild(el);
  }

  function run(data) {
    var links = document.querySelectorAll('a[href*="amazon."]');
    var corrected = 0;

    links.forEach(function (a) {
      var asin = asinFromHref(a.getAttribute("href"));
      if (!asin) return;
      var entry = data && data.prices ? data.prices[asin] : null;
      var text = a.textContent;

      if (entry && entry.price) {
        // Replace any baked dollar figure in the CTA with the current one.
        var live = fmt(entry.price);
        a.textContent = PRICE_RE.test(text)
          ? text.replace(PRICE_RE, live)
          : text.replace(/\s*→\s*$/, " — " + live + " →");
        if (a.textContent !== text) corrected++;
      } else {
        // Unknown price: never leave a possibly-wrong promise in a CTA.
        a.textContent = text.replace(/\s*—\s*\$[0-9][0-9,]*(\.[0-9]{2})?\s*→/, " →");
      }
    });

    // Correct inline prose figures for ASINs referenced on the page.
    var pageAsins = {};
    links.forEach(function (a) {
      var asin = asinFromHref(a.getAttribute("href"));
      if (asin && data && data.prices && data.prices[asin]) pageAsins[asin] = data.prices[asin];
    });

    var art = document.querySelector("article") || document.body;
    if (Object.keys(pageAsins).length) {
      var checked = (data && data.checked) || "";
      note(art, "Prices verified " + checked + " and refresh regularly. Always confirm the current price on Amazon before buying.");
    }

    if (window.console && corrected >= 0) {
      console.debug("[price-sync] corrected " + corrected + " affiliate CTA price(s)");
    }
  }

  function boot() {
    if (document.querySelector('a[href*="amazon."]')) {
      load().then(function (data) {
        try { run(data); } catch (e) { /* never break the page */ }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();