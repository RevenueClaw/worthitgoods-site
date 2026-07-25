/**
 * WorthIt Goods — Price Alert / Subscribe Proxy
 * 
 * Proxies subscribe POST requests from worthitgoods.com
 * to the lead tracker running through Cloudflare Tunnel.
 */
export async function onRequest(context) {
  const { request } = context;

  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const body = await request.text();

    const response = await fetch(
      "https://price-alert.worthitgoods.com/subscribe",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body,
      }
    );

    const data = await response.text();

    return new Response(data, {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        success: false,
        message:
          "Something went wrong. Please try again later.",
      }),
      {
        status: 502,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}
