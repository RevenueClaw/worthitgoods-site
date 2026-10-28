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

  // Fire-and-forget Plausible event (don't block the redirect)
  const eventCtx = new URL(request.url);
  context.waitUntil(
    fetch("https://plausible.io/api/event", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": ua,
        "X-Forwarded-For": ip,
      },
      body: JSON.stringify({
        name: "Amazon Click",
        url: eventCtx.href,
        domain: "worthitgoods.com",
        referrer: referrer,
        props: {
          asin: asin,
        },
      }),
    }).catch(() => {
      // Silently ignore Plausible failures — never block the redirect
    })
  );

  return Response.redirect(redirectUrl, 301);
}