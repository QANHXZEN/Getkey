from flask import Flask, render_template, request, jsonify, session
import requests
import uuid
import os
import json
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ========== CẤU HÌNH ==========
LINK4M_API_KEY = os.environ.get("LINK4M_API_KEY", "65c47d157fbdff4d79625e57")
LINK4M_API_URL = "https://link4m.co/api-shorten/v2"
YOUR_DOMAIN = "https://roszmodxqanhno1.onrender.com"  # DOMAIN CỦA BẠN

DATA_FILE = "dragon_keys.json"

# ========== HÀM XỬ LÝ FILE ==========
def load_keys():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_keys(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_dragon_key():
    """Tạo key dạng DRP-XXXXXX-XXXX (10 chữ số ngẫu nhiên)"""
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=6))
    part2 = ''.join(random.choices(chars, k=4))
    return f"DRP-{part1}-{part2}"

def clean_expired_keys():
    """Xóa key hết hạn"""
    keys = load_keys()
    now = datetime.now()
    expired = []
    for key, info in keys.items():
        if key.startswith("DRP-"):
            try:
                expires = datetime.fromisoformat(info.get('expires_at', ''))
                if now > expires:
                    expired.append(key)
            except:
                expired.append(key)
    for key in expired:
        del keys[key]
    if expired:
        save_keys(keys)

# ========== ROUTE ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    return render_template_string(GETKEY_HTML, session_id=session_id)

@app.route('/generate_task', methods=['POST'])
def generate_task():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400
    
    callback_url = f"{YOUR_DOMAIN}/donekey?session_id={session_id}"
    
    try:
        params = {'api': LINK4M_API_KEY, 'url': callback_url}
        response = requests.get(LINK4M_API_URL, params=params, timeout=10)
        result = response.json()
        task_url = result.get('shortenedUrl', callback_url)
    except:
        task_url = callback_url
    
    keys = load_keys()
    keys[session_id] = {
        'type': 'pending',
        'created_at': datetime.now().isoformat(),
        'status': 'waiting'
    }
    save_keys(keys)
    
    return jsonify({'success': True, 'task_url': task_url})

@app.route('/donekey')
def donekey():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return render_template_string(ERROR_HTML, message="Thiếu mã phiên!")
    
    keys = load_keys()
    
    if session_id not in keys:
        return render_template_string(ERROR_HTML, message="Phiên không hợp lệ!")
    
    if keys[session_id].get('status') == 'completed':
        return render_template_string(ERROR_HTML, message="Key đã được tạo trước đó!")
    
    # Tạo key mới dạng DRP-XXXXXX-XXXX
    new_key = generate_dragon_key()
    expires_at = datetime.now() + timedelta(hours=24)
    
    keys[session_id]['status'] = 'completed'
    keys[session_id]['key'] = new_key
    keys[session_id]['expires_at'] = expires_at.isoformat()
    
    # Lưu key vào danh sách key hợp lệ
    keys[new_key] = {
        'type': 'license',
        'created_at': datetime.now().isoformat(),
        'expires_at': expires_at.isoformat(),
        'used': False,
        'session_id': session_id
    }
    save_keys(keys)
    
    return render_template_string(SUCCESS_HTML, key=new_key, expires="24 giờ")

@app.route('/api/verify', methods=['POST'])
def verify_key():
    """API cho app Android kiểm tra key"""
    data = request.json
    key = data.get('key', '').strip().upper()
    
    if not key:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập key!'}), 400
    
    clean_expired_keys()
    keys = load_keys()
    
    # Kiểm tra key có tồn tại không
    if key not in keys:
        return jsonify({'status': 'invalid', 'message': 'Key không hợp lệ!'})
    
    info = keys[key]
    
    # Kiểm tra hết hạn
    try:
        expires_at = datetime.fromisoformat(info.get('expires_at', ''))
        if datetime.now() > expires_at:
            return jsonify({'status': 'expired', 'message': 'Key đã hết hạn!'})
    except:
        return jsonify({'status': 'invalid', 'message': 'Key không hợp lệ!'})
    
    # Kiểm tra đã sử dụng chưa
    if info.get('used', False):
        return jsonify({'status': 'used', 'message': 'Key đã được sử dụng!'})
    
    # Đánh dấu đã sử dụng
    info['used'] = True
    info['used_at'] = datetime.now().isoformat()
    info['device'] = request.headers.get('User-Agent', 'Unknown')
    save_keys(keys)
    
    return jsonify({
        'status': 'success',
        'message': 'Key hợp lệ!',
        'key': key,
        'expires_at': expires_at.isoformat(),
        'app_name': 'DRAGON PINGX PREMIUM'
    })

@app.route('/api/check/<key>')
def check_key(key):
    """API check nhanh (GET method)"""
    clean_expired_keys()
    keys = load_keys()
    key = key.upper()
    
    if key not in keys:
        return "INVALID"
    
    try:
        expires_at = datetime.fromisoformat(keys[key].get('expires_at', ''))
        if datetime.now() > expires_at:
            return "EXPIRED"
        if keys[key].get('used', False):
            return "USED"
        return "VALID"
    except:
        return "INVALID"

@app.route('/api/stats')
def stats():
    clean_expired_keys()
    keys = load_keys()
    valid_keys = 0
    for k, v in keys.items():
        if k.startswith("DRP-") and not v.get('used', False):
            try:
                if datetime.now() < datetime.fromisoformat(v.get('expires_at', '')):
                    valid_keys += 1
            except:
                pass
    return jsonify({
        'total_keys': len([k for k in keys if k.startswith("DRP-")]),
        'valid_keys': valid_keys,
        'server_time': datetime.now().isoformat()
    })

# ========== HTML TEMPLATES ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DRAGON PINGX PREMIUM | Hệ Thống Kích Hoạt Chính Thức</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a0033, #0a0a0a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .hero { text-align: center; max-width: 600px; animation: fadeInUp 0.8s ease; }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .badge {
            display: inline-block;
            background: rgba(176, 0, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1.2rem;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #b000ff;
            border: 1px solid rgba(176, 0, 255, 0.3);
            margin-bottom: 2rem;
        }
        h1 {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #fff, #b000ff, #ff00ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 1rem;
        }
        .sub { font-size: 1.1rem; color: #888; margin-bottom: 2rem; line-height: 1.6; }
        .btn-primary {
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            border: none;
            padding: 1rem 2.5rem;
            font-size: 1rem;
            font-weight: 600;
            color: white;
            border-radius: 60px;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
        }
        .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 20px 40px rgba(176, 0, 255, 0.3); }
        .stats {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(176, 0, 255, 0.2);
        }
        .stat-number { font-size: 1.5rem; font-weight: 700; color: #b000ff; }
        .stat-label { font-size: 0.75rem; color: #666; }
    </style>
</head>
<body>
    <div class="hero">
        <div class="badge">⚡ DRAGON PINGX PREMIUM | CHÍNH THỨC</div>
        <h1>DRAGON PINGX</h1>
        <div class="sub">Hệ thống kích hoạt bản quyền tự động<br>Bảo mật - Nhanh chóng - Uy tín</div>
        <a href="/getkey" class="btn-primary">
            🚀 LẤY KEY NGAY
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
        <div class="stats">
            <div><div class="stat-number">24/7</div><div class="stat-label">Hỗ trợ</div></div>
            <div><div class="stat-number">1.2k+</div><div class="stat-label">Người dùng</div></div>
            <div><div class="stat-number">99.9%</div><div class="stat-label">Uptime</div></div>
        </div>
    </div>
</body>
</html>
"""

GETKEY_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lấy Key - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a0033, #0a0a0a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 480px;
            width: 100%;
            background: rgba(26, 0, 51, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            border: 1px solid rgba(176, 0, 255, 0.3);
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        .icon {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            border-radius: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
        }
        h2 { color: white; text-align: center; margin-bottom: 0.5rem; }
        .desc { color: #888; text-align: center; font-size: 0.9rem; margin-bottom: 1.5rem; }
        .info-box {
            background: rgba(0,0,0,0.3);
            border-radius: 1rem;
            padding: 1rem;
            margin: 1.5rem 0;
        }
        .info-item { display: flex; align-items: center; gap: 0.75rem; color: #b000ff; font-size: 0.85rem; margin-bottom: 0.75rem; }
        .btn-get {
            width: 100%;
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            border: none;
            padding: 1rem;
            border-radius: 1rem;
            color: white;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-get:hover { transform: translateY(-2px); filter: brightness(1.05); }
        .btn-get:disabled { opacity: 0.6; cursor: not-allowed; }
        .loading-spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">
            <svg width="36" height="36" fill="none" stroke="white" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
        </div>
        <h2>DRAGON PINGX PREMIUM</h2>
        <div class="desc">Hoàn thành nhiệm vụ để nhận key kích hoạt</div>
        <div class="info-box">
            <div class="info-item">📌 Key có hiệu lực 24 giờ</div>
            <div class="info-item">🔒 1 key = 1 thiết bị</div>
            <div class="info-item">⚡ Kích hoạt ngay sau khi nhận</div>
        </div>
        <button class="btn-get" onclick="generateKey()" id="getKeyBtn">🔥 LẤY KEY NGAY</button>
    </div>
    <script>
        const sessionId = '{{ session_id }}';
        async function generateKey() {
            const btn = document.getElementById('getKeyBtn');
            btn.innerHTML = '<span class="loading-spinner"></span> Đang tạo...';
            btn.disabled = true;
            try {
                const response = await fetch('/generate_task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = data.task_url;
                } else {
                    alert('Lỗi: ' + (data.message || 'Không thể tạo link'));
                    btn.innerHTML = '🔥 LẤY KEY NGAY';
                    btn.disabled = false;
                }
            } catch (error) {
                alert('Lỗi kết nối! Vui lòng thử lại.');
                btn.innerHTML = '🔥 LẤY KEY NGAY';
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

SUCCESS_HTML = """
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
            background: linear-gradient(135deg, #0a0a0a, #1a0033, #0a0a0a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 500px;
            width: 100%;
            background: rgba(26, 0, 51, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(176, 0, 255, 0.3);
            animation: bounceIn 0.6s ease;
        }
        @keyframes bounceIn {
            0% { opacity: 0; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .success-icon {
            width: 80px;
            height: 80px;
            background: rgba(176, 0, 255, 0.15);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
        }
        h2 { color: white; font-size: 1.8rem; margin-bottom: 0.5rem; }
        .desc { color: #888; margin-bottom: 1.5rem; }
        .key-box {
            background: #0a0a0a;
            border-radius: 1rem;
            padding: 1.2rem;
            margin: 1.5rem 0;
            border: 1px dashed #b000ff;
        }
        .key-label { font-size: 0.7rem; color: #b000ff; text-transform: uppercase; letter-spacing: 1px; }
        .key-value {
            font-family: monospace;
            font-size: 1.2rem;
            font-weight: 700;
            color: #b000ff;
            word-break: break-all;
            margin: 0.5rem 0;
        }
        .copy-btn {
            background: rgba(176, 0, 255, 0.2);
            border: 1px solid #b000ff;
            padding: 0.5rem 1.2rem;
            border-radius: 2rem;
            color: #b000ff;
            cursor: pointer;
            font-size: 0.8rem;
        }
        .warning { font-size: 0.7rem; color: #666; margin: 1rem 0; }
    </style>
</head>
<body>
    <div class="card">
        <div class="success-icon">
            <svg width="48" height="48" fill="none" stroke="#b000ff" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
        </div>
        <h2>Thành Công!</h2>
        <div class="desc">Bạn đã hoàn thành nhiệm vụ</div>
        <div class="key-box">
            <div class="key-label">🔑 KEY KÍCH HOẠT CỦA BẠN</div>
            <div class="key-value" id="licenseKey">{{ key }}</div>
            <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
        </div>
        <div class="warning">
            ⏰ Key có hiệu lực trong {{ expires }}<br>
            📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM để kích hoạt
        </div>
    </div>
    <script>
        function copyKey() {
            const key = document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(key).then(() => {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ Đã sao chép!';
                setTimeout(() => { btn.innerHTML = originalText; }, 2000);
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lỗi - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a0033, #0a0a0a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 450px;
            background: rgba(26, 0, 51, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .error-icon { font-size: 4rem; margin-bottom: 1rem; }
        h2 { color: #f87171; margin-bottom: 0.5rem; }
        p { color: #888; margin-bottom: 1.5rem; }
        .btn-back {
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            color: white;
            text-decoration: none;
            padding: 0.8rem 1.5rem;
            border-radius: 2rem;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="error-icon">⚠️</div>
        <h2>Đã xảy ra lỗi</h2>
        <p>{{ message }}</p>
        <a href="/getkey" class="btn-back">🔄 Thử lại</a>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)