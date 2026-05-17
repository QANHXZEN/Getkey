from flask import Flask, render_template, render_template_string, request, jsonify, session, send_from_directory
import requests
import uuid
import os
import json
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'QanhNo1KeyVip')

# ========== CẤU HÌNH ==========
LINK4M_API_KEY = os.environ.get("LINK4M_API_KEY", "65c47d157fbdff4d79625e57")
LINK4M_API_URL = "https://link4m.co/api-shorten/v2"

# QUAN TRỌNG: Domain thật của bạn trên Render
YOUR_DOMAIN = "https://roszmodxqanhno1.onrender.com"  # Đã sửa đúng domain

DATA_FILE = "temp_keys.json"
APK_FOLDER = os.path.join(app.root_path, 'downloads')
os.makedirs(APK_FOLDER, exist_ok=True)

# ========== HÀM XỬ LÝ FILE ==========
def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ========== ROUTE CHÍNH ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/Getkey.php')
def get_main_web():
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    return render_template_string(MAIN_WEB_HTML, session_id=session_id)

@app.route('/generate_free_key', methods=['POST'])
def generate_free_key():
    data = request.json or {}
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'status': 'error', 'message': 'Phiên làm việc không hợp lệ'}), 400

    # FIX LỖI: Dùng domain thật, không phải localhost
    callback_url = f"{YOUR_DOMAIN}/DoneKey.php?session_id={session_id}"
    
    try:
        params = {'api': LINK4M_API_KEY, 'url': callback_url}
        response = requests.get(LINK4M_API_URL, params=params, timeout=10)
        res_json = response.json()
        
        if res_json.get('status') == 'success' or 'shortenedUrl' in res_json:
            short_url = res_json.get('shortenedUrl')
            
            db = load_data()
            db[session_id] = {
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'expire_at': (datetime.now() + timedelta(hours=24)).isoformat(),
                'ip': request.remote_addr
            }
            save_data(db)
            
            return jsonify({'status': 'success', 'link': short_url})
        else:
            return jsonify({'status': 'error', 'message': 'Không thể tạo link từ Link4M'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/DoneKey.php', methods=['GET'])
def done_key():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return render_template_string(ERROR_HTML, message="Thiếu mã phiên!")
        
    db = load_data()
    if session_id in db:
        # Tạo key độc đáo
        activation_key = f"PDV3-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:4].upper()}"
        
        db[session_id]['status'] = 'completed'
        db[session_id]['key'] = activation_key
        db[session_id]['activated_at'] = datetime.now().isoformat()
        save_data(db)
        
        return render_template_string(SUCCESS_HTML, activation_key=activation_key)
    else:
        return render_template_string(ERROR_HTML, message="Phiên không tồn tại hoặc hết hạn!")

# ========== API CHO APP ANDROID ==========
@app.route('/api/verify_key', methods=['POST'])
def verify_key():
    """App Android gọi API này để kiểm tra key"""
    req_data = request.json or {}
    user_key = req_data.get('key', '').strip()
    
    if not user_key:
        return jsonify({
            'status': 'error', 
            'message': 'Vui lòng nhập mã Key!'
        }), 400
    
    db = load_data()
    
    # Tìm key trong database
    for session_id, info in db.items():
        if info.get('key') == user_key:
            # Kiểm tra hết hạn
            expire_at = datetime.fromisoformat(info.get('expire_at'))
            if datetime.now() > expire_at:
                return jsonify({
                    'status': 'expired', 
                    'message': 'Key đã hết hạn (24h)!',
                    'expired_at': expire_at.isoformat()
                })
            
            # Key hợp lệ
            return jsonify({
                'status': 'success', 
                'message': '✅ Key hợp lệ!',
                'key': user_key,
                'expires_at': expire_at.isoformat(),
                'app_name': 'Ping Delay V3'
            })
    
    # Không tìm thấy key
    return jsonify({
        'status': 'invalid', 
        'message': '❌ Mã Key không chính xác hoặc chưa được kích hoạt.'
    }), 404

@app.route('/api/check_key/<key>', methods=['GET'])
def check_key(key):
    """API đơn giản để kiểm tra key (GET method)"""
    db = load_data()
    for session_id, info in db.items():
        if info.get('key') == key:
            expire_at = datetime.fromisoformat(info.get('expire_at'))
            if datetime.now() > expire_at:
                return jsonify({'valid': False, 'reason': 'expired'})
            return jsonify({'valid': True, 'expires': expire_at.isoformat()})
    return jsonify({'valid': False, 'reason': 'not_found'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API lấy thống kê (cho admin)"""
    db = load_data()
    total_keys = len(db)
    active_keys = sum(1 for info in db.values() 
                     if info.get('status') == 'completed' 
                     and datetime.now() < datetime.fromisoformat(info.get('expire_at')))
    
    return jsonify({
        'total_keys_generated': total_keys,
        'active_keys': active_keys,
        'server_time': datetime.now().isoformat()
    })

# ========== DOWNLOAD APK ==========
@app.route('/download/<filename>')
def download_file(filename):
    """Tải file APK"""
    # Kiểm tra file có tồn tại không
    file_path = os.path.join(APK_FOLDER, filename)
    if not os.path.exists(file_path):
        return render_template_string(ERROR_HTML, message=f"File {filename} không tồn tại!"), 404
    return send_from_directory(APK_FOLDER, filename, as_attachment=True)

@app.route('/download/latest')
def download_latest():
    """Tải phiên bản mới nhất"""
    # Tìm file apk mới nhất
    apk_files = [f for f in os.listdir(APK_FOLDER) if f.endswith('.apk')]
    if apk_files:
        latest = max(apk_files, key=lambda f: os.path.getctime(os.path.join(APK_FOLDER, f)))
        return send_from_directory(APK_FOLDER, latest, as_attachment=True)
    return render_template_string(ERROR_HTML, message="Chưa có file APK nào!"), 404

# ========== TEMPLATES HTML ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ping Delay V3 - Cổng kích hoạt chính thức</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .hero {
            text-align: center;
            max-width: 600px;
            animation: fadeInUp 0.8s ease;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .badge {
            display: inline-block;
            background: rgba(139, 92, 246, 0.2);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1.2rem;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #c4b5fd;
            border: 1px solid rgba(139, 92, 246, 0.3);
            margin-bottom: 2rem;
        }
        h1 {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #fff, #a78bfa, #8b5cf6);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 1rem;
        }
        .sub {
            font-size: 1.1rem;
            color: #a1a1aa;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        .btn-primary {
            background: linear-gradient(135deg, #8b5cf6, #6d28d9);
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
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 20px 40px rgba(139, 92, 246, 0.3);
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .stat-number {
            font-size: 1.5rem;
            font-weight: 700;
            color: #a78bfa;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #71717a;
        }
    </style>
</head>
<body>
    <div class="hero">
        <div class="badge">⚡ CHÍNH THỨC | VERIFIED</div>
        <h1>Ping Delay V3</h1>
        <div class="sub">Hệ thống kích hoạt bản quyền tự động<br>Bảo mật - Nhanh chóng - Uy tín</div>
        <a href="/Getkey.php" class="btn-primary">
            🚀 GET KEY NGAY
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7m0 0l-7 7m7-7H3"></path></svg>
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

MAIN_WEB_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lấy Key - Ping Delay V3</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 480px;
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            border: 1px solid rgba(139, 92, 246, 0.3);
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        .icon {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #8b5cf6, #6d28d9);
            border-radius: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
        }
        h2 { color: white; text-align: center; margin-bottom: 0.5rem; }
        .desc { color: #a1a1aa; text-align: center; font-size: 0.9rem; margin-bottom: 1.5rem; }
        .info-box {
            background: rgba(0,0,0,0.3);
            border-radius: 1rem;
            padding: 1rem;
            margin: 1.5rem 0;
        }
        .info-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: #c4b5fd;
            font-size: 0.85rem;
            margin-bottom: 0.75rem;
        }
        .info-item:last-child { margin-bottom: 0; }
        .btn-get {
            width: 100%;
            background: linear-gradient(135deg, #8b5cf6, #6d28d9);
            border: none;
            padding: 1rem;
            border-radius: 1rem;
            color: white;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        .btn-get:hover { transform: translateY(-2px); filter: brightness(1.05); }
        .btn-get:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
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
        <h2>Nhận Key Kích Hoạt</h2>
        <div class="desc">Hoàn thành bước bên dưới để nhận key</div>
        
        <div class="info-box">
            <div class="info-item">📌 Key có hiệu lực 24 giờ</div>
            <div class="info-item">🔒 Bảo mật tuyệt đối</div>
            <div class="info-item">⚡ Kích hoạt ngay sau khi nhận</div>
        </div>
        
        <button class="btn-get" onclick="generateKey()" id="getKeyBtn">
            🔑 LẤY KEY NGAY
        </button>
    </div>
    
    <script>
        const sessionId = '{{ session_id }}';
        
        async function generateKey() {
            const btn = document.getElementById('getKeyBtn');
            btn.innerHTML = '<span class="loading-spinner"></span> Đang xử lý...';
            btn.disabled = true;
            
            try {
                const response = await fetch('/generate_free_key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Chuyển hướng đến link nhiệm vụ
                    window.location.href = data.link;
                } else {
                    alert('Lỗi: ' + (data.message || 'Không thể tạo link'));
                    btn.innerHTML = '🔑 LẤY KEY NGAY';
                    btn.disabled = false;
                }
            } catch (error) {
                alert('Lỗi kết nối server! Vui lòng thử lại sau.');
                btn.innerHTML = '🔑 LẤY KEY NGAY';
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
    <title>Thành Công - Ping Delay V3</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 500px;
            width: 100%;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(74, 222, 128, 0.3);
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
            background: rgba(74, 222, 128, 0.15);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
        }
        h2 { color: white; font-size: 1.8rem; margin-bottom: 0.5rem; }
        .desc { color: #a1a1aa; margin-bottom: 1.5rem; }
        .key-box {
            background: #0f172a;
            border-radius: 1rem;
            padding: 1.2rem;
            margin: 1.5rem 0;
            border: 1px dashed #4ade80;
        }
        .key-label { font-size: 0.7rem; color: #4ade80; text-transform: uppercase; letter-spacing: 1px; }
        .key-value {
            font-family: monospace;
            font-size: 1.2rem;
            font-weight: 700;
            color: #4ade80;
            word-break: break-all;
            margin: 0.5rem 0;
        }
        .copy-btn {
            background: rgba(74, 222, 128, 0.2);
            border: 1px solid #4ade80;
            padding: 0.5rem 1.2rem;
            border-radius: 2rem;
            color: #4ade80;
            cursor: pointer;
            font-size: 0.8rem;
        }
        .warning {
            font-size: 0.7rem;
            color: #71717a;
            margin: 1rem 0;
        }
        .btn-download {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, #8b5cf6, #6d28d9);
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
            <svg width="48" height="48" fill="none" stroke="#4ade80" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
        </div>
        <h2>Thành Công!</h2>
        <div class="desc">Bạn đã vượt link thành công</div>
        
        <div class="key-box">
            <div class="key-label">🔑 MÃ KÍCH HOẠT CỦA BẠN</div>
            <div class="key-value" id="licenseKey">{{ activation_key }}</div>
            <button class="copy-btn" onclick="copyKey()">📋 Sao chép mã</button>
        </div>
        
        <div class="warning">
            ⏰ Key có hiệu lực trong 24 giờ<br>
            📱 Nhập mã vào ứng dụng Ping Delay V3 để kích hoạt
        </div>
        
        <a href="/download/latest" class="btn-download">
            📲 Tải ứng dụng
            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
        </a>
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
    <title>Lỗi - Ping Delay V3</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 450px;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .error-icon { font-size: 4rem; margin-bottom: 1rem; }
        h2 { color: #f87171; margin-bottom: 0.5rem; }
        p { color: #a1a1aa; margin-bottom: 1.5rem; }
        .btn-back {
            background: #8b5cf6;
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
        <a href="/Getkey.php" class="btn-back">🔄 Thử lại</a>
    </div>
</body>
</html>
"""

# ========== TEMPLATE CHO APP ANDROID (hướng dẫn) ==========
APP_README = """
HƯỚNG DẪN TÍCH HỢP KEY CHO APP ANDROID
=========================================

1. API kiểm tra key:
   POST https://roszmodxqanhno1.onrender.com/api/verify_key
   Body: {"key": "PDV3-XXXX-XXXX"}

2. Response:
   - Thành công: {"status": "success", "message": "✅ Key hợp lệ!"}
   - Hết hạn: {"status": "expired", "message": "Key đã hết hạn!"}
   - Sai key: {"status": "invalid", "message": "Mã Key không chính xác"}

3. Code mẫu cho Android (Kotlin):
   
   suspend fun verifyKey(key: String): Boolean {
       val client = OkHttpClient()
       val body = JSONObject().put("key", key).toString()
       val request = Request.Builder()
           .url("https://roszmodxqanhno1.onrender.com/api/verify_key")
           .post(body.toRequestBody("application/json".toMediaType()))
           .build()
       
       val response = client.newCall(request).await()
       val result = JSONObject(response.body?.string() ?: "{}")
       return result.getBoolean("status") == "success"
   }

4. Lưu key sau khi xác thực thành công vào SharedPreferences
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)