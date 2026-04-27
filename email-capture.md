# Email Capture Automation for worthitgoods.com

## Overview
Capture emails via a lightweight form, feed them into Mailchimp (or Klaviyo), and trigger automated drip campaigns.

---

## 🏗️ 1. Form Setup (Static HTML)

Add to `_site/index.html` (or via `generate-pages.js`):

```html
<!-- Email Capture Banner -->
<div id="email-banner" style="background:#f8f9fa;padding:1rem;text-align:center;">
  <p style="margin:0 0 0.5rem 0;">Get 10% off your first order when you sign up!</p>
  <form id="email-form" action="https://YOUR_WORKER_OR_FORM_ENDPOINT" method="POST">
    <input type="email" name="email" placeholder="you@email.com" required style="padding:0.5rem;width:200px;">
    <button type="submit" style="padding:0.5rem 1rem;background:#007cba;color:#fff;border:none;">Sign Up</button>
  </form>
  <p id="form-msg" style="color:green;display:none;"></p>
</div>

<script>
document.getElementById('email-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = e.target.email.value;
  const resp = await fetch(e.target.action, { method:'POST', body: JSON.stringify({email}), headers:{'Content-Type':'application/json'}});
  if (resp.ok) {
    document.getElementById('form-msg').innerText = 'Thanks! Check your inbox.';
    document.getElementById('form-msg').style.display = 'block';
    e.target.reset();
  }
});
</script>
```

---

## ⚙️ 2. Serverless Endpoint (Cloudflare Worker)

Create a Worker (`email-capture-worker.js`) that:
1. Receives POST with `{email}`
2. Validates email format
3. Adds to Mailchimp list via API
4. Returns success

```javascript
export default {
  async fetch(request) {
    if (request.method !== 'POST') return new Response('Method not allowed', {status:405});
    const { email } = await request.json();
    // Basic validation
    if (!email || !email.includes('@')) return new Response('Invalid email', {status:400});
    // Mailchimp API call
    const apiKey = MAILCHIMP_API_KEY; // set as Worker secret
    const listId = 'YOUR_LIST_ID';
    const resp = await fetch(`https://<dc>.api.mailchimp.com/3.0/lists/${listId}/members`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email_address: email,
        status: 'subscribed'
      })
    });
    if (resp.ok) return new Response('OK', {status:200});
    return new Response('Error', {status:500});
  }
};
```

Set secrets:
```bash
wrangler secret put MAILCHIMP_API_KEY
```

---

## 🔗 3. Zapier Integration (Alternative to Worker)

If you don't want to manage a Worker:

1. **Create a Zap**:
   - Trigger: **Webhooks by Zapier** → **Catch Hook**
   - Action: **Mailchimp** → **Add/Update Subscriber**
2. **Get webhook URL** from Zapier.
3. **Update form action** to that webhook URL.

---

## 📧 4. Mailchimp Drip Campaign

In Mailchimp:
1. Create an **Audience** (list) for worthitgoods.com.
2. Set up **Automation**:
   - **Welcome series**: 3 emails over 7 days.
   - **Product highlight**: Pick 3 random products from `sample_products.json` (via API or manual selection).
   - **Abandoned cart** (if e‑commerce added later).

---

## 🤖 5. Automation Summary

| Step | Tool | Action |
|------|------|--------|
| Capture email | Form on site | POST to Worker or Zapier webhook |
| Store contact | Mailchimp | Add subscriber via API |
| Nurture | Mailchimp Automation | Send welcome series |
| Track conversions | Google Analytics | UTM on email links |

---

## 📅 6. Next Steps

1. Deploy the Worker (or set up Zapier webhook).
2. Add the form snippet to `generate-pages.js` so it appears on every page.
3. Test the flow: submit an email → check Mailchimp → receive welcome email.
4. Connect Google Analytics UTM parameters to email links.

> **Note**: The Worker approach is more reliable and free (Cloudflare Workers free tier). Zapier free tier has limits.
