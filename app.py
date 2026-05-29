from flask import Flask, request, jsonify, render_template_string, redirect
import secrets
import hashlib
import requests
import urllib.parse
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ==================== CẤU HÌNH ====================
TRAFFICVN_API = "eef4080ff90f6180b109ecc46a78f33b"
BASE_URL = "https://roszmodxqanhno1.onrender.com"  # ⚠️ THAY URL THẬT CỦA BẠN

tasks = {}

def short_link_trafficvn(url):
    """Tạo shortlink TrafficVN"""
    try:
        enc = urllib.parse.quote(url, safe='')
        api = f"https://trafficvn.com/api?api_key={TRAFFICVN_API}&url={enc}&format=json"
        r = requests.get(api, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get('shortenedUrl') or data.get('short_url')
    except Exception as e:
        print(f"Lỗi TrafficVN: {e}")
    return url

# ==================== HTML ====================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BuffTiền - Hoàn Thành Nhiệm Vụ</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        body {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 500px;
            width: 100%;
            background: rgba(255,255,255,0.95);
            border-radius: 32px;
            padding: 32px 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 {
            font-size: 2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 8px;
        }
        .sub {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .task-box {
            background: #f0f0f0;
            border-radius: 20px;
            padding: 20px;
            margin: 20px 0;
        }
        .task-link {
            background: white;
            padding: 12px;
            border-radius: 12px;
            margin: 15px 0;
            word-break: break-all;
        }
        .task-link a {
            color: #667eea;
            text-decoration: none;
        }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 50px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
        }
        .warning {
            font-size: 12px;
            color: #888;
            margin-top: 20px;
        }
        .success-box {
            background: rgba(16,185,129,0.1);
            border: 1px solid #10b981;
            border-radius: 16px;
            padding: 20px;
            margin-top: 20px;
        }
        .code {
            font-family: monospace;
            font-size: 18px;
            font-weight: bold;
            color: #10b981;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 BuffTiền</h1>
        <div class="sub">Hoàn thành nhiệm vụ bên dưới</div>
        
        <div class="task-box">
            <div style="font-weight:bold; margin-bottom:10px">📌 NHIỆM VỤ: TRAFFICVN</div>
            <div class="task-link">
                <a href="{{ task_url }}" target="_blank">{{ task_url }}</a>
            </div>
            <div style="font-size:12px; color:#888">⬆️ Bấm vào link, xem hết quảng cáo</div>
        </div>
        
        <div class="warning">
            ⚠️ Sau khi bấm link xong, <strong>QUAY LẠI BOT</strong> và dùng lệnh <strong>/verify</strong>
        </div>
        
        <div class="footer" style="margin-top:20px; font-size:11px; color:#888">
            📞 @QanhXMod | Zalo: 84798179321
        </div>
    </div>
</body>
</html>
"""

# ==================== ROUTES ====================
@app.route('/')
def index():
    return redirect('/getkey')

@app.route('/getkey')
def getkey_page():
    sid = secrets.token_hex(16)
    
    # Tạo callback để ghi nhận hoàn thành
    callback_url = f"{BASE_URL}/callback/{sid}"
    task_url = short_link_trafficvn(callback_url)
    
    tasks[sid] = {'completed': False}
    
    return render_template_string(HTML_TEMPLATE, sid=sid, task_url=task_url)

@app.route('/callback/<sid>')
def callback(sid):
    """Callback khi user hoàn thành nhiệm vụ qua shortlink"""
    if sid in tasks:
        tasks[sid]['completed'] = True
        print(f"[{sid}] Đã hoàn thành nhiệm vụ")
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Đã xác nhận</title>
        <style>
            body{background:#0a0f1a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Arial}
            .card{text-align:center}
            h2{color:#10b981}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>✅ ĐÃ HOÀN THÀNH!</h2>
            <p>Đóng tab này và quay lại bot để dùng <strong>/verify</strong></p>
            <script>setTimeout(() => window.close(), 3000);</script>
        </div>
    </body>
    </html>
    """

@app.route('/api/check/<sid>')
def api_check(sid):
    """API để bot kiểm tra trạng thái nhiệm vụ"""
    if sid not in tasks:
        return jsonify({'completed': False})
    return jsonify({'completed': tasks[sid].get('completed', False)})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)