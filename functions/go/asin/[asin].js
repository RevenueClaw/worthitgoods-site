/**
 * WorthItGoods click tracker — Cloudflare Pages Function.
 * Handles /go/asin/:asin — records click to Plausible, redirects to Amazon.
 * 
 * Usage: /go/asin/B08LVJ87M6 → redirects to amazon.com/dp/B08LVJ87M6?tag=worthitgoods-20
 */

export async function onRequest(context) {
  const { request, params } = context;
  const asin = params.asin;
  const tag = "worthitgoods-20";
  const referrer = request.headers.get("Referer") || "";
  const ua = request.headers.get("User-Agent") || "";
  const ip = request.headers.get("CF-Connecting-IP") || "";

  const redirectUrl = `https://www.amazon.com/dp/${asin}?tag=${tag}`;

  // Log click to chipradar (internal analytics — zero external deps)
  context.waitUntil(
    fetch("https://chipradar.io/api/worthitgoods/click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asin: asin, referrer: referrer }),
    }).catch(() => {})
  );

  return Response.redirect(redirectUrl, 301);
}