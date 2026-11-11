#!/usr/bin/env python3
"""Minimal Pinterest OAuth callback server for Standard Access demo video.
Starts on port 8080, handles the callback, exchanges code for token, creates a test pin.
"""
import json, urllib.request, urllib.parse, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

CLIENT_ID = "1566159"
CLIENT_SECRET = "cbf6b7e23440be3acf6fc0ecdcc749cef3e27570"
REDIRECT_URI = "http://192.168.4.131:8080/callback"
BOARD_ID = "1088956453590786635"

# Pinterest OAuth URL the owner visits in browser:
AUTH_URL = (
    "https://www.pinterest.com/oauth/"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    "&response_type=code"
    "&scope=boards:read,pins:read,boards:write,pins:write"
)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(path.query)
        code = params.get('code', [None])[0]
        error = params.get('error', [None])[0]
        
        if error:
            body = f"<h1>❌ Auth failed</h1><p>{error}: {params.get('error_description',[''])[0]}</p>"
        elif code:
            # Exchange code for access token
            print(f"\n✅ Got auth code: {code[:20]}...")
            token = exchange_code(code)
            if token:
                body = "<h1>✅ Authorized!</h1><p>Access token received. Check the terminal for the pin result.</p>"
                create_test_pin(token)
            else:
                body = "<h1>❌ Token exchange failed</h1><p>Check terminal for details.</p>"
        else:
            body = "<h1>Pinterest OAuth Callback</h1><p>No authorization code received.</p>"
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(body.encode())

def exchange_code(code):
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }).encode()
    req = urllib.request.Request('https://api.pinterest.com/v5/oauth/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            tok = result.get('access_token', '')
            print(f"✅ Access token (len={len(tok)}): {tok[:20]}...")
            # Save it
            with open('/tmp/pinterest_oauth_token.txt', 'w') as f:
                f.write(tok)
            return tok
    except Exception as e:
        try: body = e.read().decode()[:400]
        except: body = ''
        print(f"❌ Token exchange failed: {e}\n{body}")
        return None

def create_test_pin(token):
    """Create a test pin on the board."""
    data = {
        'title': '🎁 WorthItGoods Holiday Gift Guide 2026 — Test Pin',
        'description': '10 hand-picked holiday gifts across barware, tech, kitchen, grilling and cozy. Every product vetted — no filler, no novelty junk. Test pin for API Standard Access demo.',
        'link': 'https://www.worthitgoods.com/blog/2026-11-07-seasonal-holiday_gifts.html',
        'board_id': BOARD_ID,
        'media_source': {
            'source_type': 'image_url',
            'url': 'https://m.media-amazon.com/images/I/51QAxJlD4-L._SL400_.jpg'
        }
    }
    body = json.dumps(data).encode()
    
    # Try sandbox first (Trial access), then production
    for base, label in [('https://api-sandbox.pinterest.com', 'sandbox'), ('https://api.pinterest.com', 'production')]:
        url = f"{base}/v5/pins"
        req = urllib.request.Request(url, data=body,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())
                pid = result.get('id', '?')
                print(f"✅ Pin created ({label}): https://www.pinterest.com/pin/{pid}/")
                return
        except Exception as e:
            code = getattr(e, 'code', '?')
            try: resp = e.read().decode()[:300]
            except: resp = ''
            print(f"  {label}: {code} — {resp}")

if __name__ == '__main__':
    print("=" * 60)
    print("Pinterest OAuth Callback Server")
    print("=" * 60)
    print(f"\n👉 Owner: open this URL in your browser:\n\n{AUTH_URL}\n")
    print(f"Listening on {REDIRECT_URI} ...\n")
    sys.stdout.flush()
    
    server = HTTPServer(('0.0.0.0', 8080), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")