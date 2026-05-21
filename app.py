from flask import Flask, request, jsonify, render_template_string, redirect, make_response, session
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
import uuid

# ========== CẤU HÌNH LOGGING ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== KHỞI TẠO FLASK ==========
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

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
RATE_LIMIT_MAX_REQUESTS = 30

# ========== FILE LƯU TRỮ ==========
KEYS_FILE = "keys.json"
TASKS_FILE = "user_tasks.json"
BLACKLIST_FILE = "blacklist.json"
RATE_LIMIT_FILE = "rate_limit.json"
STATS_FILE = "stats.json"
EARNINGS_FILE = "earnings.json"
LOGS_FILE = "logs.json"

# ========== HÀM ĐỌC/GHI FILE JSON ==========
def load_json_file(filename, default_value=None):
    if default_value is None:
        default_value = {}
    if not os.path.exists(filename):
        return default_value
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Lỗi đọc file {filename}: {str(e)}")
        return default_value

def save_json_file(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Lỗi ghi file {filename}: {str(e)}")
        return False

def append_log(action, details, level="INFO"):
    logs = load_json_file(LOGS_FILE, [])
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'ip': request.remote_addr if request else 'unknown',
        'details': details,
        'level': level
    })
    if len(logs) > 5000:
        logs = logs[-5000:]
    save_json_file(LOGS_FILE, logs)

# ========== HÀM TELEGRAM ==========
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message[:4000],
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Lỗi gửi Telegram: {str(e)}")
        return False

def notify_new_key(key, user_ip, user_fingerprint, session_id):
    send_telegram_message(f"""
🔑 <b>KEY MỚI ĐƯỢC TẠO!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>Fingerprint:</b> <code>{user_fingerprint[:24]}...</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)
    append_log('key_created', f'Key: {key}, IP: {user_ip}')

def notify_key_used(key, user_ip, user_fingerprint):
    send_telegram_message(f"""
✅ <b>KEY ĐÃ ĐƯỢC KÍCH HOẠT!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>Fingerprint:</b> <code>{user_fingerprint[:24]}...</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)
    append_log('key_used', f'Key: {key}, IP: {user_ip}')

def notify_new_user(ip, fingerprint, session_id):
    send_telegram_message(f"""
👤 <b>NGƯỜI DÙNG MỚI!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> <code>{fingerprint[:24]}...</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)
    append_log('new_user', f'IP: {ip}, Session: {session_id}')

def notify_completed_all_tasks(session_id, fingerprint, key):
    send_telegram_message(f"""
🎉 <b>HOÀN THÀNH TOÀN BỘ NHIỆM VỤ!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Session:</b> <code>{session_id[:16]}...</code>
🔑 <b>Key nhận được:</b> <code>{key}</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)

def notify_attack_detected(ip, fingerprint, attack_type):
    send_telegram_message(f"""
🚨 <b>CẢNH BÁO TẤN CÔNG!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> <code>{fingerprint[:24]}...</code>
⚔️ <b>Loại:</b> {attack_type}
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """)

# ========== HÀM KIẾM TIỀN ==========
def update_earnings(service_name, amount):
    earnings = load_json_file(EARNINGS_FILE, {})
    today = datetime.now().strftime('%Y-%m-%d')
    
    if 'daily' not in earnings:
        earnings['daily'] = {}
    if today not in earnings['daily']:
        earnings['daily'][today] = {}
    if service_name not in earnings['daily'][today]:
        earnings['daily'][today][service_name] = 0
    
    earnings['daily'][today][service_name] += amount
    earnings['total'] = earnings.get('total', 0) + amount
    earnings['last_updated'] = datetime.now().isoformat()
    
    save_json_file(EARNINGS_FILE, earnings)
    return earnings['total']

def get_total_earnings():
    earnings = load_json_file(EARNINGS_FILE, {})
    return earnings.get('total', 0)

def get_earnings_by_service():
    earnings = load_json_file(EARNINGS_FILE, {})
    result = {'vuotnhanh': 0, 'yeumoney': 0, 'link4m': 0}
    
    for date, services in earnings.get('daily', {}).items():
        for service, amount in services.items():
            if 'vuotnhanh' in service:
                result['vuotnhanh'] += amount
            elif 'yeumoney' in service:
                result['yeumoney'] += amount
            elif 'link4m' in service:
                result['link4m'] += amount
    
    return result

# ========== MÃ HÓA BẢO MẬT ==========
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
    except Exception as e:
        logger.error(f"Lỗi giải mã: {e}")
        return None

def generate_session_id():
    return secrets.token_hex(24)

# ========== SINH KEY ==========
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
    pattern = r'^DRP-[A-Z0-9]{6}-[A-Z0-9]{4}-([A-Z0-9]{2})$'
    match = re.match(pattern, key)
    if not match:
        return False
    provided = match.group(1)
    raw = key[:-3]
    expected = hashlib.md5(raw.encode()).hexdigest()[:2].upper()
    return hmac.compare_digest(provided, expected)

# ========== LẤY DẤU VÂN TAY ==========
def get_client_fingerprint():
    ua = request.headers.get('User-Agent', 'unknown')
    al = request.headers.get('Accept-Language', 'unknown')
    ip = request.remote_addr
    fingerprint_str = f"{ip}|{ua}|{al}"
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

# ========== RATE LIMITING ==========
def load_rate_limit_data():
    return load_json_file(RATE_LIMIT_FILE, {})

def save_rate_limit_data(data):
    save_json_file(RATE_LIMIT_FILE, data)

def check_rate_limit(action, identifier):
    now = time.time()
    rate_data = load_rate_limit_data()
    key = f"{action}:{identifier}"
    
    if key not in rate_data:
        rate_data[key] = {'count': 1, 'first_request': now}
        save_rate_limit_data(rate_data)
        return True
    
    record = rate_data[key]
    if now - record['first_request'] > RATE_LIMIT_WINDOW:
        record['count'] = 1
        record['first_request'] = now
        save_rate_limit_data(rate_data)
        return True
    
    if record['count'] >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    record['count'] += 1
    save_rate_limit_data(rate_data)
    return True

# ========== BLACKLIST ==========
def load_blacklist():
    return load_json_file(BLACKLIST_FILE, {'ips': [], 'fingerprints': []})

def save_blacklist(data):
    save_json_file(BLACKLIST_FILE, data)

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
    notify_attack_detected(ip, fingerprint, reason)

def remove_from_blacklist(ip=None, fingerprint=None):
    blacklist = load_blacklist()
    if ip and ip in blacklist['ips']:
        blacklist['ips'].remove(ip)
    if fingerprint and fingerprint in blacklist['fingerprints']:
        blacklist['fingerprints'].remove(fingerprint)
    save_blacklist(blacklist)

# ========== QUẢN LÝ KEY ==========
def load_keys():
    return load_json_file(KEYS_FILE, {})

def save_keys(data):
    save_json_file(KEYS_FILE, data)

def create_new_key(expires_hours=24, note=""):
    new_key = generate_dragon_key()
    keys = load_keys()
    keys[new_key] = {
        'expires_at': (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
        'used': False,
        'created_at': datetime.now().isoformat(),
        'note': note
    }
    save_keys(keys)
    
    stats = load_stats()
    stats['total_keys_generated'] = stats.get('total_keys_generated', 0) + 1
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in stats['daily_keys']:
        stats['daily_keys'][today] = 0
    stats['daily_keys'][today] += 1
    save_stats(stats)
    
    return new_key

def activate_key(key, fingerprint):
    keys = load_keys()
    if key not in keys:
        return False, "Key không tồn tại!"
    
    info = keys[key]
    expires_at = datetime.fromisoformat(info['expires_at'])
    
    if datetime.now() > expires_at:
        return False, "Key đã hết hạn!"
    
    if info.get('used', False):
        return False, "Key đã được sử dụng!"
    
    info['used'] = True
    info['used_at'] = datetime.now().isoformat()
    info['used_by'] = fingerprint
    save_keys(keys)
    
    stats = load_stats()
    stats['total_keys_used'] = stats.get('total_keys_used', 0) + 1
    save_stats(stats)
    
    return True, "Kích hoạt thành công!"

def get_all_keys(limit=100):
    keys = load_keys()
    result = []
    for key, info in list(keys.items())[-limit:]:
        info['key'] = key
        result.append(info)
    return result

def cleanup_expired_keys():
    keys = load_keys()
    expired = []
    for key, info in keys.items():
        if datetime.now() > datetime.fromisoformat(info['expires_at']):
            expired.append(key)
    for key in expired:
        del keys[key]
    if expired:
        save_keys(keys)
    return len(expired)

# ========== QUẢN LÝ TASK ==========
def load_user_tasks():
    return load_json_file(TASKS_FILE, {})

def save_user_tasks(data):
    save_json_file(TASKS_FILE, data)

def create_user_task(session_id, fingerprint, ip):
    tasks = load_user_tasks()
    
    step1_cb = f"{YOUR_DOMAIN}/api/cb/{session_id}/1"
    step2_cb = f"{YOUR_DOMAIN}/api/cb/{session_id}/2"
    step3_cb = f"{YOUR_DOMAIN}/api/cb/{session_id}/3"
    
    step1_url = create_vuotnhanh_link(step1_cb)
    step2_url = create_yeumoney_link(step2_cb)
    step3_url = create_link4m_link(step3_cb)
    
    tasks[session_id] = {
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
    save_user_tasks(tasks)
    return tasks[session_id]

def get_user_task(session_id):
    tasks = load_user_tasks()
    return tasks.get(session_id)

def update_task_step(session_id, step_num):
    tasks = load_user_tasks()
    if session_id not in tasks:
        return False, "Session không tồn tại!"
    
    task = tasks[session_id]
    field = f'step{step_num}_completed'
    
    if task.get(field, False):
        return False, "Bước đã hoàn thành!"
    
    task[field] = True
    task['step'] = step_num + 1
    save_user_tasks(tasks)
    
    if step_num == 1:
        update_earnings('vuotnhanh', 0.0005)
    elif step_num == 2:
        update_earnings('yeumoney', 0.001)
    elif step_num == 3:
        update_earnings('link4m', 0.002)
    
    return True, "Thành công"

def complete_final_step(session_id):
    tasks = load_user_tasks()
    if session_id not in tasks:
        return False, None, "Session không tồn tại!"
    
    task = tasks[session_id]
    if not task.get('step3_completed', False):
        return False, None, "Chưa hoàn thành bước 3!"
    
    if task.get('key'):
        return True, task['key'], "Key đã có!"
    
    new_key = create_new_key(24, f"Session {session_id}")
    task['key'] = new_key
    save_user_tasks(tasks)
    return True, new_key, "Thành công"

def cleanup_expired_tasks():
    tasks = load_user_tasks()
    expired = []
    for sid, task in tasks.items():
        if datetime.now() - datetime.fromisoformat(task['created_at']) > timedelta(hours=1):
            expired.append(sid)
    for sid in expired:
        del tasks[sid]
    if expired:
        save_user_tasks(tasks)
    return len(expired)

# ========== TẠO LINK NHIỆM VỤ ==========
def create_vuotnhanh_link(callback_url):
    try:
        encoded = urllib.parse.quote(callback_url, safe='')
        api = f"{VUOTNHANH_API_URL}?token={VUOTNHANH_API_KEY}&url={encoded}&format=json"
        resp = requests.get(api, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            short = data.get('shortenedUrl') or data.get('short_url') or data.get('url')
            if short:
                update_earnings('vuotnhanh_link', 0.001)
                return short
        return callback_url
    except:
        return callback_url

def create_yeumoney_link(callback_url):
    try:
        encoded = urllib.parse.quote(callback_url, safe='')
        api = f"{YEUMONEY_API_URL}?token={YEUMONEY_API_KEY}&url={encoded}&format=json"
        resp = requests.get(api, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            short = data.get('shortenedUrl') or data.get('shortUrl')
            if short:
                update_earnings('yeumoney_link', 0.002)
                return short
        return callback_url
    except:
        return callback_url

def create_link4m_link(callback_url):
    try:
        params = {'api': LINK4M_API_KEY, 'url': callback_url}
        resp = requests.get(LINK4M_API_URL, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success' and data.get('shortenedUrl'):
                update_earnings('link4m_link', 0.003)
                return data.get('shortenedUrl')
        return callback_url
    except:
        return callback_url

# ========== THỐNG KÊ ==========
def load_stats():
    return load_json_file(STATS_FILE, {
        'total_keys_generated': 0,
        'total_keys_used': 0,
        'total_users': 0,
        'daily_keys': {},
        'daily_users': {},
        'started_at': datetime.now().isoformat()
    })

def save_stats(data):
    data['last_updated'] = datetime.now().isoformat()
    save_json_file(STATS_FILE, data)

def update_stats(stat_type):
    stats = load_stats()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if stat_type == 'key_generated':
        stats['total_keys_generated'] += 1
        stats['daily_keys'][today] = stats['daily_keys'].get(today, 0) + 1
    elif stat_type == 'key_used':
        stats['total_keys_used'] += 1
    elif stat_type == 'new_user':
        stats['total_users'] += 1
        stats['daily_users'][today] = stats['daily_users'].get(today, 0) + 1
    
    save_stats(stats)

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
        .star{position:fixed;width:2px;height:2px;background:#fff;border-radius:50%;animation:shootingStar 4s linear infinite}
        @keyframes shootingStar{0%{transform:translateX(0) translateY(0);opacity:0}10%{opacity:1}30%{opacity:0}100%{transform:translateX(-200px) translateY(200px);opacity:0}}
        .hero{text-align:center;max-width:600px;animation:fadeInUp 0.8s}
        @keyframes fadeInUp{from{opacity:0;transform:translateY(50px)}to{opacity:1;transform:translateY(0)}}
        .badge{display:inline-block;background:rgba(176,0,255,0.15);backdrop-filter:blur(10px);padding:8px 24px;border-radius:100px;font-size:12px;font-weight:600;color:#b000ff;border:1px solid rgba(176,0,255,0.4);margin-bottom:30px;animation:pulse 2s infinite}
        @keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(176,0,255,0.4)}50%{box-shadow:0 0 0 15px rgba(176,0,255,0)}}
        h1{font-size:60px;font-weight:800;background:linear-gradient(135deg,#fff,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px;animation:gradientShift 4s ease infinite}
        @keyframes gradientShift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
        .sub{font-size:16px;color:#aaa;margin-bottom:30px;line-height:1.6}
        .btn{background:linear-gradient(135deg,#b000ff,#ff44ff);border:none;padding:16px 45px;font-size:16px;font-weight:600;color:#fff;border-radius:60px;display:inline-flex;align-items:center;gap:10px;text-decoration:none;box-shadow:0 5px 20px rgba(176,0,255,0.4);transition:0.3s}
        .btn:hover{transform:translateY(-5px) scale(1.05)}
        .stats{display:flex;justify-content:center;gap:40px;margin-top:50px;padding-top:30px;border-top:1px solid rgba(176,0,255,0.2)}
        .stat-number{font-size:28px;font-weight:700;background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent}
        .stat-label{font-size:12px;color:#888;margin-top:5px}
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
            <div><div class="stat-number">100%</div><div class="stat-label">Bảo mật</div></div>
        </div>
    </div>
    <script>for(let i=0;i<30;i++){let s=document.createElement('div');s.className='star';s.style.top=Math.random()*100+'%';s.style.left=Math.random()*100+'%';s.style.animationDelay=Math.random()*8+'s';document.body.appendChild(s)}</script>
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
        .card{max-width:550px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:32px;border:1px solid rgba(176,0,255,0.3);text-align:center;animation:fadeIn 0.6s}
        @keyframes fadeIn{from{opacity:0;transform:scale(0.9)}to{opacity:1;transform:scale(1)}}
        .step-badge{background:linear-gradient(135deg,#b000ff,#ff44ff);padding:8px 24px;border-radius:100px;font-size:13px;font-weight:700;color:#fff;display:inline-block;margin-bottom:24px}
        h2{font-size:28px;background:linear-gradient(135deg,#fff,#b000ff);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px}
        .desc{color:#aaa;margin-bottom:24px}
        .task-link{background:rgba(0,0,0,0.4);border-radius:16px;padding:16px;margin:24px 0;word-break:break-all}
        .task-link a{color:#b000ff;text-decoration:none}
        .btn-group{display:flex;gap:16px;margin-top:24px}
        .btn-continue{flex:1;background:linear-gradient(135deg,#00cc66,#00ff88);border:none;padding:12px;border-radius:16px;color:#fff;font-weight:600;cursor:pointer}
        .btn-back{flex:1;background:rgba(176,0,255,0.2);border:1px solid rgba(176,0,255,0.5);padding:12px;border-radius:16px;color:#b000ff;font-weight:600;text-decoration:none;display:inline-block;text-align:center}
        .loading{display:inline-block;width:18px;height:18px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.8s linear infinite}
        @keyframes spin{to{transform:rotate(360deg)}}
        .warning{font-size:12px;color:#64748b;margin-top:16px}
        .info{background:rgba(255,193,7,0.1);border:1px solid rgba(255,193,7,0.3);border-radius:12px;padding:10px;margin:10px 0;font-size:12px;color:#ffc107}
    </style>
</head>
<body>
    <div class="card">
        <div class="step-badge">📌 BƯỚC {{ step }}/3</div>
        <h2>{{ title }}</h2>
        <div class="desc">{{ desc }}</div>
        <div class="info">💰 Hoàn thành nhiệm vụ để nhận KEY MIỄN PHÍ!</div>
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
        async function check(){
            if(checking) return;
            checking=true;
            const btn=document.getElementById('continueBtn');
            const original=btn.innerHTML;
            btn.innerHTML='<span class="loading"></span> Đang kiểm tra...';
            btn.disabled=true;
            try{
                const res=await fetch(`/api/check/${sid}/${step}`);
                const data=await res.json();
                if(data.completed){
                    window.location.href=data.next;
                }else{
                    document.getElementById('warningMsg').innerHTML='⚠️ Bạn chưa hoàn thành nhiệm vụ!';
                    btn.innerHTML=original;
                    btn.disabled=false;
                    checking=false;
                    window.open(document.getElementById('taskLink').href,'_blank');
                }
            }catch(e){
                document.getElementById('warningMsg').innerHTML='⚠️ Lỗi, thử lại!';
                btn.innerHTML=original;
                btn.disabled=false;
                checking=false;
            }
        }
        window.open(document.getElementById('taskLink').href,'_blank');
        setInterval(()=>{if(!checking) check()},5000);
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
        .card{max-width:520px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:32px;text-align:center;border:1px solid rgba(176,0,255,0.4);animation:bounceIn 0.8s}
        @keyframes bounceIn{0%{opacity:0;transform:scale(0.7)}50%{transform:scale(1.05)}100%{transform:scale(1)}}
        .success-icon{width:80px;height:80px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;animation:pulseSuccess 1s infinite}
        @keyframes pulseSuccess{0%,100%{transform:scale(1);box-shadow:0 0 0 0 rgba(0,255,136,0.4)}50%{transform:scale(1.05);box-shadow:0 0 0 20px rgba(0,255,136,0)}}
        h2{font-size:32px;background:linear-gradient(135deg,#fff,#00ff88);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px}
        .key-box{background:linear-gradient(135deg,#0f172a,#1a1a2e);border-radius:20px;padding:24px;margin:24px 0;border:1px dashed #b000ff}
        .key-value{font-family:monospace;font-size:20px;font-weight:700;background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent;word-break:break-all;margin:12px 0;cursor:pointer}
        .copy-btn{background:linear-gradient(135deg,#b000ff,#ff44ff);border:none;padding:10px 28px;border-radius:32px;color:#fff;cursor:pointer;font-weight:600}
        .btn-back{display:inline-block;background:rgba(176,0,255,0.2);text-decoration:none;color:#b000ff;padding:10px 24px;border-radius:32px;margin-top:16px}
        .warning{font-size:12px;color:#64748b;margin:16px 0}
        .confetti{position:fixed;width:10px;height:10px;background:linear-gradient(135deg,#b000ff,#ff44ff);position:absolute;animation:fall 3s linear forwards;z-index:9999}
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
        <div class="warning">⏰ Key có hiệu lực trong 24 giờ<br>📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM</div>
        <a href="/" class="btn-back">🏠 Về trang chủ</a>
    </div>
    <script>
        for(let i=0;i<100;i++){let c=document.createElement('div');c.className='confetti';c.style.left=Math.random()*100+'%';c.style.animationDelay=Math.random()*2+'s';c.style.animationDuration=(2+Math.random()*2)+'s';document.body.appendChild(c);setTimeout(()=>c.remove(),3000)}
        function copyKey(){const k=document.getElementById('licenseKey').innerText;navigator.clipboard.writeText(k).then(()=>alert('✅ Đã sao chép key!\\nKey: '+k))}
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

CALLBACK_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thành công - DRAGON PINGX</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .card{max-width:500px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:40px;text-align:center;border:1px solid rgba(176,0,255,0.4);animation:fadeIn 0.5s}
        @keyframes fadeIn{from{opacity:0;transform:scale(0.9)}to{opacity:1;transform:scale(1)}}
        .success-icon{width:70px;height:70px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px}
        h2{font-size:28px;color:#00ff88;margin-bottom:10px}
        p{color:#aaa;margin-bottom:20px;line-height:1.6}
        .next-step{background:linear-gradient(135deg,#b000ff,#ff44ff);border:none;padding:12px 30px;border-radius:40px;color:#fff;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;margin-top:10px}
        .next-step:hover{transform:translateY(-2px);filter:brightness(1.05)}
        .key-display{background:rgba(0,0,0,0.4);border-radius:16px;padding:16px;margin:20px 0;word-break:break-all}
        .key-display code{font-size:18px;color:#b000ff}
        .warning{font-size:12px;color:#64748b;margin-top:20px}
        .confetti{position:fixed;width:8px;height:8px;background:linear-gradient(135deg,#b000ff,#ff44ff);position:absolute;animation:fall 2.5s linear forwards;z-index:9999}
        @keyframes fall{0%{transform:translateY(-100vh) rotate(0deg)}100%{transform:translateY(100vh) rotate(360deg);opacity:0}}
    </style>
</head>
<body>
    <div class="card">
        <div class="success-icon"><svg width="35" height="35" fill="none" stroke="white" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg></div>
        <h2>{% if key %}🎉 CHÚC MỪNG! 🎉{% else %}✅ THÀNH CÔNG!{% endif %}</h2>
        <p>{{ message }}</p>
        {% if key %}
        <div class="key-display">
            <code>{{ key }}</code>
        </div>
        <a href="/" class="next-step">🏠 Về trang chủ</a>
        {% elif next_step %}
        <a href="/step/{{ sid }}/{{ next_step }}" class="next-step">🚀 Tiếp tục bước {{ next_step }}</a>
        {% endif %}
        <div class="warning">🔒 Hệ thống bảo mật tuyệt đối - DRAGON PINGX PREMIUM</div>
    </div>
    <script>
        for(let i=0;i<80;i++){let c=document.createElement('div');c.className='confetti';c.style.left=Math.random()*100+'%';c.style.animationDelay=Math.random()*2+'s';document.body.appendChild(c);setTimeout(()=>c.remove(),2500)}
        setTimeout(()=>{window.close()},3000);
    </script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;padding:32px}
.container{max-width:1200px;margin:0 auto}.header{text-align:center;margin-bottom:32px}.header h1{background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px}
.stat-card{background:rgba(15,23,42,0.9);border-radius:16px;padding:20px;border:1px solid rgba(176,0,255,0.3)}.stat-card h3{color:#64748b;font-size:12px;margin-bottom:8px}
.stat-card .value{font-size:32px;font-weight:700;color:#b000ff}.section{background:rgba(15,23,42,0.9);border-radius:16px;padding:24px;margin-bottom:24px;border:1px solid rgba(176,0,255,0.3)}
.section h2{color:#fff;margin-bottom:16px;font-size:20px}.logout{position:fixed;top:16px;right:16px;background:rgba(239,68,68,0.2);color:#f87171;padding:8px 16px;border-radius:8px;text-decoration:none}
input{background:rgba(0,0,0,0.3);border:1px solid rgba(176,0,255,0.3);padding:10px;border-radius:8px;color:#fff;width:100%}
.btn{background:linear-gradient(135deg,#b000ff,#ff44ff);color:#fff;border:none;padding:10px 20px;border-radius:8px;cursor:pointer}
.btn-danger{background:linear-gradient(135deg,#ef4444,#dc2626)}.flex{display:flex;gap:16px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse}th,td{padding:12px;text-align:left;color:#cbd5e1;border-bottom:1px solid rgba(176,0,255,0.2)}th{color:#b000ff}
</style></head>
<body><a href="/admin/logout" class="logout">🚪 Đăng xuất</a><div class="container"><div class="header"><h1>🔐 DRAGON PINGX ADMIN</h1><p style="color:#64748b">Quản lý hệ thống key</p></div>
<div class="stats-grid"><div class="stat-card"><h3>📊 Tổng key</h3><div class="value">{{ stats.total_keys_generated }}</div></div><div class="stat-card"><h3>✅ Key đã dùng</h3><div class="value">{{ stats.total_keys_used }}</div></div><div class="stat-card"><h3>👥 Người dùng</h3><div class="value">{{ stats.total_users }}</div></div><div class="stat-card"><h3>💰 Thu nhập (USD)</h3><div class="value">${{ "%.4f"|format(earnings.total) }}</div></div></div>
<div class="section"><h2>💰 Thu nhập chi tiết</h2><table><th>Dịch vụ</th><th>USD</th></tr>
<tr><td>Vuotnhanh</td><td>${{ "%.4f"|format(earnings_by_service.vuotnhanh) }}</td></tr>
<tr><td>Yeumoney</td><td>${{ "%.4f"|format(earnings_by_service.yeumoney) }}</td></tr>
<tr><td>Link4M</td><td>${{ "%.4f"|format(earnings_by_service.link4m) }}</td></tr>
</table></div>
<div class="section"><h2>🔑 Tạo key mới</h2><form method="POST" action="/admin/create_key"><div class="flex"><input type="text" name="note" placeholder="Ghi chú"><button type="submit" class="btn">➕ Tạo key</button></div></form></div>
<div class="section"><h2>🚫 Blacklist IP</h2><form method="POST" action="/admin/blacklist"><div class="flex"><input type="text" name="ip" placeholder="IP cần chặn"><button type="submit" class="btn btn-danger">🚫 Thêm</button></div></form>
<table style="margin-top:16px"><tr><th>IP</th><th>Hành động</th></tr>{% for ip in blacklist.ips %}<tr><td>{{ ip }}</td><td><a href="/admin/unban?ip={{ ip }}" style="color:#f87171">Xóa</a></td></tr>{% endfor %}</table></div>
<div class="section"><h2>📋 Danh sách key gần đây</h2><table><tr><th>Key</th><th>Trạng thái</th><th>Hết hạn</th></tr>{% for k in keys %}<tr><td><code>{{ k.key }}</code></td><td>{% if k.used %}✅ Đã dùng{% else %}🟢 Còn hiệu lực{% endif %}</td><td>{{ k.expires_at[:16] }}</td></tr>{% endfor %}</table></div></div></body></html>
"""

# ========== ROUTES ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    fp = get_client_fingerprint()
    ip = request.remote_addr
    
    if is_blacklisted(ip, fp):
        return render_template_string(ERROR_HTML, msg="Truy cập bị chặn!")
    
    if not check_rate_limit('getkey', fp):
        add_to_blacklist(ip, fp, "Rate limit exceeded")
        return render_template_string(ERROR_HTML, msg="Quá nhiều yêu cầu! Thử lại sau 1 phút.")
    
    sid = generate_session_id()
    create_user_task(sid, fp, ip)
    update_stats('new_user')
    notify_new_user(ip, fp, sid)
    
    return redirect(f'/step/{sid}/1')

@app.route('/step/<sid>/<int:step>')
def step_page(sid, step):
    task = get_user_task(sid)
    fp = get_client_fingerprint()
    
    if not task:
        return render_template_string(ERROR_HTML, msg="Phiên không hợp lệ!")
    
    if task.get('fingerprint') != fp:
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!")
    
    config = {
        1: {'title': '🚀 Bước 1: Vuotnhanh', 'desc': 'Hoàn thành nhiệm vụ trên Vuotnhanh', 'url': task.get('step1_url', '#'), 'back': '/getkey'},
        2: {'title': '💰 Bước 2: Yeumoney', 'desc': 'Hoàn thành nhiệm vụ trên Yeumoney', 'url': task.get('step2_url', '#'), 'back': f'/step/{sid}/1'},
        3: {'title': '🔗 Bước 3: Link4M', 'desc': 'Hoàn thành nhiệm vụ cuối cùng', 'url': task.get('step3_url', '#'), 'back': f'/step/{sid}/2'}
    }
    
    cfg = config.get(step)
    if not cfg:
        return render_template_string(ERROR_HTML, msg="Bước không hợp lệ!")
    
    return render_template_string(STEP_HTML, step=step, title=cfg['title'], desc=cfg['desc'], url=cfg['url'], sid=sid, back_url=cfg['back'])

@app.route('/api/cb/<sid>/<int:step>')
def callback(sid, step):
    tasks = load_user_tasks()
    
    if sid not in tasks:
        return render_template_string(ERROR_HTML, msg="Session không hợp lệ!"), 404
    
    task = tasks[sid]
    fp = get_client_fingerprint()
    
    # Kiểm tra fingerprint (bảo mật)
    if task.get('fingerprint') != fp:
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!"), 403
    
    # Kiểm tra đã hoàn thành chưa
    field = f'step{step}_completed'
    if task.get(field, False):
        return render_template_string(CALLBACK_SUCCESS_HTML, 
            message=f"✅ Bước {step} đã được hoàn thành trước đó!",
            key=None, next_step=None, sid=None)
    
    # Xử lý theo từng bước
    if step == 1:
        task['step1_completed'] = True
        task['step'] = 2
        update_earnings('vuotnhanh', 0.0005)
        save_user_tasks(tasks)
        return render_template_string(CALLBACK_SUCCESS_HTML, 
            message="🎉 Chúc mừng! Bạn đã hoàn thành bước 1 thành công! Hãy tiếp tục bước 2.",
            key=None, next_step=2, sid=sid)
    
    elif step == 2:
        task['step2_completed'] = True
        task['step'] = 3
        update_earnings('yeumoney', 0.001)
        save_user_tasks(tasks)
        return render_template_string(CALLBACK_SUCCESS_HTML, 
            message="🎉 Chúc mừng! Bạn đã hoàn thành bước 2 thành công! Hãy tiếp tục bước cuối cùng.",
            key=None, next_step=3, sid=sid)
    
    elif step == 3:
        task['step3_completed'] = True
        new_key = create_new_key(24, f"Session {sid}")
        task['key'] = new_key
        save_user_tasks(tasks)
        
        update_stats('key_generated')
        notify_new_key(new_key, task.get('ip', 'unknown'), task.get('fingerprint', 'unknown'), sid)
        notify_completed_all_tasks(sid, task.get('fingerprint', 'unknown'), new_key)
        update_earnings('link4m', 0.002)
        
        return render_template_string(CALLBACK_SUCCESS_HTML, 
            message=f"🎉 CHÚC MỪNG! Bạn đã hoàn thành toàn bộ nhiệm vụ! Đây là key của bạn:",
            key=new_key, next_step=None, sid=None)
    
    else:
        return render_template_string(ERROR_HTML, msg="Bước không hợp lệ!")

@app.route('/api/check/<sid>/<int:step>')
def check_step(sid, step):
    task = get_user_task(sid)
    fp = get_client_fingerprint()
    
    if not task:
        return jsonify({'completed': False, 'error': 'Not found'})
    
    if task.get('fingerprint') != fp:
        return jsonify({'completed': False, 'error': 'Invalid'})
    
    completed = False
    next_url = None
    
    if step == 1 and task.get('step1_completed'):
        completed = True
        next_url = f'/step/{sid}/2'
    elif step == 2 and task.get('step2_completed'):
        completed = True
        next_url = f'/step/{sid}/3'
    elif step == 3 and task.get('step3_completed'):
        completed = True
        next_url = f'/final/{sid}'
    
    return jsonify({'completed': completed, 'next': next_url})

@app.route('/final/<sid>')
def final(sid):
    task = get_user_task(sid)
    fp = get_client_fingerprint()
    
    if not task:
        return render_template_string(ERROR_HTML, msg="Phiên không hợp lệ!")
    
    if task.get('fingerprint') != fp:
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!")
    
    key = task.get('key')
    if not key:
        return render_template_string(ERROR_HTML, msg="Chưa có key! Hoàn thành các bước trước.")
    
    return render_template_string(FINAL_HTML, key=key)

@app.route('/api/verify', methods=['POST'])
def verify():
    fp = get_client_fingerprint()
    ip = request.remote_addr
    
    if is_blacklisted(ip, fp):
        return jsonify({'status': 'error', 'message': 'Bị chặn'}), 403
    
    if not check_rate_limit('verify', fp):
        add_to_blacklist(ip, fp, "Verify rate limit")
        return jsonify({'status': 'error', 'message': 'Quá nhiều lần thử!'}), 429
    
    data = request.json
    key = data.get('key', '').strip().upper()
    
    if not key:
        return jsonify({'status': 'error', 'message': 'Nhập key!'})
    
    if not verify_key_checksum(key):
        return jsonify({'status': 'invalid', 'message': 'Key không hợp lệ!'})
    
    admin_keys = ["QANHNO1CRACKER", "DRAGONLOCUT"]
    if key in admin_keys:
        return jsonify({'status': 'success', 'message': 'Kích hoạt thành công!', 'expires': (datetime.now() + timedelta(days=365)).isoformat()})
    
    success, msg = activate_key(key, fp)
    
    if success:
        update_stats('key_used')
        notify_key_used(key, ip, fp)
        return jsonify({'status': 'success', 'message': 'Key hợp lệ!'})
    else:
        return jsonify({'status': 'error', 'message': msg})

@app.route('/api/stats')
def api_stats():
    stats = load_stats()
    earnings = load_json_file(EARNINGS_FILE, {})
    return jsonify({
        'total_keys': stats.get('total_keys_generated', 0),
        'total_used': stats.get('total_keys_used', 0),
        'total_users': stats.get('total_users', 0),
        'earnings_usd': earnings.get('total', 0)
    })

# ========== ADMIN ==========
def admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin"'}))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_auth
def admin():
    stats = load_stats()
    earnings = load_json_file(EARNINGS_FILE, {})
    earnings_by_service = get_earnings_by_service()
    blacklist = load_blacklist()
    keys = get_all_keys(50)
    return render_template_string(ADMIN_HTML, stats=stats, earnings=earnings, earnings_by_service=earnings_by_service, blacklist=blacklist, keys=keys)

@app.route('/admin/create_key', methods=['POST'])
@admin_auth
def admin_create_key():
    note = request.form.get('note', '')
    key = create_new_key(720, note)
    send_telegram_message(f"👑 Admin tạo key mới!\n<code>{key}</code>\n📝 {note}")
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
        remove_from_blacklist(ip=ip)
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    return make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin"'}))

# ========== CLEANUP SCHEDULER ==========
def schedule_cleanup():
    def cleanup():
        while True:
            time.sleep(3600)
            cleanup_expired_tasks()
            cleanup_expired_keys()
    thread = threading.Thread(target=cleanup, daemon=True)
    thread.start()

if __name__ != '__main__':
    schedule_cleanup()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    schedule_cleanup()
    logger.info(f"🚀 DRAGON PINGX PREMIUM chạy tại port {port}")
    logger.info(f"📍 Domain: {YOUR_DOMAIN}")
    app.run(host='0.0.0.0', port=port, debug=False)