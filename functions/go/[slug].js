/**
 * WorthItGoods legacy click shim (added 2026-11-24).
 * Old emails/newsletters (Aug-Oct 2026, Worker era) link /go/{slug}?asin=B0XXXX.
 * The replacement Pages Function only matches /go/asin/:asin — this keeps the
 * query form alive: valid asin -> tagged Amazon redirect, anything else -> home.
 */
export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  const asin = (url.searchParams.get("asin") || "").trim().toUpperCase();
  const tag = "worthitgoods-20";
  let target = "https://www.worthitgoods.com/";
  let status = 302;
  if (/^[A-Z0-9]{10}$/.test(asin)) {
    target = `https://www.amazon.com/dp/${asin}?tag=${tag}&linkCode=ll1&language=en_US&ref_=as_li_ss_tl`;
    status = 301;
    context.waitUntil(
      fetch("https://plausible.io/api/event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "User-Agent": request.headers.get("User-Agent") || "",
          "X-Forwarded-For": request.headers.get("CF-Connecting-IP") || "",
        },
        body: JSON.stringify({
          name: "Amazon Click", url: url.href, domain: "worthitgoods.com",
          referrer: request.headers.get("Referer") || "", props: { asin },
        }),
      }).catch(() => {})
    );
  }
  return Response.redirect(target, status);
}
