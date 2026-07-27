/**
 * WorthIt Goods — Newsletter Signup Proxy
 * 
 * Proxies newsletter signup POST requests from worthitgoods.com
 * to the ChipRadar backend -> Pi5 Listmonk via reverse SSH tunnel.
 */
export async function onRequest(context) {
  const { request } = context;

  if (request.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const body = await request.text();

    // Parse the JSON body to extract email, then forward as form data
    const json = JSON.parse(body);
    const email = json.email || "";

    const response = await fetch(
      "https://chipradar.io/api/worthitgoods/subscribe",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "email=" + encodeURIComponent(email),
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
