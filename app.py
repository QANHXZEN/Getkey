from flask import Flask, request, jsonify, render_template_string, redirect, session
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
import threading
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ========== CẤU HÌNH API ==========
LINK4M_API_KEY = os.environ.get("LINK4M_API_KEY", "65c47d157fbdff4d79625e57")
LINK4M_API_URL = "https://link4m.co/api-shorten/v2"

YEUMONEY_API_KEY = os.environ.get("YEUMONEY_API_KEY", "4e3bbf63ff3ac2f780f246675412f35c3f31946a74f195992dbaf2a6d6c26eee")
YEUMONEY_API_URL = "https://yeumoney.com/QL_api.php"

VUOTNHANH_API_KEY = os.environ.get("VUOTNHANH_API_KEY", "e7c716d2-996f-4bdd-bcbf-7653223a400b")
VUOTNHANH_API_URL = "https://vuotnhanh.com/api"

YOUR_DOMAIN = os.environ.get("YOUR_DOMAIN", "https://roszmodxqanhno1.onrender.com")

# ========== TELEGRAM BOT ==========
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8448578289:AAH2Pp6s3V1Le-cV5I1Qc-gFKQzTDBMXnvA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8588555065")

# ========== ADMIN PANEL ==========
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Dragon@2024")

# ========== BẢO MẬT ==========
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", secrets.token_hex(32))
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30

# ========== FILE LƯU TRỮ ==========
KEYS_FILE = "keys.json"
TASKS_FILE = "user_tasks.json"
BLACKLIST_FILE = "blacklist.json"
RATE_LIMIT_FILE = "rate_limit.json"
STATS_FILE = "stats.json"
EARNINGS_FILE = "earnings.json"
SETTINGS_FILE = "settings.json"

# ========== HÀM TIỆN ÍCH ==========
def load_json_file(filename, default=None):
    if default is None:
        default = {}
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Lỗi đọc file {filename}: {e}")
        return default

def save_json_file(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Lỗi ghi file {filename}: {e}")
        return False

# ========== TELEGRAM ==========
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message[:4000], 'parse_mode': 'HTML'}
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

def notify_new_key(key, user_ip, fingerprint):
    send_telegram_message(f"""
🔑 <b>KEY MỚI ĐƯỢC TẠO!</b>
━━━━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>ID:</b> {fingerprint[:20]}...
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━
✅ Có hiệu lực 24 giờ
    """)

def notify_key_used(key, user_ip, fingerprint):
    send_telegram_message(f"""
✅ <b>KEY ĐÃ ĐƯỢC KÍCH HOẠT!</b>
━━━━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>ID:</b> {fingerprint[:20]}...
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━
🎉 Chúc mừng!
    """)

def notify_new_user(ip, fingerprint):
    send_telegram_message(f"""
👤 <b>NGƯỜI DÙNG MỚI!</b>
━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> {ip}
🆔 <b>ID:</b> {fingerprint[:20]}...
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)

# ========== BẢO MẬT ==========
def encrypt_data(text):
    if not text:
        return text
    key = ENCRYPTION_KEY.encode()[:32]
    result = bytearray()
    for i, c in enumerate(str(text)):
        result.append(ord(c) ^ key[i % len(key)])
    return result.hex()

def decrypt_data(hex_text):
    if not hex_text:
        return hex_text
    try:
        data = bytes.fromhex(hex_text)
        key = ENCRYPTION_KEY.encode()[:32]
        result = []
        for i, b in enumerate(data):
            result.append(chr(b ^ key[i % len(key)]))
        return ''.join(result)
    except:
        return None

def generate_key():
    chars = string.ascii_uppercase + string.digits
    p1 = ''.join(secrets.choice(chars) for _ in range(6))
    p2 = ''.join(secrets.choice(chars) for _ in range(4))
    raw = f"DRP-{p1}-{p2}"
    checksum = hashlib.md5(raw.encode()).hexdigest()[:2].upper()
    return f"{raw}-{checksum}"

def verify_key_checksum(key):
    if not key or len(key) < 15:
        return False
    match = re.match(r'^DRP-[A-Z0-9]{6}-[A-Z0-9]{4}-([A-Z0-9]{2})$', key)
    if not match:
        return False
    provided = match.group(1)
    raw = key[:-3]
    expected = hashlib.md5(raw.encode()).hexdigest()[:2].upper()
    return hmac.compare_digest(provided, expected)

def get_fingerprint():
    ua = request.headers.get('User-Agent', 'unknown')
    al = request.headers.get('Accept-Language', 'unknown')
    ip = request.remote_addr
    return hashlib.sha256(f"{ip}|{ua}|{al}".encode()).hexdigest()[:32]

def generate_session():
    return secrets.token_hex(24)

def rate_limit_check(action, identifier):
    rate_data = load_json_file(RATE_LIMIT_FILE, {})
    now = time.time()
    key = f"{action}:{identifier}"
    
    if key not in rate_data:
        rate_data[key] = {'count': 1, 'first': now}
        save_json_file(RATE_LIMIT_FILE, rate_data)
        return True
    
    record = rate_data[key]
    if now - record['first'] > RATE_LIMIT_WINDOW:
        record['count'] = 1
        record['first'] = now
        save_json_file(RATE_LIMIT_FILE, rate_data)
        return True
    
    if record['count'] >= RATE_LIMIT_MAX:
        return False
    
    record['count'] += 1
    save_json_file(RATE_LIMIT_FILE, rate_data)
    return True

def is_blocked(ip, fp):
    blacklist = load_json_file(BLACKLIST_FILE, {'ips': [], 'fingerprints': []})
    return ip in blacklist.get('ips', []) or fp in blacklist.get('fingerprints', [])

def add_to_blacklist(ip, fp, reason):
    blacklist = load_json_file(BLACKLIST_FILE, {'ips': [], 'fingerprints': []})
    if ip and ip not in blacklist['ips']:
        blacklist['ips'].append(ip)
    if fp and fp not in blacklist['fingerprints']:
        blacklist['fingerprints'].append(fp)
    save_json_file(BLACKLIST_FILE, blacklist)
    send_telegram_message(f"🚫 BLACKLIST: {ip} | {fp[:20]}... | {reason}")

# ========== QUẢN LÝ KEY ==========
def save_key(key, expires_hours=24):
    keys = load_json_file(KEYS_FILE, {})
    keys[key] = {
        'expires': (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
        'used': False,
        'created': datetime.now().isoformat()
    }
    save_json_file(KEYS_FILE, keys)
    return keys[key]

def use_key(key, fingerprint):
    keys = load_json_file(KEYS_FILE, {})
    if key not in keys:
        return False, "Key không tồn tại"
    
    info = keys[key]
    expires = datetime.fromisoformat(info['expires'])
    
    if datetime.now() > expires:
        return False, "Key đã hết hạn"
    
    if info.get('used', False):
        return False, "Key đã được sử dụng"
    
    info['used'] = True
    info['used_at'] = datetime.now().isoformat()
    info['used_by'] = fingerprint
    save_json_file(KEYS_FILE, keys)
    return True, "Thành công"

# ========== QUẢN LÝ TASK ==========
def create_task(session_id, fingerprint, ip):
    tasks = load_json_file(TASKS_FILE, {})
    
    step1_cb = f"{YOUR_DOMAIN}/api/cb/{session_id}/1?t={int(time.time())}"
    step2_cb = f"{YOUR_DOMAIN}/api/cb/{session_id}/2?t={int(time.time())}"
    step3_cb = f"{YOUR_DOMAIN}/api/cb/{session_id}/3?t={int(time.time())}"
    
    tasks[session_id] = {
        'step': 1,
        's1': False, 's2': False, 's3': False,
        'fp': fingerprint,
        'ip': ip,
        'created': datetime.now().isoformat()
    }
    save_json_file(TASKS_FILE, tasks)
    
    # Tạo link rút gọn
    url1 = step1_cb
    url2 = step2_cb
    url3 = step3_cb
    
    try:
        # Yeumoney
        yeu_resp = requests.get(f"{YEUMONEY_API_URL}?token={YEUMONEY_API_KEY}&url={urllib.parse.quote(url2)}&format=json", timeout=10)
        if yeu_resp.status_code == 200:
            yeu_data = yeu_resp.json()
            url2 = yeu_data.get('shortenedUrl') or yeu_data.get('shortUrl') or url2
        
        # Link4M
        l4m_resp = requests.get(LINK4M_API_URL, params={'api': LINK4M_API_KEY, 'url': url3}, timeout=10)
        if l4m_resp.status_code == 200:
            l4m_data = l4m_resp.json()
            if l4m_data.get('status') == 'success' and l4m_data.get('shortenedUrl'):
                url3 = l4m_data.get('shortenedUrl')
    except:
        pass
    
    tasks[session_id]['url1'] = url1
    tasks[session_id]['url2'] = url2
    tasks[session_id]['url3'] = url3
    save_json_file(TASKS_FILE, tasks)
    
    return tasks[session_id]

# ========== THỐNG KÊ ==========
def update_stats(type):
    stats = load_json_file(STATS_FILE, {'total_keys': 0, 'total_used': 0, 'total_users': 0})
    today = datetime.now().strftime('%Y-%m-%d')
    
    if 'daily' not in stats:
        stats['daily'] = {}
    if today not in stats['daily']:
        stats['daily'][today] = {'keys': 0, 'used': 0, 'users': 0}
    
    if type == 'key':
        stats['total_keys'] = stats.get('total_keys', 0) + 1
        stats['daily'][today]['keys'] += 1
    elif type == 'used':
        stats['total_used'] = stats.get('total_used', 0) + 1
        stats['daily'][today]['used'] += 1
    elif type == 'user':
        stats['total_users'] = stats.get('total_users', 0) + 1
        stats['daily'][today]['users'] += 1
    
    save_json_file(STATS_FILE, stats)

def update_earnings(service, amount):
    earnings = load_json_file(EARNINGS_FILE, {'total': 0})
    today = datetime.now().strftime('%Y-%m-%d')
    if 'daily' not in earnings:
        earnings['daily'] = {}
    if today not in earnings['daily']:
        earnings['daily'][today] = {}
    earnings['daily'][today][service] = earnings['daily'][today].get(service, 0) + amount
    earnings['total'] = earnings.get('total', 0) + amount
    save_json_file(EARNINGS_FILE, earnings)

# ========== HTML TEMPLATES ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a 0%,#0f0f1a 50%,#0a0a0a 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .hero{text-align:center;max-width:600px}
        .badge{display:inline-block;background:rgba(176,0,255,0.15);backdrop-filter:blur(10px);padding:8px 24px;border-radius:100px;font-size:12px;font-weight:600;color:#b000ff;border:1px solid rgba(176,0,255,0.4);margin-bottom:30px}
        h1{font-size:60px;font-weight:800;background:linear-gradient(135deg,#fff,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px}
        .sub{font-size:16px;color:#aaa;margin-bottom:30px;line-height:1.6}
        .btn{background:linear-gradient(135deg,#b000ff,#ff44ff);border:none;padding:16px 45px;font-size:16px;font-weight:600;color:#fff;border-radius:60px;cursor:pointer;display:inline-flex;align-items:center;gap:10px;text-decoration:none;box-shadow:0 5px 20px rgba(176,0,255,0.4);transition:0.3s}
        .btn:hover{transform:translateY(-5px) scale(1.05);box-shadow:0 15px 40px rgba(176,0,255,0.6)}
        .stats{display:flex;justify-content:center;gap:40px;margin-top:50px;padding-top:30px;border-top:1px solid rgba(176,0,255,0.2)}
        .stat-number{font-size:28px;font-weight:700;background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent}
        .stat-label{font-size:12px;color:#888;margin-top:5px}
        @keyframes fadeIn{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
        .hero{animation:fadeIn 0.8s}
    </style>
</head>
<body>
    <div class="hero">
        <div class="badge">✨ DRAGON PINGX PREMIUM | CHÍNH THỨC ✨</div>
        <h1>DRAGON PINGX</h1>
        <div class="sub">⚡ Hệ thống kích hoạt bản quyền tự động ⚡<br>🔒 Bảo mật tuyệt đối - 🚀 Tốc độ thần tốc</div>
        <a href="/getkey" class="btn">🎁 NHẬN KEY MIỄN PHÍ →</a>
        <div class="stats">
            <div><div class="stat-number">24/7</div><div class="stat-label">Hỗ trợ</div></div>
            <div><div class="stat-number">2.5K+</div><div class="stat-label">Người dùng</div></div>
            <div><div class="stat-number">100%</div><div class="stat-label">Uptime</div></div>
        </div>
    </div>
</body>
</html>
"""

STEP_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bước {{ step }} - DRAGON PINGX</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .card{max-width:550px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:32px;border:1px solid rgba(176,0,255,0.3);text-align:center}
        .step-badge{background:linear-gradient(135deg,#b000ff,#ff44ff);padding:8px 24px;border-radius:100px;font-size:13px;font-weight:700;color:#fff;display:inline-block;margin-bottom:24px}
        h2{font-size:28px;background:linear-gradient(135deg,#fff,#b000ff);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px}
        .desc{color:#aaa;margin-bottom:24px}
        .task-link{background:rgba(0,0,0,0.4);border-radius:16px;padding:16px;margin:24px 0;word-break:break-all}
        .task-link a{color:#b000ff;text-decoration:none;font-size:14px}
        .btn-group{display:flex;gap:16px;margin-top:24px}
        .btn-continue{flex:1;background:linear-gradient(135deg,#00cc66,#00ff88);border:none;padding:12px;border-radius:16px;color:#fff;font-weight:600;cursor:pointer}
        .btn-back{flex:1;background:rgba(176,0,255,0.2);border:1px solid rgba(176,0,255,0.5);padding:12px;border-radius:16px;color:#b000ff;font-weight:600;text-decoration:none;display:inline-block;text-align:center}
        .warning{font-size:12px;color:#64748b;margin-top:16px}
        .loading{display:inline-block;width:18px;height:18px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.8s linear infinite}
        @keyframes spin{to{transform:rotate(360deg)}}
        .info{background:rgba(255,193,7,0.1);border:1px solid rgba(255,193,7,0.3);border-radius:12px;padding:10px;margin:10px 0;font-size:12px;color:#ffc107}
    </style>
</head>
<body>
    <div class="card">
        <div class="step-badge">📌 BƯỚC {{ step }}/3</div>
        <h2>{{ title }}</h2>
        <div class="desc">{{ desc }}</div>
        <div class="info">💰 Bạn đang giúp chúng tôi kiếm tiền từ quảng cáo! Cảm ơn bạn!</div>
        <div class="task-link">
            <div style="font-size:12px;color:#64748b;margin-bottom:8px;">🔗 Link nhiệm vụ của bạn:</div>
            <a href="{{ url }}" target="_blank" id="taskLink">{{ url }}</a>
        </div>
        <div class="btn-group">
            <a href="{{ back_url }}" class="btn-back">🔙 Quay lại</a>
            <button class="btn-continue" onclick="check()" id="continueBtn">✅ Tiếp tục</button>
        </div>
        <div class="warning" id="warningMsg"></div>
    </div>
    <script>
        let sid = "{{ sid }}";
        let step = {{ step }};
        let checking = false;
        
        async function check() {
            if(checking) return;
            checking = true;
            const btn = document.getElementById('continueBtn');
            const original = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Đang kiểm tra...';
            btn.disabled = true;
            
            try {
                const res = await fetch(`/api/check/${sid}/${step}`);
                const data = await res.json();
                if(data.completed) {
                    window.location.href = data.next;
                } else {
                    document.getElementById('warningMsg').innerHTML = '⚠️ Bạn chưa hoàn thành nhiệm vụ. Vui lòng hoàn thành và thử lại!';
                    btn.innerHTML = original;
                    btn.disabled = false;
                    checking = false;
                    window.open(document.getElementById('taskLink').href, '_blank');
                }
            } catch(e) {
                document.getElementById('warningMsg').innerHTML = '⚠️ Có lỗi xảy ra, vui lòng thử lại!';
                btn.innerHTML = original;
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
    <title>Thành Công - DRAGON PINGX</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .card{max-width:520px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:32px;text-align:center;border:1px solid rgba(176,0,255,0.4)}
        .success-icon{width:80px;height:80px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 24px}
        h2{font-size:32px;background:linear-gradient(135deg,#fff,#00ff88);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px}
        .key-box{background:linear-gradient(135deg,#0f172a,#1a1a2e);border-radius:20px;padding:24px;margin:24px 0;border:1px dashed #b000ff}
        .key-value{font-family:monospace;font-size:20px;font-weight:700;background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent;word-break:break-all;margin:12px 0;cursor:pointer}
        .copy-btn{background:linear-gradient(135deg,#b000ff,#ff44ff);border:none;padding:10px 28px;border-radius:32px;color:#fff;cursor:pointer;font-weight:600}
        .btn-back{display:inline-block;background:rgba(176,0,255,0.2);text-decoration:none;color:#b000ff;padding:10px 24px;border-radius:32px;margin-top:16px}
        .warning{font-size:12px;color:#64748b;margin:16px 0}
        .confetti{position:fixed;width:10px;height:10px;background:linear-gradient(135deg,#b000ff,#ff44ff);animation:fall 3s linear forwards}
        @keyframes fall{0%{transform:translateY(-100vh) rotate(0deg)}100%{transform:translateY(100vh) rotate(360deg);opacity:0}}
    </style>
</head>
<body>
    <div class="card">
        <div class="success-icon"><svg width="48" height="48" fill="none" stroke="white" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg></div>
        <h2>🎉 THÀNH CÔNG! 🎉</h2>
        <div class="desc">Bạn đã hoàn thành tất cả nhiệm vụ</div>
        <div class="key-box">
            <div class="key-value" id="licenseKey" onclick="copyKey()">{{ key }}</div>
            <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
        </div>
        <div class="warning">⏰ Key có hiệu lực trong 24 giờ<br>📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM để kích hoạt</div>
        <a href="/" class="btn-back">🏠 Về trang chủ</a>
    </div>
    <script>
        for(let i=0;i<100;i++){
            let c=document.createElement('div');
            c.className='confetti';
            c.style.left=Math.random()*100+'%';
            c.style.animationDelay=Math.random()*2+'s';
            c.style.animationDuration=(2+Math.random()*2)+'s';
            document.body.appendChild(c);
            setTimeout(()=>c.remove(),3000);
        }
        function copyKey(){
            const key=document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(key).then(()=>alert('✅ Đã sao chép key!\\nKey: '+key));
        }
    </script>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><title>Lỗi - DRAGON PINGX</title><style>body{font-family:Arial;background:#0a0a0a;display:flex;align-items:center;justify-content:center;height:100vh;color:#fff}.card{background:#1a1a2e;padding:32px;border-radius:16px;text-align:center}.error-icon{font-size:48px;color:#f87171}.btn{background:#b000ff;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block;margin-top:16px}</style></head>
<body><div class="card"><div class="error-icon">⚠️</div><h2>Đã xảy ra lỗi</h2><p>{{ msg }}</p><a href="/getkey" class="btn">Thử lại</a></div></body></html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;padding:32px}
.container{max-width:1200px;margin:0 auto}
.header{text-align:center;margin-bottom:32px}
.header h1{background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px}
.stat-card{background:rgba(15,23,42,0.9);border-radius:16px;padding:20px;border:1px solid rgba(176,0,255,0.3)}
.stat-card h3{color:#64748b;font-size:12px;margin-bottom:8px}
.stat-card .value{font-size:32px;font-weight:700;color:#b000ff}
.section{background:rgba(15,23,42,0.9);border-radius:16px;padding:24px;margin-bottom:24px;border:1px solid rgba(176,0,255,0.3)}
.section h2{color:#fff;margin-bottom:16px;font-size:20px}
.logout{position:fixed;top:16px;right:16px;background:rgba(239,68,68,0.2);color:#f87171;padding:8px 16px;border-radius:8px;text-decoration:none}
input,textarea{background:rgba(0,0,0,0.3);border:1px solid rgba(176,0,255,0.3);padding:10px;border-radius:8px;color:#fff;width:100%}
.btn{background:linear-gradient(135deg,#b000ff,#ff44ff);color:#fff;border:none;padding:10px 20px;border-radius:8px;cursor:pointer}
.btn-danger{background:linear-gradient(135deg,#ef4444,#dc2626)}
.flex{display:flex;gap:16px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse}
th,td{padding:12px;text-align:left;color:#cbd5e1;border-bottom:1px solid rgba(176,0,255,0.2)}
th{color:#b000ff}
</style></head>
<body><a href="/admin/logout" class="logout">🚪 Đăng xuất</a><div class="container"><div class="header"><h1>🔐 DRAGON PINGX ADMIN</h1><p style="color:#64748b">Quản lý hệ thống key</p></div><div class="stats-grid"><div class="stat-card"><h3>📊 Tổng key đã tạo</h3><div class="value">{{ stats.total_keys }}</div></div><div class="stat-card"><h3>✅ Key đã dùng</h3><div class="value">{{ stats.total_used }}</div></div><div class="stat-card"><h3>👥 Người dùng</h3><div class="value">{{ stats.total_users }}</div></div><div class="stat-card"><h3>💰 Thu nhập (USD)</h3><div class="value">${{ "%.3f"|format(earnings.total) }}</div></div></div><div class="section"><h2>💰 Chi tiết thu nhập</h2><table><th>Dịch vụ</th><th>USD</th></tr>

{% for k,v in earnings.daily.items() %}
{% for sk,sv in v.items() if sk != 'total' %}
<tr><td>{{ sk }}</td><td>${{ "%.4f"|format(sv) }}</td></tr>
{% endfor %}
{% endfor %}
</table></div><div class="section"><h2>🔑 Tạo key mới</h2><form method="POST" action="/admin/create_key"><div class="flex"><input type="text" name="note" placeholder="Ghi chú"><button type="submit" class="btn">➕ Tạo key</button></div></form></div><div class="section"><h2>🚫 Blacklist IP</h2><form method="POST" action="/admin/blacklist"><div class="flex"><input type="text" name="ip" placeholder="IP cần chặn"><button type="submit" class="btn btn-danger">🚫 Thêm</button></div></form><table style="margin-top:16px"><tr><th>IP bị chặn</th><th>Hành động</th></tr>{% for ip in blacklist.ips %}<tr><td>{{ ip }}</td><td><a href="/admin/unban?ip={{ ip }}" style="color:#f87171">Xóa</a></td></tr>{% endfor %}</table></div></div></body></html>
"""

# ========== ROUTES ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    fp = get_fingerprint()
    ip = request.remote_addr
    
    if is_blocked(ip, fp):
        return render_template_string(ERROR_HTML, msg="Truy cập bị chặn")
    
    if not rate_limit_check('getkey', fp):
        add_to_blacklist(ip, fp, "Rate limit exceeded")
        return render_template_string(ERROR_HTML, msg="Quá nhiều yêu cầu. Thử lại sau 1 phút.")
    
    sid = generate_session()
    task = create_task(sid, fp, ip)
    update_stats('user')
    notify_new_user(ip, fp)
    
    return redirect(f'/step/{sid}/1')

@app.route('/step/<sid>/<int:step>')
def step_page(sid, step):
    tasks = load_json_file(TASKS_FILE, {})
    fp = get_fingerprint()
    
    if sid not in tasks:
        return render_template_string(ERROR_HTML, msg="Phiên không hợp lệ!")
    
    task = tasks[sid]
    if task.get('fp') != fp:
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!")
    
    config = {
        1: {'title': '🚀 Vượt Nhanh', 'desc': 'Hoàn thành nhiệm vụ trên Vượt Nhanh', 'url': task.get('url1', '#'), 'back': '/getkey'},
        2: {'title': '💰 Yeumoney', 'desc': 'Hoàn thành nhiệm vụ trên Yeumoney', 'url': task.get('url2', '#'), 'back': f'/step/{sid}/1'},
        3: {'title': '🔗 Link4M', 'desc': 'Hoàn thành nhiệm vụ cuối cùng', 'url': task.get('url3', '#'), 'back': f'/step/{sid}/2'}
    }
    
    cfg = config.get(step)
    if not cfg:
        return render_template_string(ERROR_HTML, msg="Bước không hợp lệ!")
    
    return render_template_string(STEP_HTML, step=step, title=cfg['title'], desc=cfg['desc'], url=cfg['url'], sid=sid, back_url=cfg['back'])

@app.route('/api/cb/<sid>/<int:step>')
def callback(sid, step):
    tasks = load_json_file(TASKS_FILE, {})
    
    if sid not in tasks:
        return "Session not found", 404
    
    task = tasks[sid]
    
    if step == 1:
        task['s1'] = True
        task['step'] = 2
        update_earnings('vuotnhanh', 0.0005)
    elif step == 2:
        task['s2'] = True
        task['step'] = 3
        update_earnings('yeumoney', 0.001)
    elif step == 3:
        task['s3'] = True
        new_key = generate_key()
        save_key(new_key, 24)
        task['key'] = new_key
        update_stats('key')
        notify_new_key(new_key, task.get('ip', 'unknown'), task.get('fp', 'unknown'))
        update_earnings('link4m', 0.002)
    
    save_json_file(TASKS_FILE, tasks)
    return "OK"

@app.route('/api/check/<sid>/<int:step>')
def check_step(sid, step):
    fp = get_fingerprint()
    
    if not rate_limit_check('check', fp):
        return jsonify({'completed': False, 'error': 'Rate limit'})
    
    tasks = load_json_file(TASKS_FILE, {})
    
    if sid not in tasks:
        return jsonify({'completed': False, 'error': 'Not found'})
    
    task = tasks[sid]
    if task.get('fp') != fp:
        return jsonify({'completed': False, 'error': 'Invalid'})
    
    completed = False
    next_url = None
    
    if step == 1 and task.get('s1'):
        completed = True
        next_url = f'/step/{sid}/2'
    elif step == 2 and task.get('s2'):
        completed = True
        next_url = f'/step/{sid}/3'
    elif step == 3 and task.get('s3'):
        completed = True
        next_url = f'/final/{sid}'
    
    return jsonify({'completed': completed, 'next': next_url})

@app.route('/final/<sid>')
def final(sid):
    tasks = load_json_file(TASKS_FILE, {})
    fp = get_fingerprint()
    
    if sid not in tasks:
        return render_template_string(ERROR_HTML, msg="Phiên không hợp lệ!")
    
    task = tasks[sid]
    if task.get('fp') != fp:
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!")
    
    key = task.get('key')
    if not key:
        return render_template_string(ERROR_HTML, msg="Chưa có key! Hoàn thành các bước trước.")
    
    return render_template_string(FINAL_HTML, key=key)

@app.route('/api/verify', methods=['POST'])
def verify():
    fp = get_fingerprint()
    ip = request.remote_addr
    
    if is_blocked(ip, fp):
        return jsonify({'status': 'error', 'message': 'Bị chặn'}), 403
    
    if not rate_limit_check('verify', fp):
        add_to_blacklist(ip, fp, "Verify rate limit")
        return jsonify({'status': 'error', 'message': 'Quá nhiều lần thử'}), 429
    
    data = request.json
    key = data.get('key', '').strip().upper()
    
    if not key:
        return jsonify({'status': 'error', 'message': 'Nhập key!'})
    
    if not verify_key_checksum(key):
        return jsonify({'status': 'invalid', 'message': 'Key không hợp lệ!'})
    
    admin_keys = ["QANHNO1CRACKER", "DRAGONLOCUT"]
    if key in admin_keys:
        return jsonify({'status': 'success', 'message': 'Kích hoạt thành công!', 'expires': (datetime.now() + timedelta(days=365)).isoformat()})
    
    success, msg = use_key(key, fp)
    
    if success:
        update_stats('used')
        notify_key_used(key, ip, fp)
        return jsonify({'status': 'success', 'message': 'Key hợp lệ!'})
    else:
        return jsonify({'status': 'error', 'message': msg})

# ========== ADMIN ==========
def admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return app.make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin"'}))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_auth
def admin():
    stats = load_json_file(STATS_FILE, {'total_keys': 0, 'total_used': 0, 'total_users': 0})
    earnings = load_json_file(EARNINGS_FILE, {'total': 0})
    blacklist = load_json_file(BLACKLIST_FILE, {'ips': []})
    return render_template_string(ADMIN_HTML, stats=stats, earnings=earnings, blacklist=blacklist)

@app.route('/admin/create_key', methods=['POST'])
@admin_auth
def admin_create_key():
    key = generate_key()
    save_key(key, 720)
    send_telegram_message(f"👑 Admin tạo key mới!\n<code>{key}</code>")
    return redirect('/admin')

@app.route('/admin/blacklist', methods=['POST'])
@admin_auth
def admin_blacklist():
    ip = request.form.get('ip', '')
    if ip:
        add_to_blacklist(ip, '', 'Admin add')
    return redirect('/admin')

@app.route('/admin/unban')
@admin_auth
def admin_unban():
    ip = request.args.get('ip', '')
    if ip:
        blacklist = load_json_file(BLACKLIST_FILE, {'ips': []})
        if ip in blacklist['ips']:
            blacklist['ips'].remove(ip)
            save_json_file(BLACKLIST_FILE, blacklist)
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    return app.make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin"'}))

@app.route('/api/stats')
def api_stats():
    stats = load_json_file(STATS_FILE, {})
    earnings = load_json_file(EARNINGS_FILE, {})
    return jsonify({
        'total_keys': stats.get('total_keys', 0),
        'total_used': stats.get('total_used', 0),
        'total_users': stats.get('total_users', 0),
        'earnings_usd': earnings.get('total', 0)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)