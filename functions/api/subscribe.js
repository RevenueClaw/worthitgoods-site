/**
 * WorthIt Goods — Subscribe endpoint.
 * Price-alert signups were discontinued 2026-11-05 for Amazon Associates
 * compliance (no price tracking / alerting tied to Amazon products).
 * Newsletter signup remains available at /api/newsletter/signup.
 */
export async function onRequest(context) {
  const { request } = context;
  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }
  return new Response(
    JSON.stringify({ success: false, message: "Price alerts have been discontinued. Subscribe to our newsletter instead." }),
    { status: 410, headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } }
  );
}
