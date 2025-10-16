cat > app.py <<'EOF'
from flask import Flask, request, jsonify, send_from_directory, abort
import requests
import time
import os
from urllib.parse import urlparse

app = Flask(__name__, static_folder='public', static_url_path='')

# simple rate-limit/per-IP in-memory store
LAST_REQUEST_TIME = {}
MIN_INTERVAL = 2.0  # seconds per IP

TARGET_URL = 'https://nakrutka.com/my/freelikes.php'  # the upstream endpoint

def is_valid_instagram_url(u: str) -> bool:
    if not u: return False
    u = u.strip()
    try:
        p = urlparse(u)
        if p.scheme not in ('http', 'https'): return False
        if 'instagram.com' not in p.netloc: return False
        # basic check for path
        if not p.path or p.path == '/': return False
        return True
    except Exception:
        return False

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/api/send-link', methods=['POST'])
def send_link():
    client_ip = request.remote_addr or 'unknown'
    now = time.time()
    last = LAST_REQUEST_TIME.get(client_ip, 0)
    if now - last < MIN_INTERVAL:
        return jsonify({'error': 'Too many requests. Slow down.'}), 429
    LAST_REQUEST_TIME[client_ip] = now

    j = request.get_json(silent=True)
    if not j or 'postUrl' not in j:
        return jsonify({'error': 'Missing postUrl in JSON body'}), 400

    post_url = j.get('postUrl','').strip()
    if not is_valid_instagram_url(post_url) or not post_url.startswith('https://www.instagram.com/'):
        return jsonify({'error': 'Invalid Instagram URL'}), 400

    # Normalize /reel/ /reels/ /tv/ -> /p/
    normalized = post_url.replace('/reel/','/p/').replace('/reels/','/p/').replace('/tv/','/p/')

    # Build payload as form data. Adjust field names as the upstream expects.
    payload = {
        'link': normalized
        # add other fields here if required but only if you have explicit permission
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Python proxy)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    try:
        resp = requests.post(TARGET_URL, data=payload, headers=headers, timeout=15, allow_redirects=True)
        status_code = resp.status_code
        # You can inspect resp.text for success markers if you know them.
        return jsonify({
            'message': 'Forwarded to target site',
            'upstream_status': status_code,
            'snippet_length': len(resp.text or '')
        }), 200 if 200 <= status_code < 300 else 502
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Upstream request failed', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    # For Termux/dev use: debug=False recommended for production
    app.run(host='0.0.0.0', port=port, debug=False)
EOF
