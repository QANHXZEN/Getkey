from flask import Flask, request, jsonify, render_template_string, redirect
import requests
import random
import string
from datetime import datetime, timedelta
import os
import json
import hashlib
import hmac
import secrets
import time
from functools import wraps
import re
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# ========== CẤU HÌNH API ==========
LINK4M_API_KEY = os.environ.get("LINK4M_API_KEY", "65c47d157fbdff4d79625e57")
LINK4M_API_URL = "https://link4m.co/api-shorten/v2"

YEUMONEY_API_KEY = os.environ.get("YEUMONEY_API_KEY", "4e3bbf63ff3ac2f780f246675412f35c3f31946a74f195992dbaf2a6d6c26eee")
YEUMONEY_API_URL = "https://yeumoney.com/QL_api.php"

VUOTNHANH_API_KEY = os.environ.get("VUOTNHANH_API_KEY", "e7c716d2-996f-4bdd-bcbf-7653223a400b")
VUOTNHANH_API_URL = "https://vuotnhanh.com/api"

YOUR_DOMAIN = os.environ.get("YOUR_DOMAIN", "https://your-app.onrender.com")

# ========== TELEGRAM BOT (ĐÃ CẬP NHẬT) ==========
TELEGRAM_BOT_TOKEN = "8448578289:AAH2Pp6s3V1Le-cV5I1Qc-gFKQzTDBMXnvA"
TELEGRAM_CHAT_ID = "8588555065"  # Chat ID của bạn

# ========== ADMIN PANEL ==========
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Dragon@2024")

# ========== KHÓA MÃ HÓA ==========
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", secrets.token_hex(32))

# ========== FILE LƯU TRỮ ==========
KEYS_FILE = "keys.json"
TASKS_FILE = "user_tasks.json"
BLACKLIST_FILE = "blacklist.json"
RATE_LIMIT_FILE = "rate_limit.json"
STATS_FILE = "stats.json"
EARNINGS_FILE = "earnings.json"

# ========== GIỚI HẠN TỐC ĐỘ ==========
RATE_LIMITS = {
    'verify_key': {'max_requests': 5, 'window': 60},
    'generate_key': {'max_requests': 2, 'window': 300},
    'check_step': {'max_requests': 30, 'window': 60},
}

# ========== HÀM TELEGRAM ==========
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram chưa được cấu hình đầy đủ")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
        response = requests.post(url, json=payload, timeout=5)
        print(f"Telegram sent: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def notify_new_key(key, user_ip, user_fingerprint):
    send_telegram_message(f"""
🔑 <b>KEY MỚI ĐƯỢC TẠO!</b>
━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>Fingerprint:</b> {user_fingerprint[:16]}...
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━
✅ Key có hiệu lực 24 giờ
    """)

def notify_key_used(key, user_ip, user_fingerprint):
    send_telegram_message(f"""
✅ <b>KEY ĐÃ ĐƯỢC KÍCH HOẠT!</b>
━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>Fingerprint:</b> {user_fingerprint[:16]}...
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━
🎉 Chúc mừng người dùng mới!
    """)

def notify_new_user(ip, fingerprint):
    send_telegram_message(f"""
👤 <b>NGƯỜI DÙNG MỚI!</b>
━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> {fingerprint[:16]}...
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)

def notify_completed_all_tasks(fingerprint, key):
    send_telegram_message(f"""
🎉 <b>HOÀN THÀNH TOÀN BỘ NHIỆM VỤ!</b>
━━━━━━━━━━━━━━━━━
🆔 <b>Fingerprint:</b> {fingerprint[:16]}...
🔑 <b>Key nhận được:</b> <code>{key}</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━
💰 Bạn đã kiếm được tiền từ link nhiệm vụ!
    """)

# ========== HÀM KIẾM TIỀN ==========
def update_earnings(service_name, amount=0.001):
    earnings = load_earnings()
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in earnings:
        earnings[today] = {}
    if service_name not in earnings[today]:
        earnings[today][service_name] = 0
    earnings[today][service_name] += amount
    earnings['total'] = earnings.get('total', 0) + amount
    save_earnings(earnings)
    return earnings['total']

def load_earnings():
    if not os.path.exists(EARNINGS_FILE):
        return {'total': 0}
    try:
        with open(EARNINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'total': 0}

def save_earnings(data):
    with open(EARNINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ========== HÀM BẢO MẬT ==========
def simple_encrypt(text):
    if not text:
        return text
    key_bytes = ENCRYPTION_KEY.encode()[:32]
    result = bytearray()
    for i, char in enumerate(str(text)):
        result.append(ord(char) ^ key_bytes[i % len(key_bytes)])
    return result.hex()

def simple_decrypt(hex_text):
    if not hex_text:
        return hex_text
    try:
        encrypted = bytes.fromhex(hex_text)
        key_bytes = ENCRYPTION_KEY.encode()[:32]
        result = []
        for i, byte in enumerate(encrypted):
            result.append(chr(byte ^ key_bytes[i % len(key_bytes)]))
        return ''.join(result)
    except:
        return None

def generate_session_id():
    return secrets.token_hex(24)

def generate_dragon_key():
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(secrets.choice(chars) for _ in range(6))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    raw_key = f"DRP-{part1}-{part2}"
    checksum = hashlib.md5(raw_key.encode()).hexdigest()[:2].upper()
    return f"{raw_key}-{checksum}"

def verify_key_checksum(key):
    if not key or len(key) < 15:
        return False
    match = re.match(r'^DRP-[A-Z0-9]{6}-[A-Z0-9]{4}-([A-Z0-9]{2})$', key)
    if not match:
        return False
    provided_checksum = match.group(1)
    raw_key = key[:-3]
    expected_checksum = hashlib.md5(raw_key.encode()).hexdigest()[:2].upper()
    return hmac.compare_digest(provided_checksum, expected_checksum)

def get_client_fingerprint(request):
    user_agent = request.headers.get('User-Agent', 'unknown')
    accept_language = request.headers.get('Accept-Language', 'unknown')
    ip = request.remote_addr
    fingerprint_str = f"{ip}|{user_agent}|{accept_language}"
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

# ========== RATE LIMIT ==========
def load_rate_limit():
    if not os.path.exists(RATE_LIMIT_FILE):
        return {}
    try:
        with open(RATE_LIMIT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_rate_limit(data):
    with open(RATE_LIMIT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def rate_limit(action, identifier):
    now = time.time()
    limit_config = RATE_LIMITS.get(action)
    if not limit_config:
        return True
    rate_data = load_rate_limit()
    key = f"{action}:{identifier}"
    if key not in rate_data:
        rate_data[key] = {'count': 1, 'first_request': now}
        save_rate_limit(rate_data)
        return True
    record = rate_data[key]
    if now - record['first_request'] > limit_config['window']:
        record['count'] = 1
        record['first_request'] = now
        save_rate_limit(rate_data)
        return True
    if record['count'] >= limit_config['max_requests']:
        return False
    record['count'] += 1
    save_rate_limit(rate_data)
    return True

# ========== BLACKLIST ==========
def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return {'ips': [], 'fingerprints': []}
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'ips': [], 'fingerprints': []}

def save_blacklist(data):
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_blacklisted(ip, fingerprint):
    blacklist = load_blacklist()
    return ip in blacklist.get('ips', []) or fingerprint in blacklist.get('fingerprints', [])

def add_to_blacklist(ip, fingerprint, reason):
    blacklist = load_blacklist()
    if ip and ip not in blacklist['ips']:
        blacklist['ips'].append(ip)
    if fingerprint and fingerprint not in blacklist['fingerprints']:
        blacklist['fingerprints'].append(fingerprint)
    save_blacklist(blacklist)
    
    send_telegram_message(f"""
🚫 <b>ĐÃ THÊM VÀO BLACKLIST!</b>
━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> {fingerprint[:16]}...
📝 <b>Lý do:</b> {reason}
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)

# ========== LƯU TRỮ ==========
def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, 'r') as f:
            data = json.load(f)
            for key, value in data.items():
                if 'encrypted_data' in value:
                    decrypted = simple_decrypt(value['encrypted_data'])
                    if decrypted:
                        value['decrypted'] = decrypted
            return data
    except:
        return {}

def save_keys(data):
    safe_data = {}
    for key, value in data.items():
        safe_value = value.copy()
        if 'decrypted' in safe_value:
            safe_value['encrypted_data'] = simple_encrypt(safe_value['decrypted'])
            del safe_value['decrypted']
        safe_data[key] = safe_value
    with open(KEYS_FILE, 'w') as f:
        json.dump(safe_data, f, indent=2)

def load_user_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    try:
        with open(TASKS_FILE, 'r') as f:
            data = json.load(f)
            for sid, task in data.items():
                if task.get('encrypted'):
                    for field in ['key', 'fingerprint']:
                        if field in task:
                            decrypted = simple_decrypt(task[field])
                            if decrypted:
                                task[field] = decrypted
            return data
    except:
        return {}

def save_user_tasks(data):
    safe_data = {}
    for sid, task in data.items():
        safe_task = task.copy()
        safe_task['encrypted'] = True
        for field in ['key', 'fingerprint']:
            if field in safe_task and safe_task[field]:
                safe_task[field] = simple_encrypt(safe_task[field])
        safe_data[sid] = safe_task
    with open(TASKS_FILE, 'w') as f:
        json.dump(safe_data, f, indent=2)

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {
            'total_keys_generated': 0,
            'total_keys_used': 0,
            'total_users': 0,
            'daily_users': {},
            'daily_keys': {}
        }
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            'total_keys_generated': 0,
            'total_keys_used': 0,
            'total_users': 0,
            'daily_users': {},
            'daily_keys': {}
        }

def save_stats(data):
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_stats(stat_type):
    stats = load_stats()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if stat_type == 'key_generated':
        stats['total_keys_generated'] += 1
        if today not in stats['daily_keys']:
            stats['daily_keys'][today] = 0
        stats['daily_keys'][today] += 1
    elif stat_type == 'key_used':
        stats['total_keys_used'] += 1
    elif stat_type == 'new_user':
        stats['total_users'] += 1
        if today not in stats['daily_users']:
            stats['daily_users'][today] = 0
        stats['daily_users'][today] += 1
    
    save_stats(stats)

# ========== TẠO LINK CALLBACK ==========
def create_signed_callback(session_id, step_num):
    timestamp = int(time.time())
    signature_data = f"{session_id}:{step_num}:{timestamp}"
    signature = hmac.new(ENCRYPTION_KEY.encode(), signature_data.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{YOUR_DOMAIN}/api/callback/{session_id}/{step_num}?ts={timestamp}&sig={signature}"

def verify_callback_signature(session_id, step_num, timestamp, signature):
    try:
        ts = int(timestamp)
        if abs(time.time() - ts) > 300:
            return False
        expected = hmac.new(ENCRYPTION_KEY.encode(), f"{session_id}:{step_num}:{timestamp}".encode(), hashlib.sha256).hexdigest()[:16]
        return hmac.compare_digest(signature, expected)
    except:
        return False

# ========== TẠO LINK NHIỆM VỤ ==========
def create_vuotnhanh_link(callback_url):
    try:
        encoded_url = urllib.parse.quote(callback_url, safe='')
        api_url = f"{VUOTNHANH_API_URL}?token={VUOTNHANH_API_KEY}&url={encoded_url}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            short_url = data.get('shortenedUrl') or data.get('short_url') or data.get('url') or callback_url
            update_earnings('vuotnhanh', 0.001)
            return short_url
        return callback_url
    except:
        return callback_url

def create_yeumoney_link(callback_url):
    try:
        encoded_url = urllib.parse.quote(callback_url, safe='')
        api_url = f"{YEUMONEY_API_URL}?token={YEUMONEY_API_KEY}&url={encoded_url}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            short_url = data.get('shortenedUrl') or data.get('shortUrl') or callback_url
            update_earnings('yeumoney', 0.002)
            return short_url
        return callback_url
    except:
        return callback_url

def create_link4m_link(callback_url):
    try:
        params = {'api': LINK4M_API_KEY, 'url': callback_url}
        response = requests.get(LINK4M_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success' and result.get('shortenedUrl'):
                update_earnings('link4m', 0.003)
                return result.get('shortenedUrl')
        return callback_url
    except:
        return callback_url

# ========== HTML TEMPLATES ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DRAGON PINGX PREMIUM | Hệ Thống Kích Hoạt</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #0f0f1a 50%, #0a0a0a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            position: relative;
            overflow-x: hidden;
        }
        .star {
            position: fixed;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            opacity: 0;
            animation: shootingStar 4s linear infinite;
        }
        @keyframes shootingStar {
            0% { transform: translateX(0) translateY(0); opacity: 0; }
            10% { opacity: 1; }
            20% { opacity: 1; }
            30% { opacity: 0; }
            100% { transform: translateX(-200px) translateY(200px); opacity: 0; }
        }
        .hero {
            text-align: center;
            max-width: 600px;
            animation: fadeInUp 0.8s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            position: relative;
            z-index: 2;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(50px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .badge {
            display: inline-block;
            background: rgba(176,0,255,0.15);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1.5rem;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #b000ff;
            border: 1px solid rgba(176,0,255,0.4);
            margin-bottom: 2rem;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(176,0,255,0.4); }
            50% { box-shadow: 0 0 0 15px rgba(176,0,255,0); }
        }
        h1 {
            font-size: 3.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #b000ff, #ff44ff);
            background-size: 300% 300%;
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 0.5rem;
            animation: gradientShift 4s ease infinite;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .sub {
            font-size: 1.1rem;
            color: #aaa;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        .btn-primary {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border: none;
            padding: 1rem 2.8rem;
            font-size: 1rem;
            font-weight: 600;
            color: white;
            border-radius: 60px;
            cursor: pointer;
            transition: all 0.4s;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            box-shadow: 0 5px 20px rgba(176,0,255,0.4);
        }
        .btn-primary:hover {
            transform: translateY(-5px) scale(1.05);
            box-shadow: 0 15px 40px rgba(176,0,255,0.6);
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 2.5rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(176,0,255,0.2);
        }
        .stat-number {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #888;
            margin-top: 0.3rem;
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="badge">✨ DRAGON PINGX PREMIUM | CHÍNH THỨC ✨</div>
        <h1>DRAGON PINGX</h1>
        <div class="sub">⚡ Hệ thống kích hoạt bản quyền tự động ⚡<br>🔒 Bảo mật tuyệt đối - 🚀 Tốc độ thần tốc</div>
        <a href="/getkey" class="btn-primary">
            🎁 NHẬN KEY MIỄN PHÍ
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
        <div class="stats">
            <div class="stat-item"><div class="stat-number">24/7</div><div class="stat-label">Hỗ trợ</div></div>
            <div class="stat-item"><div class="stat-number">2.5K+</div><div class="stat-label">Người dùng</div></div>
            <div class="stat-item"><div class="stat-number">100%</div><div class="stat-label">Uptime</div></div>
        </div>
    </div>
    <script>
        for(let i = 0; i < 50; i++) {
            let star = document.createElement('div');
            star.className = 'star';
            star.style.top = Math.random() * 100 + '%';
            star.style.left = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 8 + 's';
            star.style.animationDuration = (3 + Math.random() * 3) + 's';
            document.body.appendChild(star);
        }
    </script>
</body>
</html>
"""

STEP_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bước {{ step_index }} - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 550px;
            width: 100%;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            border: 1px solid rgba(176, 0, 255, 0.3);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            animation: fadeInScale 0.6s ease;
            text-align: center;
        }
        @keyframes fadeInScale {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        .step-badge {
            display: inline-block;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            padding: 0.5rem 1.5rem;
            border-radius: 100px;
            font-size: 0.8rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1.5rem;
        }
        h2 {
            color: white;
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #fff, #b000ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }
        .desc {
            color: #aaa;
            margin-bottom: 1.5rem;
        }
        .task-link {
            background: rgba(0,0,0,0.4);
            border-radius: 1rem;
            padding: 1rem;
            margin: 1.5rem 0;
            word-break: break-all;
        }
        .task-link a {
            color: #b000ff;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .btn-group {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        .btn-continue {
            flex: 1;
            background: linear-gradient(135deg, #00cc66, #00ff88);
            border: none;
            padding: 0.8rem;
            border-radius: 1rem;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-back {
            flex: 1;
            background: rgba(176,0,255,0.2);
            border: 1px solid rgba(176,0,255,0.5);
            padding: 0.8rem;
            border-radius: 1rem;
            color: #b000ff;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-continue:hover, .btn-back:hover {
            transform: translateY(-2px);
            filter: brightness(1.05);
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .warning {
            font-size: 0.7rem;
            color: #64748b;
            margin-top: 1rem;
        }
        .success-note {
            background: rgba(0,255,136,0.1);
            border: 1px solid rgba(0,255,136,0.3);
            border-radius: 0.8rem;
            padding: 0.8rem;
            margin: 1rem 0;
            font-size: 0.8rem;
            color: #00ff88;
        }
        .earnings-note {
            background: rgba(255,193,7,0.1);
            border: 1px solid rgba(255,193,7,0.3);
            border-radius: 0.8rem;
            padding: 0.5rem;
            margin: 0.5rem 0;
            font-size: 0.7rem;
            color: #ffc107;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="step-badge">📌 BƯỚC {{ step_index }}/{{ total_steps }}</div>
        <h2>{{ step_title }}</h2>
        <div class="desc">{{ step_desc }}</div>
        
        <div class="earnings-note">
            💰 Bạn đang giúp chúng tôi kiếm tiền từ quảng cáo! Cảm ơn bạn!
        </div>
        
        <div class="task-link">
            <div style="font-size:0.8rem; color:#64748b; margin-bottom:8px;">🔗 Link nhiệm vụ của bạn:</div>
            <a href="{{ task_url }}" target="_blank" id="taskLink">{{ task_url }}</a>
        </div>
        
        {% if step_index == 3 %}
        <div class="success-note">
            ⭐ Đây là bước cuối cùng! Hoàn thành nhiệm vụ để nhận KEY chính thức.
        </div>
        {% endif %}
        
        <div class="btn-group">
            <a href="{{ back_url }}" class="btn-back">🔙 Quay lại</a>
            <button class="btn-continue" onclick="checkComplete()" id="continueBtn">✅ Tiếp tục</button>
        </div>
        <div class="warning" id="warningMsg"></div>
    </div>
    
    <script>
        let sessionId = "{{ session_id }}";
        let step = {{ step_index }};
        let checking = false;
        
        async function checkComplete() {
            if (checking) return;
            checking = true;
            const btn = document.getElementById('continueBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Đang kiểm tra...';
            btn.disabled = true;
            
            try {
                const response = await fetch(`/api/check_step/${sessionId}/${step}`);
                const data = await response.json();
                
                if (data.completed) {
                    window.location.href = data.next_url;
                } else {
                    document.getElementById('warningMsg').innerHTML = '⚠️ Bạn chưa hoàn thành nhiệm vụ. Vui lòng hoàn thành và thử lại!';
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    checking = false;
                    window.open(document.getElementById('taskLink').href, '_blank');
                }
            } catch (error) {
                document.getElementById('warningMsg').innerHTML = '⚠️ Có lỗi xảy ra, vui lòng thử lại!';
                btn.innerHTML = originalText;
                btn.disabled = false;
                checking = false;
            }
        }
        
        window.open(document.getElementById('taskLink').href, '_blank');
    </script>
</body>
</html>
"""

FINAL_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thành Công - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .confetti {
            position: fixed;
            width: 10px;
            height: 10px;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            position: absolute;
            animation: confettiFall 3s linear forwards;
        }
        @keyframes confettiFall {
            0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
            100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
        }
        .card {
            max-width: 520px;
            width: 100%;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(176, 0, 255, 0.4);
            animation: bounceIn 0.8s ease;
            z-index: 2;
        }
        @keyframes bounceIn {
            0% { opacity: 0; transform: scale(0.7); }
            50% { opacity: 1; transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .success-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #00ff88, #00cc66);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            animation: pulseSuccess 1s infinite;
        }
        @keyframes pulseSuccess {
            0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,255,136,0.4); }
            50% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(0,255,136,0); }
        }
        h2 {
            color: white;
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #fff, #00ff88);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }
        .key-box {
            background: linear-gradient(135deg, #0f172a, #1a1a2e);
            border-radius: 1.2rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px dashed #b000ff;
            animation: glowPulse 2s infinite;
        }
        @keyframes glowPulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(176,0,255,0.2); }
            50% { box-shadow: 0 0 20px 0 rgba(176,0,255,0.4); }
        }
        .key-value {
            font-family: monospace;
            font-size: 1.3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            word-break: break-all;
            margin: 0.8rem 0;
            cursor: pointer;
            padding: 10px;
            border-radius: 10px;
        }
        .copy-btn {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border: none;
            padding: 0.7rem 1.8rem;
            border-radius: 2rem;
            color: white;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        .copy-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(176,0,255,0.4);
        }
        .btn-back {
            display: inline-block;
            background: rgba(176,0,255,0.2);
            text-decoration: none;
            color: #b000ff;
            padding: 0.7rem 1.5rem;
            border-radius: 2rem;
            font-weight: 600;
            margin-top: 1rem;
            border: 1px solid rgba(176,0,255,0.3);
            transition: all 0.3s;
        }
        .btn-back:hover {
            background: rgba(176,0,255,0.4);
            transform: translateY(-2px);
        }
        .warning {
            font-size: 0.7rem;
            color: #64748b;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="success-icon">
            <svg width="48" height="48" fill="none" stroke="white" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
        </div>
        <h2>🎉 THÀNH CÔNG! 🎉</h2>
        <div class="desc">Bạn đã hoàn thành tất cả nhiệm vụ</div>
        <div class="key-box">
            <div class="key-value" id="licenseKey" onclick="copyKey()">{{ key }}</div>
            <div>
                <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
            </div>
        </div>
        <div class="warning">
            ⏰ Key có hiệu lực trong 24 giờ<br>
            📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM để kích hoạt
        </div>
        <a href="/" class="btn-back">🏠 Về trang chủ</a>
    </div>
    
    <script>
        for(let i = 0; i < 100; i++) {
            let confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.animationDelay = Math.random() * 2 + 's';
            confetti.style.animationDuration = (2 + Math.random() * 2) + 's';
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), 3000);
        }
        
        function copyKey() {
            const key = document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(key).then(() => {
                alert('✅ Đã sao chép key!\\nKey: ' + key);
            });
        }
    </script>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Lỗi - DRAGON PINGX</title>
    <style>
        body { font-family: Arial; background: #0a0a0a; display: flex; align-items: center; justify-content: center; height: 100vh; color: white; }
        .card { background: #1a1a2e; padding: 2rem; border-radius: 1rem; text-align: center; }
        .error-icon { font-size: 3rem; color: #f87171; }
        .btn { background: #b000ff; color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; text-decoration: none; display: inline-block; margin-top: 1rem; }
    </style>
</head>
<body>
<div class="card">
<div class="error-icon">⚠️</div>
<h2>Đã xảy ra lỗi</h2>
<p>{{ message }}</p>
<a href="/getkey" class="btn">Thử lại</a>
</div>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - DRAGON PINGX</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .header h1 {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: rgba(15,23,42,0.9);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1.5rem;
            border: 1px solid rgba(176,0,255,0.3);
        }
        .stat-card h3 {
            color: #64748b;
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
        }
        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: #b000ff;
        }
        .section {
            background: rgba(15,23,42,0.9);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(176,0,255,0.3);
        }
        .section h2 {
            color: white;
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            color: #cbd5e1;
            border-bottom: 1px solid rgba(176,0,255,0.2);
        }
        th {
            color: #b000ff;
        }
        .btn {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
        }
        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        .logout {
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: rgba(239,68,68,0.2);
            color: #f87171;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            text-decoration: none;
        }
        input, textarea {
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(176,0,255,0.3);
            padding: 0.5rem;
            border-radius: 0.5rem;
            color: white;
            width: 100%;
            margin-bottom: 0.5rem;
        }
        .flex {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
    </style>
</head>
<body>
    <a href="/admin/logout" class="logout">🚪 Đăng xuất</a>
    <div class="container">
        <div class="header">
            <h1>🔐 DRAGON PINGX ADMIN PANEL</h1>
            <p style="color:#64748b">Quản lý hệ thống key</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 Tổng số key đã tạo</h3>
                <div class="value">{{ stats.total_keys_generated }}</div>
            </div>
            <div class="stat-card">
                <h3>✅ Tổng số key đã dùng</h3>
                <div class="value">{{ stats.total_keys_used }}</div>
            </div>
            <div class="stat-card">
                <h3>👥 Tổng số người dùng</h3>
                <div class="value">{{ stats.total_users }}</div>
            </div>
            <div class="stat-card">
                <h3>💰 Tổng thu nhập (USD)</h3>
                <div class="value">${{ "%.3f"|format(earnings.total) }}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>💰 Chi tiết thu nhập theo dịch vụ</h2>
            <table>
                <tr><th>Dịch vụ</th><th>Thu nhập (USD)</th></tr>
                <tr><td>Vuotnhanh.com</td><td>${{ "%.3f"|format(earnings.get('vuotnhanh', 0)) }}</td></tr>
                <tr><td>Yeumoney.com</td><td>${{ "%.3f"|format(earnings.get('yeumoney', 0)) }}</td></tr>
                <tr><td>Link4m.co</td><td>${{ "%.3f"|format(earnings.get('link4m', 0)) }}</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>🔑 Tạo key mới (thủ công)</h2>
            <form method="POST" action="/admin/create_key">
                <div class="flex">
                    <input type="text" name="note" placeholder="Ghi chú (tùy chọn)" style="flex:2">
                    <button type="submit" class="btn">➕ Tạo key mới</button>
                </div>
            </form>
        </div>
        
        <div class="section">
            <h2>🚫 Blacklist IP / Fingerprint</h2>
            <form method="POST" action="/admin/add_blacklist">
                <div class="flex">
                    <input type="text" name="ip" placeholder="Nhập IP cần chặn">
                    <input type="text" name="fingerprint" placeholder="Hoặc Fingerprint">
                    <button type="submit" class="btn btn-danger">🚫 Thêm vào Blacklist</button>
                </div>
            </form>
            <table style="margin-top:1rem">
                <tr><th>IP bị chặn</th><th>Fingerprint bị chặn</th><th>Hành động</th></tr>
                {% for ip in blacklist.ips %}
                <tr><td>{{ ip }}</td><td>-</td><td><a href="/admin/remove_blacklist?type=ip&value={{ ip }}" style="color:#f87171">Xóa</a></td></tr>
                {% endfor %}
                {% for fp in blacklist.fingerprints %}
                <tr><td>-</td><td>{{ fp[:24] }}...</td><td><a href="/admin/remove_blacklist?type=fingerprint&value={{ fp }}" style="color:#f87171">Xóa</a></td></tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="section">
            <h2>📋 Danh sách key gần đây</h2>
            <table>
                <tr><th>Key</th><th>Trạng thái</th><th>Hết hạn</th><th>Ngày tạo</th></tr>
                {% for k, v in keys.items() %}
                <tr>
                    <td><code>{{ k }}</code></td>
                    <td>{% if v.used %}✅ Đã dùng{% else %}🟢 Còn hiệu lực{% endif %}</td>
                    <td>{{ v.expires_at[:16] if v.expires_at else 'N/A' }}</td>
                    <td>{{ v.created_at[:16] if v.created_at else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""

# ========== ADMIN PANEL ROUTES ==========
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def authenticate():
    return app.make_response((
        'Unauthorized', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    ))

@app.route('/admin')
@admin_required
def admin_panel():
    stats = load_stats()
    earnings = load_earnings()
    blacklist = load_blacklist()
    keys = load_keys()
    recent_keys = dict(list(keys.items())[-50:])
    
    return render_template_string(ADMIN_HTML, 
        stats=stats, 
        earnings=earnings, 
        blacklist=blacklist,
        keys=recent_keys
    )

@app.route('/admin/create_key', methods=['POST'])
@admin_required
def admin_create_key():
    note = request.form.get('note', '')
    new_key = generate_dragon_key()
    expires_at = datetime.now() + timedelta(days=365)
    
    keys = load_keys()
    keys[new_key] = {
        'expires_at': expires_at.isoformat(),
        'used': False,
        'created_at': datetime.now().isoformat(),
        'note': note,
        'is_admin_key': True
    }
    save_keys(keys)
    update_stats('key_generated')
    
    send_telegram_message(f"👑 <b>Admin đã tạo key mới!</b>\n<code>{new_key}</code>\n📝 Ghi chú: {note}")
    
    return redirect('/admin')

@app.route('/admin/add_blacklist', methods=['POST'])
@admin_required
def admin_add_blacklist():
    ip = request.form.get('ip', '')
    fingerprint = request.form.get('fingerprint', '')
    
    if ip or fingerprint:
        add_to_blacklist(ip, fingerprint, "Admin thêm thủ công")
    
    return redirect('/admin')

@app.route('/admin/remove_blacklist')
@admin_required
def admin_remove_blacklist():
    btype = request.args.get('type')
    value = request.args.get('value')
    
    blacklist = load_blacklist()
    if btype == 'ip' and value in blacklist['ips']:
        blacklist['ips'].remove(value)
    elif btype == 'fingerprint' and value in blacklist['fingerprints']:
        blacklist['fingerprints'].remove(value)
    
    save_blacklist(blacklist)
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    return authenticate()

# ========== MAIN ROUTES ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    fingerprint = get_client_fingerprint(request)
    ip = request.remote_addr
    
    if is_blacklisted(ip, fingerprint):
        return render_template_string(ERROR_HTML, message="Truy cập của bạn đã bị chặn do vi phạm điều khoản.")
    
    if not rate_limit('generate_key', fingerprint):
        add_to_blacklist(ip, fingerprint, "Generate key rate limit exceeded")
        return render_template_string(ERROR_HTML, message="Bạn đang thực hiện quá nhiều yêu cầu. Vui lòng thử lại sau 5 phút.")
    
    session_id = generate_session_id()
    user_tasks = load_user_tasks()
    
    step1_callback = create_signed_callback(session_id, 1)
    step2_callback = create_signed_callback(session_id, 2)
    step3_callback = create_signed_callback(session_id, 3)
    
    step1_url = create_vuotnhanh_link(step1_callback)
    step2_url = create_yeumoney_link(step2_callback)
    step3_url = create_link4m_link(step3_callback)
    
    user_tasks[session_id] = {
        'step': 1,
        'step1_completed': False,
        'step2_completed': False,
        'step3_completed': False,
        'step1_url': step1_url,
        'step2_url': step2_url,
        'step3_url': step3_url,
        'created_at': datetime.now().isoformat(),
        'fingerprint': fingerprint,
        'ip': ip,
        'attempts': 0
    }
    save_user_tasks(user_tasks)
    
    update_stats('new_user')
    notify_new_user(ip, fingerprint)
    
    return redirect(f'/step/{session_id}/1')

@app.route('/step/<session_id>/<int:step_num>')
def show_step(session_id, step_num):
    user_tasks = load_user_tasks()
    fingerprint = get_client_fingerprint(request)
    
    if session_id not in user_tasks:
        return render_template_string(ERROR_HTML, message="Phiên không hợp lệ!")
    
    task_data = user_tasks[session_id]
    
    if task_data.get('fingerprint') != fingerprint:
        return render_template_string(ERROR_HTML, message="Phát hiện truy cập trái phép. Phiên đã bị khóa.")
    
    steps_config = {
        1: {'title': '🚀 Vượt Nhanh', 'desc': 'Hoàn thành nhiệm vụ trên Vượt Nhanh để tiếp tục', 'url_key': 'step1_url', 'back_url': '/getkey'},
        2: {'title': '💰 Yeumoney', 'desc': 'Hoàn thành nhiệm vụ trên Yeumoney để tiếp tục', 'url_key': 'step2_url', 'back_url': f'/step/{session_id}/1'},
        3: {'title': '🔗 Link4M', 'desc': 'Hoàn thành nhiệm vụ cuối cùng trên Link4M để nhận KEY', 'url_key': 'step3_url', 'back_url': f'/step/{session_id}/2'}
    }
    
    config = steps_config.get(step_num)
    if not config:
        return render_template_string(ERROR_HTML, message="Bước không hợp lệ!")
    
    return render_template_string(STEP_HTML,
        step_index=step_num,
        step_title=config['title'],
        step_desc=config['desc'],
        task_url=task_data.get(config['url_key'], '#'),
        session_id=session_id,
        total_steps=3,
        back_url=config['back_url']
    )

@app.route('/api/callback/<session_id>/<int:step_num>')
def step_callback(session_id, step_num):
    timestamp = request.args.get('ts')
    signature = request.args.get('sig')
    
    if not verify_callback_signature(session_id, step_num, timestamp, signature):
        return "Invalid signature", 403
    
    user_tasks = load_user_tasks()
    if session_id not in user_tasks:
        return "Session not found", 404
    
    task_data = user_tasks[session_id]
    
    if step_num == 1:
        task_data['step1_completed'] = True
        task_data['step'] = 2
        update_earnings('vuotnhanh_completed', 0.0005)
    elif step_num == 2:
        task_data['step2_completed'] = True
        task_data['step'] = 3
        update_earnings('yeumoney_completed', 0.001)
    elif step_num == 3:
        task_data['step3_completed'] = True
        new_key = generate_dragon_key()
        expires_at = datetime.now() + timedelta(hours=24)
        keys = load_keys()
        keys[new_key] = {
            'expires_at': expires_at.isoformat(),
            'used': False,
            'created_at': datetime.now().isoformat(),
            'session_id': session_id
        }
        save_keys(keys)
        task_data['key'] = new_key
        task_data['key_expires'] = expires_at.isoformat()
        
        update_stats('key_generated')
        notify_new_key(new_key, task_data.get('ip', 'unknown'), task_data.get('fingerprint', 'unknown'))
        notify_completed_all_tasks(task_data.get('fingerprint', 'unknown'), new_key)
        
        update_earnings('link4m_completed', 0.002)
    
    save_user_tasks(user_tasks)
    return "OK"

@app.route('/api/check_step/<session_id>/<int:step_num>')
def check_step(session_id, step_num):
    fingerprint = get_client_fingerprint(request)
    
    if not rate_limit('check_step', fingerprint):
        return jsonify({'completed': False, 'error': 'Rate limit'}), 429
    
    user_tasks = load_user_tasks()
    if session_id not in user_tasks:
        return jsonify({'completed': False, 'error': 'Session not found'})
    
    task_data = user_tasks[session_id]
    
    if task_data.get('fingerprint') != fingerprint:
        return jsonify({'completed': False, 'error': 'Invalid session'})
    
    completed = False
    next_url = None
    
    if step_num == 1 and task_data.get('step1_completed'):
        completed = True
        next_url = f'/step/{session_id}/2'
    elif step_num == 2 and task_data.get('step2_completed'):
        completed = True
        next_url = f'/step/{session_id}/3'
    elif step_num == 3 and task_data.get('step3_completed'):
        completed = True
        next_url = f'/final/{session_id}'
    
    return jsonify({'completed': completed, 'next_url': next_url})

@app.route('/final/<session_id>')
def final_step(session_id):
    fingerprint = get_client_fingerprint(request)
    user_tasks = load_user_tasks()
    
    if session_id not in user_tasks:
        return render_template_string(ERROR_HTML, message="Phiên không hợp lệ!")
    
    task_data = user_tasks[session_id]
    
    if task_data.get('fingerprint') != fingerprint:
        return render_template_string(ERROR_HTML, message="Phát hiện truy cập trái phép.")
    
    key = task_data.get('key')
    if not key:
        return render_template_string(ERROR_HTML, message="Chưa có key! Vui lòng hoàn thành các bước trước.")
    
    return render_template_string(FINAL_HTML, key=key)

@app.route('/api/verify', methods=['POST'])
def verify_key():
    fingerprint = get_client_fingerprint(request)
    ip = request.remote_addr
    
    if is_blacklisted(ip, fingerprint):
        return jsonify({'status': 'error', 'message': 'Truy cập bị chặn'}), 403
    
    if not rate_limit('verify_key', fingerprint):
        add_to_blacklist(ip, fingerprint, "Verify key rate limit exceeded")
        return jsonify({'status': 'error', 'message': 'Quá nhiều lần thử. Bạn đã bị chặn tạm thời.'}), 429
    
    data = request.json
    key = data.get('key', '').strip().upper()
    
    if not key:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập key!'})
    
    if not verify_key_checksum(key):
        return jsonify({'status': 'invalid', 'message': '❌ Key không hợp lệ!'})
    
    admin_keys = ["QANHNO1CRACKER", "DRAGONLOCUT", "DRAGONLOCUT2024"]
    if key in admin_keys:
        return jsonify({'status': 'success', 'message': '✅ Kích hoạt thành công!', 'key': key, 'expires_at': (datetime.now() + timedelta(days=365)).isoformat()})
    
    keys = load_keys()
    if key not in keys:
        return jsonify({'status': 'invalid', 'message': '❌ Key không hợp lệ!'})
    
    info = keys[key]
    expires_at = datetime.fromisoformat(info['expires_at'])
    
    if datetime.now() > expires_at:
        return jsonify({'status': 'expired', 'message': '❌ Key đã hết hạn!'})
    
    if info.get('used', False):
        return jsonify({'status': 'used', 'message': '❌ Key đã được sử dụng!'})
    
    info['used'] = True
    info['used_at'] = datetime.now().isoformat()
    info['used_by_fingerprint'] = fingerprint
    save_keys(keys)
    
    update_stats('key_used')
    notify_key_used(key, ip, fingerprint)
    
    return jsonify({'status': 'success', 'message': '✅ Key hợp lệ!', 'key': key, 'expires_at': expires_at.isoformat()})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = load_stats()
    earnings = load_earnings()
    return jsonify({
        'total_keys_generated': stats.get('total_keys_generated', 0),
        'total_keys_used': stats.get('total_keys_used', 0),
        'total_users': stats.get('total_users', 0),
        'total_earnings_usd': earnings.get('total', 0)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)