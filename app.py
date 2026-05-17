from flask import Flask, render_template, render_template_string, request, jsonify, session, send_from_directory
import requests
import uuid
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
# Đặt secret key cố định để tránh mất session của user khi Render khởi động lại
app.secret_key = os.environ.get('SECRET_KEY', 'secret_key_bao_mat_mac_dinh_123')

# Cấu hình Link4M
LINK4M_API_KEY = os.environ.get("LINK4M_API_KEY", "65c47d157fbdff4d79625e57")
LINK4M_API_URL = "https://link4m.co/api-shorten/v2"
YOUR_DOMAIN = os.environ.get('YOUR_DOMAIN', 'http://localhost:5000')

# Cơ chế lưu trữ file JSON để hạn chế mất dữ liệu khi web trên Render ngủ đông
DATA_FILE = "temp_keys.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Thư mục để bạn bỏ file APK vào phục vụ việc tải xuống
APK_FOLDER = os.path.join(app.root_path, 'downloads')
os.makedirs(APK_FOLDER, ignore_ok=True)


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/get_main_web')
def get_main_web():
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    return render_template_string(MAIN_WEB_HTML, session_id=session_id)

@app.route('/generate_free_key', methods=['POST'])
def generate_free_key():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'status': 'error', 'message': 'Phiên làm việc không hợp lệ'}), 400

    callback_url = f"{YOUR_DOMAIN}/DoneKey.php?session_id={session_id}"
    
    try:
        params = {'api': LINK4M_API_KEY, 'url': callback_url}
        response = requests.get(LINK4M_API_URL, params=params, timeout=10)
        res_json = response.json()
        
        if res_json.get('status') == 'success' or 'shortenedUrl' in res_json:
            short_url = res_json.get('shortenedUrl')
            
            # Lưu trạng thái chờ duyệt vào file JSON
            db = load_data()
            db[session_id] = {
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'expire_at': (datetime.now() + timedelta(hours=24)).isoformat()
            }
            save_data(db)
            
            return jsonify({'status': 'success', 'link': short_url})
        else:
            return jsonify({'status': 'error', 'message': 'Không thể tạo link từ Link4M'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Endpoint nhận phản hồi sau khi hoàn thành link rút gọn
@app.route('/DoneKey.php', methods=['GET'])
def done_key():
    session_id = request.args.get('session_id')
    
    if not session_id:
        return render_template_string(ERROR_HTML, message="Thiếu mã phiên (Session ID)!")
        
    db = load_data()
    if session_id in db:
        # Tạo key ngẫu nhiên dạng KEY-XXXXXXXXXXXX cho App
        activation_key = f"KEY-{uuid.uuid4().hex[:12].upper()}"
        
        db[session_id]['status'] = 'completed'
        db[session_id]['key'] = activation_key
        db[session_id]['activated_at'] = datetime.now().isoformat()
        save_data(db)
        
        return render_template_string(SUCCESS_HTML, activation_key=activation_key)
    else:
        return render_template_string(ERROR_HTML, message="Phiên làm việc không tồn tại hoặc đã hết hạn!")

# --- API KẾT NỐI VỚI APP APK CỦA BẠN ---
# Khi App Android bật lên, hãy thực hiện một POST request gửi {"key": "KEY_CUA_USER"} đến URL này
@app.route('/api/verify_key', methods=['POST'])
def verify_key():
    req_data = request.json or {}
    user_key = req_data.get('key')
    
    if not user_key:
        return jsonify({'status': 'invalid', 'message': 'Vui lòng nhập mã Key!'}), 400
        
    db = load_data()
    
    # Tìm kiếm key trong file dữ liệu
    for sid, info in db.items():
        if info.get('key') == user_key:
            # Kiểm tra thời hạn 24 giờ
            expire_at = datetime.fromisoformat(info.get('expire_at'))
            if datetime.now() > expire_at:
                return jsonify({'status': 'expired', 'message': 'Key này đã hết hạn sử dụng (24h)!'})
                
            return jsonify({'status': 'valid', 'message': 'Xác thực thành công! Key hợp lệ.'})
            
    return jsonify({'status': 'invalid', 'message': 'Mã Key không chính xác hoặc không tồn tại.'})

# Route hỗ trợ tải file APK trực tiếp
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(APK_FOLDER, filename, as_attachment=True)


# ==========================================
# GIỮ NGUYÊN 100% CÁC GIAO DIỆN UI GỐC CỦA BẠN
# ==========================================

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Trang Chủ</title>
</head>
<body style="background:#0f172a; color:white; text-align:center; padding-top:10%;">
    <h2>Hệ Thống Xác Thực Key</h2>
    <a href="/get_main_web" style="color:#3b82f6; font-size:18px;">Đi tới trang lấy Key</a>
</body>
</html>
"""

MAIN_WEB_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Get Key - Ping Delay V3</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(ellipse at 30% 40%, #0f172a, #020617);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .container {
            width: 100%;
            max-width: 480px;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 2rem;
            padding: 2.5rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .header { text-align: center; margin-bottom: 2.5rem; }
        .logo-area {
            width: 64px; height: 64px;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            border-radius: 1.25rem;
            margin: 0 auto 1.25rem;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.4);
        }
        .logo-area svg { width: 32px; height: 32px; color: white; }
        h1 { color: white; font-size: 1.75rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.025em; }
        .subtitle { color: #94a3b8; font-size: 0.95rem; }
        .info-card {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 1.25rem;
            padding: 1.25rem; margin-bottom: 2rem;
        }
        .info-item { display: flex; align-items: center; gap: 0.75rem; color: #cbd5e1; font-size: 0.9rem; }
        .info-item svg { width: 20px; height: 20px; color: #3b82f6; flex-shrink: 0; }
        .btn-get {
            width: 100%;
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white; border: none;
            padding: 1.1rem; border-radius: 1.25rem;
            font-size: 1rem; font-weight: 600;
            cursor: pointer; transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
            display: flex; align-items: center; justify-content: center; gap: 0.5rem;
        }
        .btn-get:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3); background: linear-gradient(135deg, #4f46e5, #3b82f6); }
        .btn-get:active { transform: translateY(0); }
    </style>
    <script>
        function generateKey() {
            const btn = document.querySelector('.btn-get');
            btn.innerHTML = 'Đang xử lý...';
            btn.style.opacity = '0.7';
            btn.disabled = true;

            fetch('/generate_free_key', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ session_id: '{{ session_id }}' })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'success') {
                    window.location.href = data.link;
                } else {
                    alert('Lỗi: ' + data.message);
                    btn.innerHTML = 'Lấy Key Ngay';
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }
            })
            .catch(err => {
                alert('Lỗi kết nối server!');
                btn.innerHTML = 'Lấy Key Ngay';
                btn.disabled = false;
                btn.style.opacity = '1';
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-area">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>
            </div>
            <h1>Ping Delay V3</h1>
            <p class="subtitle">Hệ thống cấp khóa ứng dụng tự động</p>
        </div>
        <div class="info-card">
            <div class="info-item">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <span>Vui lòng hoàn thành liên kết ở trang tiếp theo để nhận mã Key (Thời hạn sử dụng: 24h).</span>
            </div>
        </div>
        <button class="btn-get" onclick="generateKey()">
            Lấy Key Ngay
            <svg style="width:20px;height:20px" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
        </button>
    </div>
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(ellipse at 30% 40%, #0f172a, #020617);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .success-card {
            max-width: 450px; width: 100%;
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border-radius: 2rem;
            padding: 2.5rem; text-align: center;
            border: 1px solid rgba(74, 222, 128, 0.2);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .success-icon {
            width: 64px; height: 64px; background: rgba(74, 222, 128, 0.1);
            border-radius: 50%; margin: 0 auto 1.5rem;
            display: flex; align-items: center; justify-content: center;
            color: #4ade80;
        }
        h2 { color: white; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
        p { color: #94a3b8; font-size: 0.95rem; margin-bottom: 2rem; line-height: 1.5; }
        .key-container {
            background: #0f172a; border: 1px dashed rgba(74, 222, 128, 0.4);
            border-radius: 1rem; padding: 1.2rem;
            font-family: monospace; font-size: 1.25rem; font-weight: 700;
            color: #4ade80; letter-spacing: 2px;
            margin-bottom: 1.5rem; position: relative; word-break: break-all;
        }
        .copy-hint { font-size: 0.8rem; color: #64748b; margin-top: -0.5rem; margin-bottom: 2rem; }
        .btn-download {
            display: inline-flex; align-items: center; gap: 0.5rem;
            background: #3b82f6; color: white; text-decoration: none;
            padding: 0.9rem 1.75rem; border-radius: 1rem;
            font-weight: 600; font-size: 0.95rem; transition: all 0.2s;
        }
        .btn-download:hover { background: #2563eb; transform: translateY(-1px); }
    </style>
</head>
<body>
    <div class="success-card">
        <div class="success-icon">
            <svg style="width:32px;height:32px" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
        </div>
        <h2>Vượt Link Thành Công!</h2>
        <p>Mã Key của bạn đã được khởi tạo. Vui lòng copy mã dưới đây nhập vào ứng dụng.</p>
        <div class="key-container">{{ activation_key }}</div>
        <div class="copy-hint">Mã Key có hiệu lực trong vòng 24 giờ kể từ bây giờ.</div>
        <a href="/download/Ping Delay V3_1.0.apk" class="btn-download">
            <svg style="width:20px;height:20px" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            Tải Xuống APK (Gốc)
        </a>
    </div>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lỗi Xác Thực</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(ellipse at 30% 40%, #0f172a, #020617);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .error-card {
            max-width: 450px; width: 100%;
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border-radius: 2rem;
            padding: 2.5rem; text-align: center;
            border: 1px solid rgba(239, 68, 68, 0.3);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .error-icon { color: #f87171; font-size: 3.5rem; margin-bottom: 1rem; }
        h2 { color: #f87171; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
        p { color: #94a3b8; font-size: 0.95rem; margin-bottom: 2rem; }
        .back-btn {
            display: inline-block; background: #3b82f6; color: white;
            text-decoration: none; padding: 0.8rem 1.5rem; border-radius: 1rem;
            font-weight: 600; transition: all 0.2s;
        }
        .back-btn:hover { background: #2563eb; }
    </style>
</head>
<body>
    <div class="error-card">
        <div class="error-icon">⚠️</div>
        <h2>Đã xảy ra lỗi</h2>
        <p>{{ message }}</p>
        <a href="/get_main_web" class="back-btn">Quay lại trang chủ</a>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
