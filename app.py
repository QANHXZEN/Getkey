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
SETTINGS_FILE = "settings.json"
LOGS_FILE = "logs.json"
REPORTS_FILE = "reports.json"

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
        logger.warning("Telegram chưa được cấu hình đầy đủ")
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
        if response.status_code == 200:
            logger.info("Đã gửi tin nhắn Telegram thành công")
            return True
        else:
            logger.error(f"Telegram lỗi: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Lỗi gửi Telegram: {str(e)}")
        return False

def notify_earning(service_name, amount, link_url, session_id, user_ip, user_fingerprint):
    """Thông báo khi có thu nhập từ link nhiệm vụ"""
    check_link = f"{YOUR_DOMAIN}/earning/{session_id}"
    
    message = f"""
💰 <b>BẠN ĐÃ KIẾM ĐƯỢC TIỀN!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 <b>Dịch vụ:</b> {service_name}
💵 <b>Số tiền:</b> ${amount:.4f} USD (≈ {amount * 25000:.0f} VNĐ)
🔗 <b>Link đã cộng tiền:</b>
<code>{link_url}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP người dùng:</b> {user_ip}
🆔 <b>Fingerprint:</b> <code>{user_fingerprint[:24]}...</code>
🆔 <b>Session ID:</b> <code>{session_id[:16]}...</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Xem chi tiết thu nhập:</b>
🔗 {check_link}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
    """
    send_telegram_message(message)
    append_log('earning', f'{service_name}: ${amount} - {link_url}', 'INFO')

def notify_new_key(key, user_ip, user_fingerprint, session_id):
    message = f"""
🔑 <b>KEY MỚI ĐƯỢC TẠO!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>Fingerprint:</b> <code>{user_fingerprint[:24]}...</code>
🆔 <b>Session:</b> <code>{session_id[:16]}...</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Key có hiệu lực 24 giờ
📱 Chỉ được kích hoạt trên 1 thiết bị
    """
    send_telegram_message(message)
    append_log('key_created', f'Key: {key}, IP: {user_ip}')

def notify_key_used(key, user_ip, user_fingerprint):
    message = f"""
✅ <b>KEY ĐÃ ĐƯỢC KÍCH HOẠT!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 <b>Key:</b> <code>{key}</code>
🌐 <b>IP:</b> {user_ip}
🆔 <b>Fingerprint:</b> <code>{user_fingerprint[:24]}...</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Chúc mừng người dùng mới!
    """
    send_telegram_message(message)
    append_log('key_used', f'Key: {key}, IP: {user_ip}')

def notify_new_user(ip, fingerprint, session_id):
    message = f"""
👤 <b>NGƯỜI DÙNG MỚI!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> <code>{fingerprint[:24]}...</code>
🆔 <b>Session:</b> <code>{session_id[:16]}...</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Đang bắt đầu quy trình lấy key
    """
    send_telegram_message(message)
    append_log('new_user', f'IP: {ip}, Session: {session_id}')

def notify_task_completed(session_id, step_num, fingerprint, ip):
    message = f"""
✅ <b>HOÀN THÀNH BƯỚC {step_num}/3!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Session:</b> <code>{session_id[:16]}...</code>
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> <code>{fingerprint[:24]}...</code>
📌 <b>Bước:</b> {step_num}/3
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Bạn đã kiếm được tiền từ nhiệm vụ này!
    """
    send_telegram_message(message)

def notify_completed_all_tasks(session_id, fingerprint, ip, key):
    message = f"""
🎉 <b>HOÀN THÀNH TOÀN BỘ NHIỆM VỤ!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Session:</b> <code>{session_id[:16]}...</code>
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> <code>{fingerprint[:24]}...</code>
🔑 <b>Key nhận được:</b> <code>{key}</code>
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Cảm ơn bạn đã hoàn thành nhiệm vụ!
    """
    send_telegram_message(message)
    append_log('all_tasks_completed', f'Session: {session_id}, Key: {key}')

def notify_attack_detected(ip, fingerprint, attack_type, details=""):
    message = f"""
🚨 <b>CẢNH BÁO TẤN CÔNG!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 <b>IP:</b> {ip}
🆔 <b>Fingerprint:</b> <code>{fingerprint[:24]}...</code>
⚔️ <b>Loại:</b> {attack_type}
📝 <b>Chi tiết:</b> {details}
⏰ <b>Thời gian:</b> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Đã tự động thêm vào blacklist!
    """
    send_telegram_message(message)
    append_log('attack_detected', f'IP: {ip}, Type: {attack_type}, Details: {details}', 'WARNING')

# ========== HÀM KIẾM TIỀN ==========
def update_earnings(service_name, amount, link_url, session_id, user_ip, user_fingerprint):
    """Cập nhật số tiền kiếm được và gửi thông báo Telegram"""
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
    
    # Lưu chi tiết từng giao dịch
    if 'transactions' not in earnings:
        earnings['transactions'] = []
    earnings['transactions'].append({
        'time': datetime.now().isoformat(),
        'service': service_name,
        'amount': amount,
        'link': link_url,
        'session_id': session_id,
        'ip': user_ip,
        'fingerprint': user_fingerprint[:24]
    })
    if len(earnings['transactions']) > 1000:
        earnings['transactions'] = earnings['transactions'][-1000:]
    
    save_json_file(EARNINGS_FILE, earnings)
    
    # Gửi thông báo Telegram
    notify_earning(service_name, amount, link_url, session_id, user_ip, user_fingerprint)
    
    logger.info(f"Kiếm được ${amount} từ {service_name} - Tổng: ${earnings['total']}")
    return earnings['total']

def get_total_earnings():
    earnings = load_json_file(EARNINGS_FILE, {})
    return earnings.get('total', 0)

def get_earnings_by_service():
    earnings = load_json_file(EARNINGS_FILE, {})
    result = {
        'vuotnhanh': 0,
        'yeumoney': 0,
        'link4m': 0,
        'vuotnhanh_completed': 0,
        'yeumoney_completed': 0,
        'link4m_completed': 0
    }
    
    for date, services in earnings.get('daily', {}).items():
        for service, amount in services.items():
            if service in result:
                result[service] += amount
            elif 'vuotnhanh' in service:
                result['vuotnhanh'] += amount
            elif 'yeumoney' in service:
                result['yeumoney'] += amount
            elif 'link4m' in service:
                result['link4m'] += amount
    
    return result

def get_daily_earnings():
    earnings = load_json_file(EARNINGS_FILE, {})
    daily = {}
    for date, services in earnings.get('daily', {}).items():
        total = sum(services.values())
        daily[date] = {'total': total, 'details': services}
    return daily

def get_transactions(limit=100):
    earnings = load_json_file(EARNINGS_FILE, {})
    transactions = earnings.get('transactions', [])
    return transactions[-limit:]

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

def generate_secure_token():
    return secrets.token_urlsafe(32)

def generate_session_id():
    return secrets.token_hex(24)

# ========== SINH KEY ==========
def generate_dragon_key():
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(secrets.choice(chars) for _ in range(6))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    raw_key = f"DRP-{part1}-{part2}"
    checksum = hashlib.md5(raw_key.encode()).hexdigest()[:2].upper()
    final_key = f"{raw_key}-{checksum}"
    logger.info(f"Đã tạo key mới: {final_key}")
    return final_key

def verify_key_checksum(key):
    if not key or len(key) < 15:
        return False
    pattern = r'^DRP-[A-Z0-9]{6}-[A-Z0-9]{4}-([A-Z0-9]{2})$'
    match = re.match(pattern, key)
    if not match:
        return False
    provided_checksum = match.group(1)
    raw_key = key[:-3]
    expected_checksum = hashlib.md5(raw_key.encode()).hexdigest()[:2].upper()
    return hmac.compare_digest(provided_checksum, expected_checksum)

# ========== LẤY DẤU VÂN TAY NGƯỜI DÙNG ==========
def get_client_fingerprint():
    user_agent = request.headers.get('User-Agent', 'unknown')
    accept_language = request.headers.get('Accept-Language', 'unknown')
    accept_encoding = request.headers.get('Accept-Encoding', 'unknown')
    sec_ch_ua = request.headers.get('Sec-CH-UA', 'unknown')
    ip = request.remote_addr
    fingerprint_str = f"{ip}|{user_agent}|{accept_language}|{accept_encoding}|{sec_ch_ua}"
    fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]
    return fingerprint

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
    return load_json_file(BLACKLIST_FILE, {'ips': [], 'fingerprints': [], 'reasons': {}})

def save_blacklist(data):
    save_json_file(BLACKLIST_FILE, data)

def is_blacklisted(ip, fingerprint):
    blacklist = load_blacklist()
    if ip in blacklist.get('ips', []):
        return True
    if fingerprint in blacklist.get('fingerprints', []):
        return True
    return False

def add_to_blacklist(ip, fingerprint, reason):
    blacklist = load_blacklist()
    
    if ip and ip not in blacklist['ips']:
        blacklist['ips'].append(ip)
        blacklist['reasons'][ip] = reason
    
    if fingerprint and fingerprint not in blacklist['fingerprints']:
        blacklist['fingerprints'].append(fingerprint)
        blacklist['reasons'][fingerprint] = reason
    
    save_blacklist(blacklist)
    logger.warning(f"Đã thêm vào blacklist: IP={ip}, FP={fingerprint[:16] if fingerprint else 'None'}..., Lý do={reason}")
    notify_attack_detected(ip, fingerprint, "Blacklist", reason)

def remove_from_blacklist(ip=None, fingerprint=None):
    blacklist = load_blacklist()
    
    if ip and ip in blacklist['ips']:
        blacklist['ips'].remove(ip)
        if ip in blacklist['reasons']:
            del blacklist['reasons'][ip]
    
    if fingerprint and fingerprint in blacklist['fingerprints']:
        blacklist['fingerprints'].remove(fingerprint)
        if fingerprint in blacklist['reasons']:
            del blacklist['reasons'][fingerprint]
    
    save_blacklist(blacklist)
    logger.info(f"Đã xóa khỏi blacklist: IP={ip}, FP={fingerprint[:16] if fingerprint else 'None'}")

# ========== QUẢN LÝ KEY ==========
def load_keys():
    data = load_json_file(KEYS_FILE, {})
    for key, value in data.items():
        if 'encrypted_data' in value:
            decrypted = simple_decrypt(value['encrypted_data'])
            if decrypted:
                try:
                    value['decrypted_data'] = json.loads(decrypted)
                except:
                    value['decrypted_data'] = decrypted
    return data

def save_keys(data):
    safe_data = {}
    for key, value in data.items():
        safe_value = value.copy()
        if 'decrypted_data' in safe_value:
            encrypted = simple_encrypt(json.dumps(safe_value['decrypted_data']))
            safe_value['encrypted_data'] = encrypted
            del safe_value['decrypted_data']
        safe_data[key] = safe_value
    save_json_file(KEYS_FILE, safe_data)

def create_new_key(expires_hours=24, note=""):
    new_key = generate_dragon_key()
    
    keys = load_keys()
    keys[new_key] = {
        'expires_at': (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
        'used': False,
        'created_at': datetime.now().isoformat(),
        'note': note,
        'decrypted_data': {
            'used_by': None,
            'used_at': None
        }
    }
    save_keys(keys)
    
    stats = load_stats()
    stats['total_keys_generated'] = stats.get('total_keys_generated', 0) + 1
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in stats['daily_keys']:
        stats['daily_keys'][today] = 0
    stats['daily_keys'][today] += 1
    save_stats(stats)
    
    logger.info(f"Đã tạo key mới: {new_key}, hết hạn sau {expires_hours} giờ")
    return new_key

def activate_key(key, fingerprint):
    keys = load_keys()
    
    if key not in keys:
        return False, "Key không tồn tại trong hệ thống!"
    
    info = keys[key]
    expires_at = datetime.fromisoformat(info['expires_at'])
    
    if datetime.now() > expires_at:
        return False, f"Key đã hết hạn từ {expires_at.strftime('%d/%m/%Y %H:%M')}!"
    
    if info.get('used', False):
        used_at = info.get('used_at', 'không rõ')
        return False, f"Key đã được sử dụng vào lúc {used_at}!"
    
    info['used'] = True
    info['used_at'] = datetime.now().isoformat()
    
    if 'decrypted_data' in info:
        info['decrypted_data']['used_by'] = fingerprint
        info['decrypted_data']['used_at'] = datetime.now().isoformat()
    
    save_keys(keys)
    
    stats = load_stats()
    stats['total_keys_used'] = stats.get('total_keys_used', 0) + 1
    save_stats(stats)
    
    logger.info(f"Key {key} đã được kích hoạt thành công bởi {fingerprint[:16]}...")
    return True, "Kích hoạt thành công!"

def get_key_info(key):
    keys = load_keys()
    if key not in keys:
        return None
    info = keys[key].copy()
    info['key'] = key
    return info

def get_all_keys(limit=100):
    keys = load_keys()
    result = []
    for key, info in list(keys.items())[-limit:]:
        key_info = info.copy()
        key_info['key'] = key
        result.append(key_info)
    return result

def cleanup_expired_keys():
    keys = load_keys()
    expired_keys = []
    
    for key, info in keys.items():
        expires_at = datetime.fromisoformat(info['expires_at'])
        if datetime.now() > expires_at:
            expired_keys.append(key)
    
    for key in expired_keys:
        del keys[key]
    
    if expired_keys:
        save_keys(keys)
        logger.info(f"Đã xóa {len(expired_keys)} key hết hạn")
    
    return len(expired_keys)

# ========== QUẢN LÝ TASK NHIỆM VỤ ==========
def load_user_tasks():
    data = load_json_file(TASKS_FILE, {})
    for sid, task in data.items():
        if task.get('encrypted') and task.get('encrypted_data'):
            decrypted = simple_decrypt(task['encrypted_data'])
            if decrypted:
                try:
                    decrypted_data = json.loads(decrypted)
                    for key, value in decrypted_data.items():
                        task[key] = value
                except:
                    pass
    return data

def save_user_tasks(data):
    safe_data = {}
    for sid, task in data.items():
        safe_task = task.copy()
        sensitive_fields = ['fingerprint', 'key', 'ip']
        encrypted_data = {}
        for field in sensitive_fields:
            if field in safe_task:
                encrypted_data[field] = safe_task[field]
                del safe_task[field]
        if encrypted_data:
            safe_task['encrypted'] = True
            safe_task['encrypted_data'] = simple_encrypt(json.dumps(encrypted_data))
        safe_data[sid] = safe_task
    save_json_file(TASKS_FILE, safe_data)

def create_user_task(session_id, fingerprint, ip):
    tasks = load_user_tasks()
    
    # Tạo callback URLs
    step1_callback = f"{YOUR_DOMAIN}/api/callback/{session_id}/1"
    step2_callback = f"{YOUR_DOMAIN}/api/callback/{session_id}/2"
    step3_callback = f"{YOUR_DOMAIN}/api/callback/{session_id}/3"
    
    # Tạo link rút gọn
    step1_url = create_vuotnhanh_link(step1_callback)
    step2_url = create_yeumoney_link(step2_callback)
    step3_url = create_link4m_link(step3_callback)
    
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
        'attempts': 0,
        'last_activity': datetime.now().isoformat()
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
        return False, "Bước này đã được hoàn thành trước đó!"
    
    task[field] = True
    task['step'] = step_num + 1
    task['last_activity'] = datetime.now().isoformat()
    task['attempts'] = task.get('attempts', 0) + 1
    
    save_user_tasks(tasks)
    
    # Gửi thông báo
    notify_task_completed(session_id, step_num, task.get('fingerprint', 'unknown'), task.get('ip', 'unknown'))
    
    # Cập nhật thu nhập
    if step_num == 1:
        update_earnings('vuotnhanh_completed', 0.0005, task.get('step1_url', ''), session_id, task.get('ip', 'unknown'), task.get('fingerprint', 'unknown'))
    elif step_num == 2:
        update_earnings('yeumoney_completed', 0.001, task.get('step2_url', ''), session_id, task.get('ip', 'unknown'), task.get('fingerprint', 'unknown'))
    elif step_num == 3:
        update_earnings('link4m_completed', 0.002, task.get('step3_url', ''), session_id, task.get('ip', 'unknown'), task.get('fingerprint', 'unknown'))
    
    # Cập nhật thống kê
    stats = load_stats()
    stats['total_tasks_completed'] = stats.get('total_tasks_completed', 0) + 1
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in stats['daily_tasks']:
        stats['daily_tasks'][today] = 0
    stats['daily_tasks'][today] += 1
    save_stats(stats)
    
    return True, "Thành công"

def complete_final_step(session_id):
    tasks = load_user_tasks()
    
    if session_id not in tasks:
        return False, None, "Session không tồn tại!"
    
    task = tasks[session_id]
    
    if not task.get('step3_completed', False):
        return False, None, "Chưa hoàn thành bước 3!"
    
    if task.get('key'):
        return True, task['key'], "Key đã được tạo trước đó!"
    
    new_key = create_new_key(24, f"Tự động từ session {session_id}")
    
    task['key'] = new_key
    task['key_created_at'] = datetime.now().isoformat()
    save_user_tasks(tasks)
    
    notify_completed_all_tasks(session_id, task.get('fingerprint', 'unknown'), task.get('ip', 'unknown'), new_key)
    
    return True, new_key, "Thành công!"

def cleanup_expired_tasks():
    tasks = load_user_tasks()
    expired_sessions = []
    now = datetime.now()
    
    for sid, task in tasks.items():
        created_at = datetime.fromisoformat(task['created_at'])
        if now - created_at > timedelta(hours=1):
            expired_sessions.append(sid)
    
    for sid in expired_sessions:
        del tasks[sid]
    
    if expired_sessions:
        save_user_tasks(tasks)
        logger.info(f"Đã xóa {len(expired_sessions)} task hết hạn")
    
    return len(expired_sessions)

# ========== TẠO LINK NHIỆM VỤ ==========
def create_vuotnhanh_link(callback_url):
    try:
        encoded_url = urllib.parse.quote(callback_url, safe='')
        api_url = f"{VUOTNHANH_API_URL}?token={VUOTNHANH_API_KEY}&url={encoded_url}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            short_url = data.get('shortenedUrl') or data.get('short_url') or data.get('url') or callback_url
            logger.info(f"Đã tạo link Vuotnhanh: {short_url}")
            return short_url
        logger.warning(f"Vuotnhanh API trả về status {response.status_code}")
        return callback_url
    except Exception as e:
        logger.error(f"Lỗi tạo link Vuotnhanh: {e}")
        return callback_url

def create_yeumoney_link(callback_url):
    try:
        encoded_url = urllib.parse.quote(callback_url, safe='')
        api_url = f"{YEUMONEY_API_URL}?token={YEUMONEY_API_KEY}&url={encoded_url}&format=json"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            short_url = data.get('shortenedUrl') or data.get('shortUrl') or callback_url
            logger.info(f"Đã tạo link Yeumoney: {short_url}")
            return short_url
        logger.warning(f"Yeumoney API trả về status {response.status_code}")
        return callback_url
    except Exception as e:
        logger.error(f"Lỗi tạo link Yeumoney: {e}")
        return callback_url

def create_link4m_link(callback_url):
    try:
        params = {'api': LINK4M_API_KEY, 'url': callback_url}
        response = requests.get(LINK4M_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success' and result.get('shortenedUrl'):
                logger.info(f"Đã tạo link Link4M: {result.get('shortenedUrl')}")
                return result.get('shortenedUrl')
        logger.warning(f"Link4M API trả về status {response.status_code}")
        return callback_url
    except Exception as e:
        logger.error(f"Lỗi tạo link Link4M: {e}")
        return callback_url

# ========== THỐNG KÊ ==========
def load_stats():
    return load_json_file(STATS_FILE, {
        'total_keys_generated': 0,
        'total_keys_used': 0,
        'total_users': 0,
        'total_tasks_completed': 0,
        'daily_keys': {},
        'daily_users': {},
        'daily_tasks': {},
        'started_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    })

def save_stats(data):
    data['last_updated'] = datetime.now().isoformat()
    save_json_file(STATS_FILE, data)

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
    elif stat_type == 'task_completed':
        stats['total_tasks_completed'] += 1
        if today not in stats['daily_tasks']:
            stats['daily_tasks'][today] = 0
        stats['daily_tasks'][today] += 1
    
    save_stats(stats)

# ========== HTML TEMPLATES ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>DRAGON PINGX PREMIUM | Hệ Thống Kích Hoạt Chính Thức</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
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
        
        /* Hiệu ứng sao băng */
        .star {
            position: fixed;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            opacity: 0;
            animation: shootingStar 4s linear infinite;
            z-index: 1;
        }
        
        @keyframes shootingStar {
            0% {
                transform: translateX(0) translateY(0);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            20% {
                opacity: 1;
            }
            30% {
                opacity: 0;
            }
            100% {
                transform: translateX(-200px) translateY(200px);
                opacity: 0;
            }
        }
        
        /* Hiệu ứng hạt ma thuật */
        .magic-particle {
            position: fixed;
            width: 4px;
            height: 4px;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border-radius: 50%;
            opacity: 0;
            animation: floatMagic 6s infinite;
            z-index: 1;
        }
        
        @keyframes floatMagic {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            20% {
                opacity: 0.8;
            }
            80% {
                opacity: 0.6;
            }
            100% {
                transform: translateY(-100px) rotate(360deg);
                opacity: 0;
            }
        }
        
        /* Hiệu ứng đèn nền */
        .glow {
            position: fixed;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(176,0,255,0.15) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1;
            transition: all 0.3s ease;
        }
        
        .hero {
            text-align: center;
            max-width: 600px;
            animation: fadeInUp 0.8s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            position: relative;
            z-index: 2;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(50px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
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
            animation: pulse 2s infinite, borderGlow 3s infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(176,0,255,0.4);
                transform: scale(1);
            }
            50% {
                box-shadow: 0 0 0 15px rgba(176,0,255,0);
                transform: scale(1.02);
            }
        }
        
        @keyframes borderGlow {
            0%, 100% {
                border-color: rgba(176,0,255,0.4);
            }
            50% {
                border-color: rgba(176,0,255,1);
            }
        }
        
        h1 {
            font-size: 3.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #b000ff, #ff44ff, #b000ff);
            background-size: 300% 300%;
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 0.5rem;
            animation: gradientShift 4s ease infinite, textGlow 2s ease-in-out infinite;
        }
        
        @keyframes gradientShift {
            0% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
            100% {
                background-position: 0% 50%;
            }
        }
        
        @keyframes textGlow {
            0%, 100% {
                filter: drop-shadow(0 0 5px rgba(176,0,255,0.3));
            }
            50% {
                filter: drop-shadow(0 0 20px rgba(176,0,255,0.6));
            }
        }
        
        .sub {
            font-size: 1.1rem;
            color: #aaa;
            margin-bottom: 2rem;
            line-height: 1.6;
            animation: fadeInUp 0.8s 0.2s backwards;
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
            transition: all 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            display: inline-flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            box-shadow: 0 5px 20px rgba(176,0,255,0.4);
            animation: fadeInUp 0.8s 0.4s backwards;
            position: relative;
            overflow: hidden;
        }
        
        .btn-primary::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn-primary:hover::before {
            width: 300px;
            height: 300px;
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
            animation: fadeInUp 0.8s 0.6s backwards;
        }
        
        .stat-item {
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            animation: countUp 1s ease-out;
        }
        
        @keyframes countUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: #888;
            margin-top: 0.3rem;
        }
        
        /* Hiệu ứng loading cho trang */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #0a0a0a;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeOut 1s ease 1s forwards;
        }
        
        @keyframes fadeOut {
            to {
                opacity: 0;
                visibility: hidden;
            }
        }
        
        .loader {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(176,0,255,0.3);
            border-top-color: #b000ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
        
        @media (max-width: 480px) {
            h1 {
                font-size: 2.5rem;
            }
            .stats {
                gap: 1.5rem;
            }
            .stat-number {
                font-size: 1.3rem;
            }
            .btn-primary {
                padding: 0.8rem 1.8rem;
                font-size: 0.9rem;
            }
        }
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loader"></div>
    </div>
    
    <div id="glow1" class="glow" style="top: -100px; left: -100px;"></div>
    <div id="glow2" class="glow" style="bottom: -100px; right: -100px;"></div>
    
    <div class="hero">
        <div class="badge">✨ DRAGON PINGX PREMIUM | CHÍNH THỨC ✨</div>
        <h1>DRAGON PINGX</h1>
        <div class="sub">⚡ Hệ thống kích hoạt bản quyền tự động ⚡<br>🔒 Bảo mật tuyệt đối - 🚀 Tốc độ thần tốc - 👑 Uy tín hàng đầu</div>
        <a href="/getkey" class="btn-primary">
            🎁 NHẬN KEY MIỄN PHÍ
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7m0 0l-7 7m7-7H3"/>
            </svg>
        </a>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number" data-target="24">0</div>
                <div class="stat-label">Hỗ trợ 24/7</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" data-target="2500">0</div>
                <div class="stat-label">Người dùng</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" data-target="100">0</div>
                <div class="stat-label">Bảo mật</div>
            </div>
        </div>
    </div>
    
    <script>
        // Tạo hiệu ứng sao băng và hạt ma thuật
        for(let i = 0; i < 30; i++) {
            let star = document.createElement('div');
            star.className = 'star';
            star.style.top = Math.random() * 100 + '%';
            star.style.left = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 8 + 's';
            star.style.animationDuration = (3 + Math.random() * 3) + 's';
            document.body.appendChild(star);
        }
        
        for(let i = 0; i < 40; i++) {
            let particle = document.createElement('div');
            particle.className = 'magic-particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 8 + 's';
            particle.style.animationDuration = (5 + Math.random() * 5) + 's';
            document.body.appendChild(particle);
        }
        
        // Hiệu ứng đuổi chuột
        document.addEventListener('mousemove', function(e) {
            const glow1 = document.getElementById('glow1');
            const glow2 = document.getElementById('glow2');
            if(glow1) glow1.style.transform = `translate(${e.clientX * 0.05}px, ${e.clientY * 0.05}px)`;
            if(glow2) glow2.style.transform = `translate(${-e.clientX * 0.03}px, ${-e.clientY * 0.03}px)`;
        });
        
        // Count up animation
        function animateNumber(element, target) {
            let current = 0;
            let increment = target / 50;
            let timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    element.textContent = target + (target === 2500 ? '+' : (target === 100 ? '%' : ''));
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(current) + (target === 2500 ? '+' : (target === 100 ? '%' : ''));
                }
            }, 30);
        }
        
        setTimeout(() => {
            document.querySelectorAll('.stat-number').forEach(el => {
                let target = parseInt(el.dataset.target);
                animateNumber(el, target);
            });
        }, 500);
        
        // Ẩn loading sau 1.5s
        setTimeout(() => {
            const loading = document.getElementById('loadingOverlay');
            if(loading) loading.style.display = 'none';
        }, 1500);
    </script>
</body>
</html>
"""

STEP_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Bước {{ step_index }} - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            position: relative;
            overflow-x: hidden;
        }
        
        /* Hiệu ứng nền động */
        .bg-effect {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0;
        }
        
        .bg-circle {
            position: absolute;
            border-radius: 50%;
            background: rgba(176,0,255,0.05);
            animation: float 20s infinite;
        }
        
        @keyframes float {
            0%, 100% {
                transform: translateY(0) rotate(0deg);
            }
            50% {
                transform: translateY(-50px) rotate(180deg);
            }
        }
        
        .card {
            position: relative;
            z-index: 2;
            max-width: 550px;
            width: 100%;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            border: 1px solid rgba(176, 0, 255, 0.3);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 30px rgba(176,0,255,0.1);
            animation: cardGlow 3s infinite, fadeInScale 0.6s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        }
        
        @keyframes cardGlow {
            0%, 100% {
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 20px rgba(176,0,255,0.1);
            }
            50% {
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 40px rgba(176,0,255,0.3);
            }
        }
        
        @keyframes fadeInScale {
            from {
                opacity: 0;
                transform: scale(0.9);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .step-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border-radius: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            animation: rotate3D 4s ease-in-out infinite, pulseGlow 2s infinite;
        }
        
        @keyframes rotate3D {
            0% {
                transform: rotateY(0deg);
            }
            50% {
                transform: rotateY(180deg);
            }
            100% {
                transform: rotateY(360deg);
            }
        }
        
        @keyframes pulseGlow {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(176,0,255,0.4);
            }
            50% {
                box-shadow: 0 0 0 15px rgba(176,0,255,0);
            }
        }
        
        h2 {
            color: white;
            text-align: center;
            margin-bottom: 0.5rem;
            font-size: 1.8rem;
            background: linear-gradient(135deg, #fff, #b000ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            animation: textShine 3s infinite;
        }
        
        @keyframes textShine {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.8;
                letter-spacing: 1px;
            }
        }
        
        .step-badge {
            display: inline-block;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            padding: 0.3rem 1rem;
            border-radius: 100px;
            font-size: 0.7rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
        }
        
        .desc {
            color: #aaa;
            text-align: center;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }
        
        .info-box {
            background: rgba(0,0,0,0.4);
            border-radius: 1.2rem;
            padding: 1.2rem;
            margin: 1.5rem 0;
            border: 1px solid rgba(176,0,255,0.2);
            animation: slideInLeft 0.5s 0.2s backwards;
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .info-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: #b000ff;
            font-size: 0.85rem;
            margin-bottom: 0.8rem;
            animation: fadeInItem 0.3s backwards;
        }
        
        .info-item:nth-child(1) { animation-delay: 0.3s; }
        .info-item:nth-child(2) { animation-delay: 0.4s; }
        .info-item:nth-child(3) { animation-delay: 0.5s; }
        .info-item:nth-child(4) { animation-delay: 0.6s; }
        
        @keyframes fadeInItem {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .task-link {
            background: rgba(0,0,0,0.3);
            border-radius: 1rem;
            padding: 1rem;
            margin: 1rem 0;
            word-break: break-all;
            border: 1px dashed rgba(176,0,255,0.3);
            transition: all 0.3s ease;
        }
        
        .task-link:hover {
            border-color: rgba(176,0,255,0.8);
            background: rgba(176,0,255,0.05);
        }
        
        .task-link a {
            color: #b000ff;
            text-decoration: none;
            font-size: 0.85rem;
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
            transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            position: relative;
            overflow: hidden;
        }
        
        .btn-continue::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn-continue:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .btn-continue:hover {
            transform: translateY(-3px);
            filter: brightness(1.05);
            box-shadow: 0 10px 30px rgba(0,255,136,0.3);
        }
        
        .btn-continue:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
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
        
        .btn-back:hover {
            background: rgba(176,0,255,0.4);
            transform: translateY(-2px);
        }
        
        .loading-spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .warning {
            font-size: 0.75rem;
            color: #f87171;
            margin-top: 1rem;
            padding: 0.5rem;
            background: rgba(239,68,68,0.1);
            border-radius: 0.5rem;
            display: none;
        }
        
        .warning.show {
            display: block;
            animation: shake 0.5s ease;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        
        .success-badge {
            display: inline-block;
            background: rgba(0,255,136,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            color: #00ff88;
            margin-bottom: 10px;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .footer-note {
            margin-top: 1.5rem;
            text-align: center;
            font-size: 0.7rem;
            color: #475569;
            animation: fadeInUp 0.5s 1s backwards;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @media (max-width: 480px) {
            .card {
                padding: 1.5rem;
            }
            h2 {
                font-size: 1.4rem;
            }
            .step-icon {
                width: 60px;
                height: 60px;
            }
            .step-icon svg {
                width: 30px;
                height: 30px;
            }
            .btn-group {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="bg-effect" id="bgEffect"></div>
    
    <div class="card">
        <div class="step-icon">
            <svg width="40" height="40" fill="none" stroke="white" viewBox="0 0 24 24">
                {% if step_index == 1 %}
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                {% elif step_index == 2 %}
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                {% else %}
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                {% endif %}
            </svg>
        </div>
        
        <h2>{{ step_title }}</h2>
        <div class="step-badge">📌 BƯỚC {{ step_index }}/{{ total_steps }}</div>
        <div class="desc">{{ step_desc }}</div>
        
        <div class="info-box">
            <div class="info-item">💰 Kiếm tiền thụ động từ link nhiệm vụ</div>
            <div class="info-item">🔐 Key có hiệu lực 24 giờ sau khi nhận</div>
            <div class="info-item">⚡ Hoàn thành nhanh trong 2-3 phút</div>
            <div class="info-item">🎁 Hỗ trợ 24/7 từ đội ngũ</div>
        </div>
        
        <div class="task-link">
            <div style="font-size:0.7rem; color:#64748b; margin-bottom:5px;">🔗 Bấm vào link để làm nhiệm vụ:</div>
            <a href="{{ task_url }}" target="_blank" id="taskLink">{{ task_url }}</a>
        </div>
        
        <div class="btn-group">
            <a href="{{ back_url }}" class="btn-back">🔙 Quay lại</a>
            <button class="btn-continue" onclick="checkComplete()" id="continueBtn">
                {% if step_index == total_steps %}
                🎁 NHẬN KEY NGAY
                {% else %}
                ✅ TIẾP TỤC
                {% endif %}
            </button>
        </div>
        
        <div class="warning" id="warningMsg">
            ⚠️ Bạn chưa hoàn thành nhiệm vụ. Vui lòng hoàn thành và thử lại!
        </div>
        
        <div class="footer-note">
            💜 DRAGON PINGX PREMIUM - Bảo mật tuyệt đối 💜
        </div>
    </div>
    
    <script>
        // Tạo hiệu ứng nền động
        for(let i = 0; i < 15; i++) {
            let circle = document.createElement('div');
            circle.className = 'bg-circle';
            let size = 100 + Math.random() * 200;
            circle.style.width = size + 'px';
            circle.style.height = size + 'px';
            circle.style.left = Math.random() * 100 + '%';
            circle.style.top = Math.random() * 100 + '%';
            circle.style.animationDelay = Math.random() * 20 + 's';
            circle.style.animationDuration = (15 + Math.random() * 10) + 's';
            document.getElementById('bgEffect').appendChild(circle);
        }
        
        let sessionId = "{{ session_id }}";
        let step = {{ step_index }};
        let checking = false;
        let checkInterval = null;
        
        async function checkComplete() {
            if (checking) return;
            checking = true;
            
            const btn = document.getElementById('continueBtn');
            const originalText = btn.innerHTML;
            const warningMsg = document.getElementById('warningMsg');
            
            btn.innerHTML = '<span class="loading-spinner"></span> Đang kiểm tra...';
            btn.disabled = true;
            warningMsg.classList.remove('show');
            
            try {
                const response = await fetch(`/api/check_step/${sessionId}/${step}`);
                const data = await response.json();
                
                if (data.completed) {
                    window.location.href = data.next_url;
                } else {
                    warningMsg.classList.add('show');
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    checking = false;
                    
                    // Mở lại link nhiệm vụ
                    window.open(document.getElementById('taskLink').href, '_blank');
                }
            } catch (error) {
                console.error('Lỗi:', error);
                warningMsg.innerHTML = '⚠️ Có lỗi xảy ra, vui lòng thử lại sau!';
                warningMsg.classList.add('show');
                btn.innerHTML = originalText;
                btn.disabled = false;
                checking = false;
            }
        }
        
        // Tự động mở link nhiệm vụ
        window.open(document.getElementById('taskLink').href, '_blank');
        
        // Tự động kiểm tra mỗi 5 giây
        setInterval(() => {
            if (!checking && !window.location.pathname.includes('/final')) {
                checkComplete();
            }
        }, 5000);
    </script>
</body>
</html>
"""

FINAL_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Thành Công - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            position: relative;
            overflow: hidden;
        }
        
        /* Hiệu ứng confetti */
        .confetti {
            position: fixed;
            width: 10px;
            height: 10px;
            position: absolute;
            animation: confettiFall 3s linear forwards;
            z-index: 9999;
            pointer-events: none;
        }
        
        @keyframes confettiFall {
            0% {
                transform: translateY(-100vh) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(360deg);
                opacity: 0;
            }
        }
        
        /* Hiệu ứng sparkle */
        .sparkle {
            position: fixed;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9998;
        }
        
        .sparkle-star {
            position: absolute;
            font-size: 20px;
            animation: sparkleFade 1s forwards;
        }
        
        @keyframes sparkleFade {
            0% {
                opacity: 1;
                transform: scale(1);
            }
            100% {
                opacity: 0;
                transform: scale(1.5);
            }
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
            animation: bounceIn 0.8s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            z-index: 2;
            position: relative;
        }
        
        @keyframes bounceIn {
            0% {
                opacity: 0;
                transform: scale(0.7);
            }
            50% {
                opacity: 1;
                transform: scale(1.05);
            }
            100% {
                transform: scale(1);
            }
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
            animation: pulseSuccess 1s infinite, rotateIcon 0.5s ease;
        }
        
        @keyframes pulseSuccess {
            0%, 100% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(0,255,136,0.4);
            }
            50% {
                transform: scale(1.05);
                box-shadow: 0 0 0 20px rgba(0,255,136,0);
            }
        }
        
        @keyframes rotateIcon {
            0% {
                transform: rotate(0deg);
            }
            100% {
                transform: rotate(360deg);
            }
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
        
        .desc {
            color: #aaa;
            margin-bottom: 1.5rem;
        }
        
        .key-box {
            background: linear-gradient(135deg, #0f172a, #1a1a2e);
            border-radius: 1.2rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px dashed #b000ff;
            animation: glowPulse 2s infinite;
            transition: all 0.3s ease;
        }
        
        .key-box:hover {
            border-color: #ff44ff;
            box-shadow: 0 0 20px rgba(176,0,255,0.3);
        }
        
        @keyframes glowPulse {
            0%, 100% {
                box-shadow: 0 0 0 0 rgba(176,0,255,0.2);
                border-color: #b000ff;
            }
            50% {
                box-shadow: 0 0 20px 0 rgba(176,0,255,0.4);
                border-color: #ff44ff;
            }
        }
        
        .key-label {
            font-size: 0.7rem;
            color: #b000ff;
            text-transform: uppercase;
            letter-spacing: 3px;
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
            letter-spacing: 2px;
            cursor: pointer;
            padding: 10px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .key-value:hover {
            background: rgba(176,0,255,0.2);
            transform: scale(1.02);
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
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .copy-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .copy-btn:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .copy-btn:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 10px 20px rgba(176,0,255,0.4);
        }
        
        .warning {
            font-size: 0.7rem;
            color: #64748b;
            margin: 1rem 0;
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
            transition: all 0.3s ease;
        }
        
        .btn-back:hover {
            background: rgba(176,0,255,0.4);
            transform: translateY(-2px);
        }
        
        .flex-center {
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        @media (max-width: 480px) {
            .card {
                padding: 1.5rem;
            }
            h2 {
                font-size: 1.5rem;
            }
            .key-value {
                font-size: 0.9rem;
            }
            .success-icon {
                width: 60px;
                height: 60px;
            }
            .success-icon svg {
                width: 30px;
                height: 30px;
            }
        }
    </style>
</head>
<body>
    <div class="sparkle" id="sparkle"></div>
    
    <div class="card">
        <div class="success-icon">
            <svg width="48" height="48" fill="none" stroke="white" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
        </div>
        
        <h2>🎉 THÀNH CÔNG! 🎉</h2>
        <div class="desc">Bạn đã hoàn thành nhiệm vụ thành công</div>
        
        <div class="key-box">
            <div class="key-label">🔑 KEY KÍCH HOẠT CỦA BẠN</div>
            <div class="key-value" id="licenseKey" onclick="copyKey()">{{ key }}</div>
            <div class="flex-center">
                <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
            </div>
        </div>
        
        <div class="warning">
            ⏰ Key có hiệu lực trong 24 giờ<br>
            📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM để kích hoạt<br>
            🔒 Mỗi key chỉ dùng được 1 lần duy nhất
        </div>
        
        <a href="/" class="btn-back">🏠 Về trang chủ</a>
    </div>
    
    <script>
        // Tạo hiệu ứng confetti màu sắc
        const colors = ['#b000ff', '#ff44ff', '#00ff88', '#ffaa00', '#00ccff', '#ff6600'];
        
        function createConfetti() {
            for(let i = 0; i < 150; i++) {
                let confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + '%';
                confetti.style.top = '-10px';
                confetti.style.animationDelay = Math.random() * 2 + 's';
                confetti.style.animationDuration = (2 + Math.random() * 3) + 's';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.width = (5 + Math.random() * 10) + 'px';
                confetti.style.height = (5 + Math.random() * 10) + 'px';
                document.body.appendChild(confetti);
                setTimeout(() => confetti.remove(), 5000);
            }
        }
        
        // Tạo hiệu ứng lấp lánh
        function createSparkle() {
            const sparkleDiv = document.getElementById('sparkle');
            for(let i = 0; i < 50; i++) {
                let star = document.createElement('div');
                star.innerHTML = ['✨', '⭐', '🌟', '💫', '⚡'][Math.floor(Math.random() * 5)];
                star.className = 'sparkle-star';
                star.style.left = Math.random() * 100 + '%';
                star.style.top = Math.random() * 100 + '%';
                star.style.fontSize = (15 + Math.random() * 25) + 'px';
                star.style.opacity = Math.random();
                star.style.animationDelay = Math.random() * 1 + 's';
                sparkleDiv.appendChild(star);
                setTimeout(() => star.remove(), 1000);
            }
        }
        
        // Chạy hiệu ứng
        createConfetti();
        createSparkle();
        
        // Tạo confetti đợt 2 sau 1 giây
        setTimeout(createConfetti, 1000);
        setTimeout(createSparkle, 1500);
        
        function copyKey() {
            const key = document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(key).then(() => {
                const btn = event.target;
                const originalText = btn.innerText;
                btn.innerText = '✅ Đã sao chép!';
                setTimeout(() => { 
                    btn.innerText = originalText; 
                }, 2000);
                
                // Hiệu ứng thông báo đẹp
                const notification = document.createElement('div');
                notification.innerHTML = '✅ Đã sao chép key!';
                notification.style.position = 'fixed';
                notification.style.bottom = '20px';
                notification.style.left = '50%';
                notification.style.transform = 'translateX(-50%)';
                notification.style.background = '#00ff88';
                notification.style.color = '#0a0a0a';
                notification.style.padding = '10px 20px';
                notification.style.borderRadius = '30px';
                notification.style.fontWeight = 'bold';
                notification.style.zIndex = '10000';
                notification.style.animation = 'fadeOut 2s forwards';
                document.body.appendChild(notification);
                setTimeout(() => notification.remove(), 2000);
            });
        }
        
        // Thêm animation fadeOut
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeOut {
                0% { opacity: 1; transform: translateX(-50%) translateY(0); }
                70% { opacity: 1; }
                100% { opacity: 0; transform: translateX(-50%) translateY(-20px); visibility: hidden; }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lỗi - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            position: relative;
        }
        
        .shake {
            animation: shake 0.5s ease;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
        
        .card {
            max-width: 450px;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(239, 68, 68, 0.4);
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: scale(0.9);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .error-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            animation: bounce 1s infinite;
        }
        
        @keyframes bounce {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-10px);
            }
        }
        
        h2 {
            color: #f87171;
            margin-bottom: 0.5rem;
            font-size: 1.8rem;
        }
        
        p {
            color: #aaa;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }
        
        .btn-back {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            color: white;
            text-decoration: none;
            padding: 0.8rem 1.8rem;
            border-radius: 2rem;
            display: inline-block;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-back:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(176,0,255,0.3);
        }
        
        @media (max-width: 480px) {
            .card {
                padding: 1.5rem;
            }
            h2 {
                font-size: 1.4rem;
            }
            .error-icon {
                font-size: 3rem;
            }
        }
    </style>
</head>
<body>
    <div class="card shake">
        <div class="error-icon">⚠️</div>
        <h2>Đã xảy ra lỗi</h2>
        <p>{{ message }}</p>
        <a href="/getkey" class="btn-back">🔄 Thử lại</a>
    </div>
</body>
</html>
"""

EARNING_DETAIL_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chi tiết thu nhập - DRAGON PINGX</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;padding:2rem}
        .container{max-width:1000px;margin:0 auto}
        h1{background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:1rem}
        .total-card{background:rgba(15,23,42,0.9);border-radius:1rem;padding:1.5rem;margin-bottom:1.5rem;border:1px solid rgba(176,0,255,0.3);text-align:center}
        .total-amount{font-size:3rem;font-weight:700;color:#00ff88}
        table{width:100%;border-collapse:collapse;background:rgba(15,23,42,0.9);border-radius:1rem;overflow:hidden}
        th,td{padding:1rem;text-align:left;color:#cbd5e1;border-bottom:1px solid rgba(176,0,255,0.2)}
        th{color:#b000ff}
        .back-btn{display:inline-block;margin-top:1.5rem;background:rgba(176,0,255,0.2);color:#b000ff;padding:0.5rem 1rem;border-radius:0.5rem;text-decoration:none}
        .link{color:#b000ff;text-decoration:none;word-break:break-all}
        .link:hover{text-decoration:underline}
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 CHI TIẾT THU NHẬP</h1>
        <div class="total-card">
            <div style="color:#666;margin-bottom:0.5rem">TỔNG THU NHẬP TỪ SESSION NÀY</div>
            <div class="total-amount">${{ "%.4f"|format(total) }} USD</div>
            <div style="color:#666;margin-top:0.5rem">≈ {{ "%.0f"|format(total * 25000) }} VNĐ</div>
        </div>
        <div style="overflow-x:auto">
            <table>
                <thead>
                    <tr>
                        <th>Thời gian</th>
                        <th>Dịch vụ</th>
                        <th>Số tiền</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in transactions %}
                    <tr>
                        <td>{{ t.time[:16] }}</td>
                        <td>{{ t.service }}</td>
                        <td>${{ "%.4f"|format(t.amount) }}</td>
                        <td><a href="{{ t.link }}" target="_blank" class="link">{{ t.link[:50] }}...</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <a href="/" class="back-btn">← Về trang chủ</a>
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
    <title>Admin Panel - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            padding: 2rem;
        }
        
        .container {
            max-width: 1400px;
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
            font-size: 2rem;
        }
        
        .header p {
            color: #64748b;
            margin-top: 0.5rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1.5rem;
            border: 1px solid rgba(176, 0, 255, 0.3);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #64748b;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
        }
        
        .stat-card .value {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }
        
        .section {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(176, 0, 255, 0.3);
        }
        
        .section h2 {
            color: white;
            margin-bottom: 1rem;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section h2 i {
            font-size: 1.5rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            color: #cbd5e1;
            border-bottom: 1px solid rgba(176, 0, 255, 0.2);
        }
        
        th {
            color: #b000ff;
            font-weight: 600;
        }
        
        tr:hover {
            background: rgba(176, 0, 255, 0.05);
        }
        
        .btn {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            filter: brightness(1.05);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        
        .btn-warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #10b981, #059669);
        }
        
        .logout {
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .logout:hover {
            background: rgba(239, 68, 68, 0.4);
        }
        
        input, textarea, select {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(176, 0, 255, 0.3);
            padding: 0.75rem;
            border-radius: 0.5rem;
            color: white;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #b000ff;
            box-shadow: 0 0 10px rgba(176, 0, 255, 0.3);
        }
        
        .flex {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        .flex-between {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        
        code {
            background: rgba(0, 0, 0, 0.5);
            padding: 0.2rem 0.4rem;
            border-radius: 0.3rem;
            font-size: 0.85rem;
            color: #b000ff;
        }
        
        .badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 0.3rem;
            font-size: 0.7rem;
            font-weight: 600;
        }
        
        .badge-success {
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
        }
        
        .badge-warning {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
        }
        
        .badge-danger {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
        }
        
        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(176, 0, 255, 0.2);
            padding-bottom: 0.5rem;
        }
        
        .tab {
            padding: 0.5rem 1rem;
            cursor: pointer;
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            color: white;
        }
        
        .tab:hover:not(.active) {
            background: rgba(176, 0, 255, 0.2);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }
            .stat-card .value {
                font-size: 1.8rem;
            }
            table {
                font-size: 0.8rem;
            }
            th, td {
                padding: 0.5rem;
            }
        }
        
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            .flex {
                flex-direction: column;
            }
            .logout {
                position: static;
                display: inline-block;
                margin-bottom: 1rem;
            }
        }
    </style>
</head>
<body>
    <a href="/admin/logout" class="logout">🚪 Đăng xuất</a>
    
    <div class="container">
        <div class="header">
            <h1>🔐 DRAGON PINGX ADMIN PANEL</h1>
            <p>Quản lý hệ thống key, theo dõi thống kê và bảo mật</p>
        </div>
        
        <!-- Thống kê -->
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
                <div class="value">${{ "%.4f"|format(earnings.total) }}</div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" data-tab="tab1">🔑 Quản lý key</div>
            <div class="tab" data-tab="tab2">🚫 Blacklist</div>
            <div class="tab" data-tab="tab3">💰 Thu nhập</div>
            <div class="tab" data-tab="tab4">📊 Thống kê</div>
        </div>
        
        <!-- Tab 1: Quản lý key -->
        <div id="tab1" class="tab-content active">
            <div class="section">
                <div class="flex-between">
                    <h2>🔑 Tạo key mới</h2>
                    <form method="POST" action="/admin/create_key" class="flex" style="gap: 10px;">
                        <input type="text" name="note" placeholder="Ghi chú (tùy chọn)" style="width: 250px;">
                        <button type="submit" class="btn">➕ Tạo key mới</button>
                    </form>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Danh sách key gần đây</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Key</th>
                                <th>Trạng thái</th>
                                <th>Hết hạn</th>
                                <th>Ngày tạo</th>
                                <th>Ghi chú</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for key_info in keys %}
                            <tr>
                                <td><code>{{ key_info.key }}</code></td>
                                <td>
                                    {% if key_info.used %}
                                    <span class="badge badge-danger">✅ Đã dùng</span>
                                    {% else %}
                                    <span class="badge badge-success">🟢 Còn hiệu lực</span>
                                    {% endif %}
                                </td>
                                <td>{{ key_info.expires_at[:16] if key_info.expires_at else 'N/A' }}</td>
                                <td>{{ key_info.created_at[:16] if key_info.created_at else 'N/A' }}</td>
                                <td>{{ key_info.note if key_info.note else '-' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Tab 2: Blacklist -->
        <div id="tab2" class="tab-content">
            <div class="section">
                <div class="flex-between">
                    <h2>🚫 Quản lý Blacklist</h2>
                    <form method="POST" action="/admin/blacklist" class="flex" style="gap: 10px;">
                        <input type="text" name="ip" placeholder="Nhập IP cần chặn" style="width: 250px;">
                        <button type="submit" class="btn btn-danger">🚫 Thêm IP</button>
                    </form>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Danh sách IP bị chặn</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr><th>IP</th><th>Lý do</th><th>Hành động</th></tr>
                        </thead>
                        <tbody>
                            {% for ip in blacklist.ips %}
                            <tr>
                                <td><code>{{ ip }}</code></td>
                                <td>{{ blacklist.reasons.get(ip, 'Vi phạm quy định') }}</td>
                                <td><a href="/admin/unban?ip={{ ip }}" class="btn btn-warning" style="padding: 0.3rem 0.8rem;">🔓 Bỏ chặn</a></td>
                            </tr>
                            {% else %}
                            <tr><td colspan="3" style="text-align: center;">Không có IP nào trong blacklist</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Tab 3: Thu nhập -->
        <div id="tab3" class="tab-content">
            <div class="section">
                <h2>💰 Chi tiết thu nhập theo dịch vụ</h2>
                <div class="stats-grid" style="grid-template-columns: repeat(3, 1fr);">
                    <div class="stat-card">
                        <h3>🚀 Vuotnhanh.com</h3>
                        <div class="value">${{ "%.4f"|format(earnings_by_service.vuotnhanh) }}</div>
                    </div>
                    <div class="stat-card">
                        <h3>💰 Yeumoney.com</h3>
                        <div class="value">${{ "%.4f"|format(earnings_by_service.yeumoney) }}</div>
                    </div>
                    <div class="stat-card">
                        <h3>🔗 Link4m.co</h3>
                        <div class="value">${{ "%.4f"|format(earnings_by_service.link4m) }}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📅 Thu nhập theo ngày</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr><th>Ngày</th><th>Vuotnhanh</th><th>Yeumoney</th><th>Link4M</th><th>Tổng</th></tr>
                        </thead>
                        <tbody>
                            {% for date, services in daily_earnings.items()|reverse %}
                            <tr>
                                <td>{{ date }}</td>
                                <td>${{ "%.4f"|format(services.details.get('vuotnhanh', 0) + services.details.get('vuotnhanh_completed', 0)) }}</td>
                                <td>${{ "%.4f"|format(services.details.get('yeumoney', 0) + services.details.get('yeumoney_completed', 0)) }}</td>
                                <td>${{ "%.4f"|format(services.details.get('link4m', 0) + services.details.get('link4m_completed', 0)) }}</td>
                                <td><strong>${{ "%.4f"|format(services.total) }}</strong></td>
                             </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Lịch sử giao dịch gần đây</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr><th>Thời gian</th><th>Dịch vụ</th><th>Số tiền</th><th>IP</th><th>Link</th></tr>
                        </thead>
                        <tbody>
                            {% for trans in transactions %}
                            <tr>
                                <td>{{ trans.time[:16] }}</td>
                                <td>{{ trans.service }}</td>
                                <td>${{ "%.4f"|format(trans.amount) }}</td>
                                <td>{{ trans.ip }}</td>
                                <td><a href="{{ trans.link }}" target="_blank" style="color:#b000ff">Xem</a></td>
                             </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Tab 4: Thống kê -->
        <div id="tab4" class="tab-content">
            <div class="section">
                <h2>📊 Thống kê chi tiết</h2>
                <div style="display: grid; gap: 1rem;">
                    <div class="flex-between">
                        <span>📅 Ngày bắt đầu:</span>
                        <code>{{ stats.started_at[:16] if stats.started_at else 'N/A' }}</code>
                    </div>
                    <div class="flex-between">
                        <span>🕐 Cập nhật lần cuối:</span>
                        <code>{{ stats.last_updated[:16] if stats.last_updated else 'N/A' }}</code>
                    </div>
                    <div class="flex-between">
                        <span>📊 Tỷ lệ sử dụng key:</span>
                        <code>{% if stats.total_keys_generated > 0 %}{{ "%.1f"|format(stats.total_keys_used / stats.total_keys_generated * 100) }}{% else %}0{% endif %}%</code>
                    </div>
                    <div class="flex-between">
                        <span>📈 Tổng số task đã hoàn thành:</span>
                        <code>{{ stats.total_tasks_completed }}</code>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Key tạo theo ngày</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead><tr><th>Ngày</th><th>Số lượng</th></thead>
                        <tbody>
                            {% for date, count in stats.daily_keys.items()|reverse %}
                            <tr><td>{{ date }}</td><td>{{ count }}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>👥 Người dùng theo ngày</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead><tr><th>Ngày</th><th>Số lượng</th></thead>
                        <tbody>
                            {% for date, count in stats.daily_users.items()|reverse %}
                            <tr><td>{{ date }}</td><td>{{ count }}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.dataset.tab;
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            });
        });
    </script>
</body>
</html>
"""

# ========== ROUTES ==========
@app.route('/')
def index():
    """Trang chủ"""
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    """Bắt đầu quy trình lấy key"""
    fingerprint = get_client_fingerprint()
    ip = request.remote_addr
    
    # Kiểm tra blacklist
    if is_blacklisted(ip, fingerprint):
        return render_template_string(ERROR_HTML, message="Truy cập của bạn đã bị chặn do vi phạm điều khoản sử dụng.")
    
    # Kiểm tra rate limit
    if not check_rate_limit('getkey', fingerprint):
        add_to_blacklist(ip, fingerprint, "Vượt quá giới hạn lấy key")
        return render_template_string(ERROR_HTML, message="Bạn đang thực hiện quá nhiều yêu cầu. Vui lòng thử lại sau 5 phút.")
    
    # Tạo session mới
    session_id = generate_session_id()
    
    # Tạo task mới
    task = create_user_task(session_id, fingerprint, ip)
    
    # Cập nhật thống kê
    update_stats('new_user')
    
    # Gửi thông báo Telegram
    notify_new_user(ip, fingerprint, session_id)
    
    # Chuyển đến step 1
    return redirect(f'/step/{session_id}/1')

@app.route('/step/<session_id>/<int:step_num>')
def show_step(session_id, step_num):
    """Hiển thị trang nhiệm vụ"""
    fingerprint = get_client_fingerprint()
    
    # Lấy task
    task = get_user_task(session_id)
    if not task:
        return render_template_string(ERROR_HTML, message="Phiên không hợp lệ hoặc đã hết hạn!")
    
    # Kiểm tra fingerprint
    if task.get('fingerprint') != fingerprint:
        return render_template_string(ERROR_HTML, message="Phát hiện truy cập trái phép. Phiên đã bị khóa.")
    
    # Cấu hình các bước
    steps_config = {
        1: {
            'title': '🚀 Vượt Nhanh',
            'desc': 'Hoàn thành nhiệm vụ trên Vượt Nhanh để tiếp tục',
            'url_key': 'step1_url',
            'back_url': '/getkey'
        },
        2: {
            'title': '💰 Yeumoney',
            'desc': 'Hoàn thành nhiệm vụ trên Yeumoney để tiếp tục',
            'url_key': 'step2_url',
            'back_url': f'/step/{session_id}/1'
        },
        3: {
            'title': '🔗 Link4M',
            'desc': 'Hoàn thành nhiệm vụ cuối cùng trên Link4M để nhận KEY',
            'url_key': 'step3_url',
            'back_url': f'/step/{session_id}/2'
        }
    }
    
    config = steps_config.get(step_num)
    if not config:
        return render_template_string(ERROR_HTML, message="Bước không hợp lệ!")
    
    return render_template_string(STEP_HTML,
        step_index=step_num,
        step_title=config['title'],
        step_desc=config['desc'],
        task_url=task.get(config['url_key'], '#'),
        session_id=session_id,
        total_steps=3,
        back_url=config['back_url']
    )

@app.route('/api/callback/<session_id>/<int:step_num>')
def step_callback(session_id, step_num):
    """Callback khi hoàn thành nhiệm vụ từ các dịch vụ"""
    tasks = load_user_tasks()
    
    if session_id not in tasks:
        return "Session not found", 404
    
    task = tasks[session_id]
    fingerprint = get_client_fingerprint()
    
    # Kiểm tra fingerprint
    if task.get('fingerprint') != fingerprint:
        return "Invalid fingerprint", 403
    
    # Cập nhật task
    success, message = update_task_step(session_id, step_num)
    
    if success:
        # Nếu là bước 3, tạo key
        if step_num == 3:
            success, key, message = complete_final_step(session_id)
            if success:
                logger.info(f"Đã tạo key mới cho session {session_id}: {key}")
        
        return "OK"
    else:
        logger.warning(f"Callback thất bại: {message}")
        return message, 400

@app.route('/api/check_step/<session_id>/<int:step_num>')
def check_step(session_id, step_num):
    """Kiểm tra xem bước đã hoàn thành chưa"""
    fingerprint = get_client_fingerprint()
    
    # Kiểm tra rate limit
    if not check_rate_limit('check_step', fingerprint):
        return jsonify({'completed': False, 'error': 'Rate limit'})
    
    # Lấy task
    task = get_user_task(session_id)
    if not task:
        return jsonify({'completed': False, 'error': 'Session not found'})
    
    # Kiểm tra fingerprint
    if task.get('fingerprint') != fingerprint:
        return jsonify({'completed': False, 'error': 'Invalid session'})
    
    # Kiểm tra trạng thái
    completed = False
    next_url = None
    
    if step_num == 1 and task.get('step1_completed'):
        completed = True
        next_url = f'/step/{session_id}/2'
    elif step_num == 2 and task.get('step2_completed'):
        completed = True
        next_url = f'/step/{session_id}/3'
    elif step_num == 3 and task.get('step3_completed'):
        completed = True
        next_url = f'/final/{session_id}'
    
    return jsonify({'completed': completed, 'next_url': next_url})

@app.route('/final/<session_id>')
def final_step(session_id):
    """Trang hiển thị key cuối cùng"""
    fingerprint = get_client_fingerprint()
    
    # Lấy task
    task = get_user_task(session_id)
    if not task:
        return render_template_string(ERROR_HTML, message="Phiên không hợp lệ hoặc đã hết hạn!")
    
    # Kiểm tra fingerprint
    if task.get('fingerprint') != fingerprint:
        return render_template_string(ERROR_HTML, message="Phát hiện truy cập trái phép.")
    
    # Lấy key
    key = task.get('key')
    if not key:
        return render_template_string(ERROR_HTML, message="Chưa có key! Vui lòng hoàn thành các bước trước.")
    
    return render_template_string(FINAL_HTML, key=key)

@app.route('/earning/<session_id>')
def earning_detail(session_id):
    """Trang chi tiết thu nhập theo session"""
    fingerprint = get_client_fingerprint()
    
    # Lấy task
    task = get_user_task(session_id)
    if not task:
        return render_template_string(ERROR_HTML, message="Phiên không hợp lệ!")
    
    # Kiểm tra fingerprint
    if task.get('fingerprint') != fingerprint:
        return render_template_string(ERROR_HTML, message="Truy cập trái phép!")
    
    # Lấy danh sách giao dịch theo session
    earnings = load_json_file(EARNINGS_FILE, {})
    transactions = [t for t in earnings.get('transactions', []) if t.get('session_id') == session_id]
    total = sum(t.get('amount', 0) for t in transactions)
    
    return render_template_string(EARNING_DETAIL_HTML, transactions=transactions, total=total)

@app.route('/api/verify', methods=['POST'])
def verify_key():
    """API xác thực key cho ứng dụng"""
    fingerprint = get_client_fingerprint()
    ip = request.remote_addr
    
    # Kiểm tra blacklist
    if is_blacklisted(ip, fingerprint):
        return jsonify({'status': 'error', 'message': 'Truy cập bị chặn'}), 403
    
    # Kiểm tra rate limit
    if not check_rate_limit('verify', fingerprint):
        add_to_blacklist(ip, fingerprint, "Vượt quá giới hạn xác thực key")
        return jsonify({'status': 'error', 'message': 'Quá nhiều lần thử. Bạn đã bị chặn tạm thời.'}), 429
    
    # Lấy key từ request
    data = request.json
    key = data.get('key', '').strip().upper()
    
    if not key:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập key!'})
    
    # Kiểm tra checksum
    if not verify_key_checksum(key):
        return jsonify({'status': 'invalid', 'message': '❌ Key không hợp lệ!'})
    
    # Admin keys
    admin_keys = ["QANHNO1CRACKER", "DRAGONLOCUT", "DRAGONLOCUT2024"]
    if key in admin_keys:
        expires = (datetime.now() + timedelta(days=365)).isoformat()
        return jsonify({
            'status': 'success',
            'message': '✅ Kích hoạt thành công!',
            'key': key,
            'expires_at': expires
        })
    
    # Kích hoạt key
    success, message = activate_key(key, fingerprint)
    
    if success:
        # Cập nhật thống kê
        update_stats('key_used')
        
        # Gửi thông báo Telegram
        notify_key_used(key, ip, fingerprint)
        
        return jsonify({
            'status': 'success',
            'message': '✅ Key hợp lệ!',
            'key': key
        })
    else:
        return jsonify({'status': 'error', 'message': message})

@app.route('/api/stats')
def api_stats():
    """API lấy thống kê công khai"""
    stats = load_stats()
    earnings = load_json_file(EARNINGS_FILE, {})
    return jsonify({
        'total_keys_generated': stats.get('total_keys_generated', 0),
        'total_keys_used': stats.get('total_keys_used', 0),
        'total_users': stats.get('total_users', 0),
        'total_earnings_usd': earnings.get('total', 0)
    })

# ========== ADMIN ROUTES ==========
def admin_required(f):
    """Decorator yêu cầu đăng nhập admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin Login"'}))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_required
def admin_panel():
    """Trang quản trị"""
    stats = load_stats()
    earnings = load_json_file(EARNINGS_FILE, {})
    earnings_by_service = get_earnings_by_service()
    daily_earnings = get_daily_earnings()
    blacklist = load_blacklist()
    keys = get_all_keys(limit=50)
    transactions = get_transactions(limit=100)
    
    return render_template_string(ADMIN_HTML,
        stats=stats,
        earnings=earnings,
        earnings_by_service=earnings_by_service,
        daily_earnings=daily_earnings,
        blacklist=blacklist,
        keys=keys,
        transactions=transactions
    )

@app.route('/admin/create_key', methods=['POST'])
@admin_required
def admin_create_key():
    """Tạo key mới từ admin"""
    note = request.form.get('note', '')
    new_key = create_new_key(expires_hours=720, note=note)  # 30 ngày
    
    # Gửi thông báo Telegram
    send_telegram_message(f"👑 <b>Admin đã tạo key mới!</b>\n<code>{new_key}</code>\n📝 Ghi chú: {note}")
    
    return redirect('/admin')

@app.route('/admin/blacklist', methods=['POST'])
@admin_required
def admin_add_blacklist():
    """Thêm IP vào blacklist"""
    ip = request.form.get('ip', '')
    if ip:
        add_to_blacklist(ip, '', 'Admin thêm thủ công')
    return redirect('/admin')

@app.route('/admin/unban')
@admin_required
def admin_remove_blacklist():
    """Xóa IP khỏi blacklist"""
    ip = request.args.get('ip', '')
    if ip:
        remove_from_blacklist(ip=ip)
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    """Đăng xuất admin"""
    return make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin Login"'}))

# ========== TỰ ĐỘNG DỌN DẸP ==========
def schedule_cleanup():
    """Lên lịch dọn dẹp định kỳ"""
    def cleanup_job():
        while True:
            time.sleep(3600)  # Mỗi giờ
            cleanup_expired_tasks()
            cleanup_expired_keys()
    
    thread = threading.Thread(target=cleanup_job, daemon=True)
    thread.start()

# Chạy cleanup trong thread riêng (chỉ khi chạy production)
if __name__ != '__main__':
    schedule_cleanup()

# ========== CHẠY APP ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Chạy cleanup trong thread riêng
    schedule_cleanup()
    
    logger.info(f"🚀 Khởi động DRAGON PINGX PREMIUM tại port {port}")
    logger.info(f"📍 Domain: {YOUR_DOMAIN}")
    logger.info(f"🔐 Admin: {YOUR_DOMAIN}/admin (user: {ADMIN_USERNAME})")
    
    app.run(host='0.0.0.0', port=port, debug=False)