# Cloudflare DNS Setup for worthitgoods.com

## Problem
- `worthitgoods.com` (apex domain) does not resolve
- `www.worthitgoods.com` works fine

## Solution
Fix the DNS configuration so that both domains work and redirect properly.

---

### 🧩 Option A: Cloudflare Proxy (Recommended)

#### 1. Apex DNS Record (worthitgoods.com)
In Cloudflare DNS dashboard:
- **Type**: A
- **Name**: `@` (leave blank)
- **Target**: `192.0.2.1` (Cloudflare IP – replace with actual Pages IP if known)
- **Proxy status**: **Orange Cloud (Proxied)**

#### 2. CNAME Record (www.worthitgoods.com)
- **Type**: CNAME
- **Name**: `www`
- **Target**: `your-github-username.github.io` (or Pages domain if custom)
- **Proxy status**: **Orange Cloud (Proxied)**

#### 3. Page Rules / Workers Redirect (Force WWW)
Add a redirect rule in Cloudflare:
- **URL**: `https://worthitgoods.com/*`
- **Setting**: Forwarding URL (301) → `https://www.worthitgoods.com/$1`

Or, use a Workers script for more control:

```javascript
// redirect-worker.js
export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.hostname === 'worthitgoods.com') {
      return Response.redirect(`https://www.worthitgoods.com${url.pathname}${url.search}`, 301);
    }
    return fetch(request);
  }
};
```

---

### 🧩 Option B: Apex to GitHub Pages (No Cloudflare Proxy)

If you prefer GitHub Pages to handle the bare domain:

#### 1. Apex DNS Record
- **Type**: A
- **Name**: `@`
- **Target**: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` (GitHub Pages IPs)
- **Proxy status**: **Gray Cloud (DNS Only)**

#### 2. CNAME Record (www)
- **Type**: CNAME
- **Name**: `www`
- **Target**: `your-github-username.github.io` (Pages domain)
- **Proxy status**: **Orange Cloud (Proxied)**

#### 3. GitHub Pages Custom Domain
In GitHub repo settings:
- Add `www.worthitgoods.com` to custom domains
- Enable HTTPS

---

### 🔍 Verification Commands
```bash
# Test DNS resolution
dig worthitgoods.com
dig www.worthitgoods.com

# Test redirects (should redirect to www)
curl -I https://worthitgoods.com
```

---

### ⚠️ Important Notes
- **Propagation**: DNS changes can take 24-48 hours to fully propagate
- **SSL**: Cloudflare will handle free SSL if proxying
- **Caching**: Clear Cloudflare cache after making changes

---

### 🚀 Next Steps
1. Apply DNS changes in Cloudflare dashboard
2. Wait 15-30 minutes for changes to take effect
3. Test both URLs in browser
4. Verify HTTPS is working on both domains