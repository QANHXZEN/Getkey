from flask import Flask, request, jsonify, render_template_string
import random
import string
from datetime import datetime, timedelta
import os
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database lưu key
keys_db = {}

def generate_dragon_key():
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=6))
    part2 = ''.join(random.choices(chars, k=4))
    return f"DRP-{part1}-{part2}"

# ========== HTML TEMPLATES UI ĐẸP ==========

INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>DRAGON PINGX PREMIUM | Hệ Thống Kích Hoạt Chính Thức</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(ellipse at 20% 30%, #0a0a0a, #05050a);
            min-height: 100vh;
            overflow-x: hidden;
        }
        .stars {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><circle cx="100" cy="200" r="2" fill="white" opacity="0.5"/><circle cx="300" cy="100" r="1.5" fill="white" opacity="0.3"/><circle cx="500" cy="300" r="2" fill="white" opacity="0.6"/><circle cx="700" cy="150" r="1" fill="white" opacity="0.4"/><circle cx="850" cy="400" r="2" fill="white" opacity="0.5"/><circle cx="150" cy="500" r="1.5" fill="white" opacity="0.3"/><circle cx="450" cy="600" r="2" fill="white" opacity="0.7"/><circle cx="650" cy="700" r="1" fill="white" opacity="0.4"/><circle cx="800" cy="800" r="2" fill="white" opacity="0.5"/><circle cx="200" cy="750" r="1.5" fill="white" opacity="0.3"/></svg>') repeat;
            opacity: 0.3;
            animation: twinkle 4s ease-in-out infinite;
        }
        @keyframes twinkle {
            0%, 100% { opacity: 0.2; }
            50% { opacity: 0.5; }
        }
        .glow {
            position: fixed;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(176,0,255,0.15), transparent);
            border-radius: 50%;
            top: -200px;
            right: -200px;
            pointer-events: none;
        }
        .glow2 {
            position: fixed;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(255,0,255,0.1), transparent);
            border-radius: 50%;
            bottom: -200px;
            left: -200px;
            pointer-events: none;
        }
        .container {
            position: relative;
            z-index: 10;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        .hero {
            text-align: center;
            max-width: 700px;
        }
        .badge {
            display: inline-block;
            background: rgba(176,0,255,0.15);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1.2rem;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #b000ff;
            border: 1px solid rgba(176,0,255,0.3);
            margin-bottom: 2rem;
            letter-spacing: 1px;
        }
        h1 {
            font-size: 4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #b000ff, #ff00ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 1.5rem;
            text-shadow: 0 0 30px rgba(176,0,255,0.3);
        }
        .sub {
            font-size: 1.2rem;
            color: #888;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        .btn-primary {
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            border: none;
            padding: 1.2rem 3rem;
            font-size: 1.1rem;
            font-weight: 700;
            color: white;
            border-radius: 60px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(176,0,255,0.3);
            display: inline-flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 20px 40px rgba(176,0,255,0.4);
        }
        .features {
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-top: 4rem;
            flex-wrap: wrap;
        }
        .feature {
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            padding: 1rem 1.8rem;
            border-radius: 1.5rem;
            font-size: 0.85rem;
            color: #aaa;
            border: 1px solid rgba(176,0,255,0.1);
        }
        @media (max-width: 640px) {
            h1 { font-size: 2.5rem; }
            .btn-primary { padding: 1rem 2rem; }
        }
    </style>
</head>
<body>
    <div class="stars"></div>
    <div class="glow"></div>
    <div class="glow2"></div>
    <div class="container">
        <div class="hero">
            <div class="badge">⚡ DRAGON PINGX PREMIUM | CHÍNH THỨC</div>
            <h1>DRAGON PINGX</h1>
            <div class="sub">Hệ thống kích hoạt bản quyền tự động<br>Bảo mật - Nhanh chóng - Uy tín hàng đầu</div>
            <a href="/getkey" class="btn-primary">
                🚀 LẤY KEY NGAY
                <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7m0 0l-7 7m7-7H3"/></svg>
            </a>
            <div class="features">
                <div class="feature">🔒 Bảo mật SSL</div>
                <div class="feature">⚡ Kích hoạt tức thì</div>
                <div class="feature">💎 Premium Support 24/7</div>
            </div>
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Lấy Key - DRAGON PINGX PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(ellipse at 20% 30%, #0a0a0a, #05050a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .glow {
            position: fixed;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(176,0,255,0.15), transparent);
            border-radius: 50%;
            top: -200px;
            right: -200px;
            pointer-events: none;
        }
        .card {
            max-width: 500px;
            width: 100%;
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(20px);
            border-radius: 2.5rem;
            padding: 2rem 2rem 2.5rem;
            border: 1px solid rgba(176, 0, 255, 0.2);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            animation: fadeIn 0.6s ease;
            position: relative;
            z-index: 10;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
        .premium-badge {
            display: inline-block;
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            padding: 0.3rem 1rem;
            border-radius: 50px;
            font-size: 0.7rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1.5rem;
        }
        .icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            border-radius: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            box-shadow: 0 0 30px rgba(176,0,255,0.4);
        }
        h2 {
            color: white;
            text-align: center;
            margin-bottom: 0.5rem;
            font-size: 1.8rem;
        }
        .desc {
            color: #94a3b8;
            text-align: center;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }
        .info-card {
            background: rgba(0,0,0,0.3);
            border-radius: 1.2rem;
            padding: 1.2rem;
            margin-bottom: 2rem;
        }
        .info-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: #b000ff;
            font-size: 0.85rem;
            margin-bottom: 0.75rem;
        }
        .info-item:last-child { margin-bottom: 0; }
        .btn-get {
            width: 100%;
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            border: none;
            padding: 1rem;
            border-radius: 1.5rem;
            color: white;
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-get:hover {
            transform: translateY(-2px);
            filter: brightness(1.05);
            box-shadow: 0 10px 25px rgba(176,0,255,0.3);
        }
        .btn-get:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .result-box {
            margin-top: 1.5rem;
            padding: 1rem;
            background: rgba(0,0,0,0.4);
            border-radius: 1rem;
            border-left: 3px solid #b000ff;
            display: none;
        }
        .result-box.show {
            display: block;
            animation: slideUp 0.4s ease;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .key-display {
            background: #0f172a;
            padding: 0.75rem;
            border-radius: 0.75rem;
            font-family: monospace;
            font-size: 1rem;
            font-weight: 700;
            color: #b000ff;
            text-align: center;
            margin: 0.75rem 0;
            letter-spacing: 1px;
            word-break: break-all;
        }
        .copy-btn {
            background: rgba(176,0,255,0.2);
            border: 1px solid rgba(176,0,255,0.4);
            padding: 0.5rem 1.2rem;
            border-radius: 2rem;
            color: #b000ff;
            cursor: pointer;
            font-size: 0.8rem;
            transition: 0.2s;
        }
        .copy-btn:hover {
            background: #b000ff;
            color: white;
        }
        .footer-note {
            margin-top: 1.5rem;
            text-align: center;
            font-size: 0.7rem;
            color: #475569;
        }
    </style>
</head>
<body>
    <div class="glow"></div>
    <div class="card">
        <div style="text-align:center">
            <div class="premium-badge">✨ PREMIUM ACTIVATION</div>
        </div>
        <div class="icon">
            <svg width="40" height="40" fill="none" stroke="white" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
        </div>
        <h2>DRAGON PINGX PREMIUM</h2>
        <div class="desc">Nhận key kích hoạt bản quyền ngay hôm nay</div>
        
        <div class="info-card">
            <div class="info-item">📌 Key có hiệu lực 24 giờ</div>
            <div class="info-item">🔒 1 key = 1 thiết bị duy nhất</div>
            <div class="info-item">⚡ Kích hoạt ngay sau khi nhận</div>
            <div class="info-item">💎 Hỗ trợ 24/7</div>
        </div>
        
        <button class="btn-get" onclick="generateKey()" id="getKeyBtn">
            🔥 LẤY KEY NGAY
        </button>
        
        <div id="resultBox" class="result-box">
            <div id="resultContent"></div>
        </div>
        
        <div class="footer-note">
            © 2025 DRAGON PINGX PREMIUM • Bảo mật tuyệt đối
        </div>
    </div>
    
    <script>
        async function generateKey() {
            const btn = document.getElementById('getKeyBtn');
            const resultBox = document.getElementById('resultBox');
            const resultContent = document.getElementById('resultContent');
            
            btn.innerHTML = '<span class="loading-spinner"></span> Đang tạo key...';
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/create');
                const data = await response.json();
                
                if (data.success) {
                    resultContent.innerHTML = `
                        <div style="font-size:0.85rem; margin-bottom:0.75rem;">🎉 <strong>KEY CỦA BẠN ĐÃ SẴN SÀNG</strong></div>
                        <div class="key-display" id="licenseKey">${data.key}</div>
                        <div style="display:flex; gap:10px; justify-content:center; margin-top:0.75rem;">
                            <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
                        </div>
                        <div style="font-size:0.7rem; color:#64748b; text-align:center; margin-top:0.75rem;">
                            ⏰ Hạn sử dụng: ${data.expires}
                        </div>
                    `;
                    resultBox.classList.add('show');
                } else {
                    alert('Lỗi: ' + (data.message || 'Không thể tạo key'));
                }
            } catch (error) {
                alert('Lỗi kết nối! Vui lòng thử lại sau.');
                console.error(error);
            } finally {
                btn.innerHTML = '🔥 LẤY KEY NGAY';
                btn.disabled = false;
            }
        }
        
        function copyKey() {
            const key = document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(key).then(() => {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ Đã sao chép!';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                }, 2000);
            });
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(ellipse at 20% 30%, #0a0a0a, #05050a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 500px;
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2.5rem;
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
        .desc { color: #94a3b8; margin-bottom: 1.5rem; }
        .key-box {
            background: #0f172a;
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
        .warning { font-size: 0.7rem; color: #64748b; margin: 1rem 0; }
        .btn-back {
            display: inline-block;
            background: linear-gradient(135deg, #b000ff, #ff00ff);
            text-decoration: none;
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 2rem;
            font-weight: 600;
            margin-top: 1rem;
        }
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
        <div class="desc">Bạn đã hoàn thành nhiệm vụ thành công</div>
        <div class="key-box">
            <div class="key-label">🔑 KEY KÍCH HOẠT CỦA BẠN</div>
            <div class="key-value" id="licenseKey">{{ key }}</div>
            <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
        </div>
        <div class="warning">
            ⏰ Key có hiệu lực trong {{ expires }}<br>
            📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM để kích hoạt
        </div>
        <a href="/" class="btn-back">🏠 Về trang chủ</a>
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

# ========== API ROUTES ==========

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    return render_template_string(GETKEY_HTML)

@app.route('/api/create')
def create_key():
    key = generate_dragon_key()
    expires_at = datetime.now() + timedelta(hours=24)
    keys_db[key] = {
        'expires_at': expires_at.isoformat(),
        'used': False,
        'created_at': datetime.now().isoformat()
    }
    return jsonify({
        'success': True,
        'key': key,
        'expires': '24 giờ'
    })

@app.route('/api/verify', methods=['POST'])
def verify_key():
    data = request.json
    key = data.get('key', '').strip().upper()
    
    if not key:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập key!'})
    
    if key not in keys_db:
        return jsonify({'status': 'invalid', 'message': 'Key không hợp lệ!'})
    
    info = keys_db[key]
    expires_at = datetime.fromisoformat(info['expires_at'])
    
    if datetime.now() > expires_at:
        return jsonify({'status': 'expired', 'message': 'Key đã hết hạn!'})
    
    if info.get('used', False):
        return jsonify({'status': 'used', 'message': 'Key đã được sử dụng!'})
    
    info['used'] = True
    info['used_at'] = datetime.now().isoformat()
    keys_db[key] = info
    
    return jsonify({
        'status': 'success',
        'message': 'Key hợp lệ!',
        'key': key,
        'expires_at': expires_at.isoformat(),
        'app_name': 'DRAGON PINGX PREMIUM'
    })

@app.route('/api/check/<key>')
def check_key(key):
    key = key.upper()
    if key not in keys_db:
        return "INVALID"
    info = keys_db[key]
    try:
        expires_at = datetime.fromisoformat(info['expires_at'])
        if datetime.now() > expires_at:
            return "EXPIRED"
        if info.get('used', False):
            return "USED"
        return "VALID"
    except:
        return "INVALID"

@app.route('/api/stats')
def stats():
    total = len(keys_db)
    valid = 0
    for k, v in keys_db.items():
        try:
            if datetime.now() < datetime.fromisoformat(v['expires_at']) and not v.get('used', False):
                valid += 1
        except:
            pass
    return jsonify({
        'total_keys': total,
        'valid_keys': valid,
        'server_time': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)