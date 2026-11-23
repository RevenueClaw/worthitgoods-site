/**
 * WorthIt Goods - Newsletter Signup Proxy (fixed 2026-11-23: the form posts
 * urlencoded, old code JSON.parsed everything -> 502 on every real signup).
 */
export async function onRequest(context) {
  const { request } = context;
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }
  const json = (o, status = 200) => new Response(JSON.stringify(o), {
    status, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });
  try {
    const ct = (request.headers.get("Content-Type") || "").toLowerCase();
    const raw = await request.text();
    let email = "";
    if (ct.includes("json")) { try { email = String(JSON.parse(raw).email || ""); } catch { email = ""; } }
    else { email = new URLSearchParams(raw).get("email") || ""; }
    email = email.trim().toLowerCase();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      return json({ success: false, message: "Please enter a valid email address." }, 400);
    }
    const upstream = await fetch("https://chipradar.io/api/worthitgoods/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "email=" + encodeURIComponent(email),
    });
    const body = await upstream.text();
    let parsed; try { parsed = JSON.parse(body); } catch { parsed = { success: upstream.ok }; }
    if (upstream.ok) return json({ success: true, message: parsed.message || "You are subscribed! We will keep you posted." });
    if (upstream.status === 422 || upstream.status === 400) return json({ success: false, message: "Please enter a valid email address." }, 400);
    console.error("newsletter proxy upstream", upstream.status, body.slice(0, 200));
    return json({ success: false, message: "Something went wrong. Please try again later." }, 502);
  } catch (err) {
    console.error("newsletter proxy error", err);
    return json({ success: false, message: "Something went wrong. Please try again later." }, 502);
  }
}
