from flask import Flask, request, jsonify, render_template_string, redirect
import secrets
import hashlib
import requests
import urllib.parse

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ==================== CẤU HÌNH ====================
TRAFFICVN_API = "eef4080ff90f6180b109ecc46a78f33b"
LINK4M_API = "65c47d157fbdff4d79625e57"
BASE_URL = "https://roszmodxqanhno1.onrender.com"  # ⚠️ THAY URL THẬT CỦA BẠN

# Lưu task tạm (nên dùng database nếu có nhiều user)
tasks = {}

# ==================== HÀM ====================
def short_link(service, url):
    """Tạo shortlink từ URL"""
    try:
        enc = urllib.parse.quote(url, safe='')
        if service == 'trafficvn':
            api = f"https://trafficvn.com/api?api_key={TRAFFICVN_API}&url={enc}&format=json"
            r = requests.get(api, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return data.get('shortenedUrl') or data.get('short_url')
        elif service == 'link4m':
            api = f"https://link4m.co/api-shorten/v2?api={LINK4M_API}&url={enc}"
            r = requests.get(api, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('status') == 'success':
                    return data.get('shortenedUrl')
    except Exception as e:
        print(f"Lỗi {service}: {e}")
    return url

def generate_key():
    """Tạo key định dạng BUF-XXXXXX-XXXX-XX"""
    p1 = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789') for _ in range(6))
    p2 = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789') for _ in range(4))
    raw = f"BUF-{p1}-{p2}"
    ck = hashlib.md5(raw.encode()).hexdigest()[:2].upper()
    return f"{raw}-{ck}"

# ==================== HTML TEMPLATES ====================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BuffTiền - Nhận Key Miễn Phí</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0f1a 0%, #0f1525 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .card {
            max-width: 550px;
            width: 100%;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 32px;
            text-align: center;
            border: 1px solid rgba(0, 255, 136, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .logo {
            font-size: 48px;
            margin-bottom: 16px;
        }
        h1 {
            font-size: 28px;
            background: linear-gradient(135deg, #fff, #00ff88);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 8px;
        }
        .sub {
            color: #aaa;
            font-size: 14px;
            margin-bottom: 24px;
        }
        .task-box {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 16px;
            padding: 20px;
            margin: 20px 0;
            border: 1px dashed rgba(0, 255, 136, 0.3);
        }
        .task-title {
            color: #00ff88;
            font-size: 14px;
            margin-bottom: 12px;
            font-weight: bold;
        }
        .task-link {
            word-break: break-all;
            margin: 12px 0;
        }
        .task-link a {
            color: #00ff88;
            text-decoration: none;
            font-size: 13px;
            background: rgba(0, 255, 136, 0.1);
            padding: 8px 12px;
            border-radius: 8px;
            display: inline-block;
        }
        .btn {
            background: linear-gradient(135deg, #00ff88, #00cc66);
            border: none;
            padding: 14px 28px;
            border-radius: 40px;
            color: #0a0f1a;
            font-weight: bold;
            cursor: pointer;
            font-size: 16px;
            transition: 0.3s;
            width: 100%;
        }
        .btn:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 12px;
            display: none;
        }
        .result.success {
            background: rgba(0, 255, 136, 0.2);
            border: 1px solid #00ff88;
            display: block;
        }
        .result.error {
            background: rgba(255, 68, 68, 0.2);
            border: 1px solid #ff4444;
            display: block;
        }
        .key-display {
            font-family: monospace;
            font-size: 18px;
            font-weight: bold;
            color: #00ff88;
            word-break: break-all;
            margin: 10px 0;
        }
        .copy-btn {
            background: rgba(0, 255, 136, 0.2);
            border: 1px solid #00ff88;
            padding: 8px 16px;
            border-radius: 8px;
            color: #00ff88;
            cursor: pointer;
            margin-top: 10px;
        }
        .warning {
            font-size: 12px;
            color: #ffaa00;
            margin-top: 16px;
        }
        .footer {
            margin-top: 24px;
            font-size: 11px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">💰</div>
        <h1>BuffTiền</h1>
        <div class="sub">Hoàn thành 2 nhiệm vụ bên dưới để nhận Key</div>
        
        <div class="task-box">
            <div class="task-title">📌 NHIỆM VỤ 1: TRAFFICVN</div>
            <div class="task-link"><a href="{{ task1_url }}" target="_blank" rel="noopener noreferrer">{{ task1_url }}</a></div>
        </div>
        
        <div class="task-box">
            <div class="task-title">📌 NHIỆM VỤ 2: LINK4M</div>
            <div class="task-link"><a href="{{ task2_url }}" target="_blank" rel="noopener noreferrer">{{ task2_url }}</a></div>
        </div>
        
        <button class="btn" onclick="getKey()" id="getKeyBtn">🎁 NHẬN KEY</button>
        
        <div class="result" id="result"></div>
        <div class="warning">⚠️ Bấm vào từng link, xem hết quảng cáo, sau đó bấm NHẬN KEY</div>
        <div class="footer">📞 @QanhXMod | Zalo: 84798179321</div>
    </div>
    
    <script>
        let isProcessing = false;
        
        async function getKey() {
            if (isProcessing) return;
            isProcessing = true;
            
            const btn = document.getElementById('getKeyBtn');
            const resultDiv = document.getElementById('result');
            const originalText = btn.innerText;
            
            btn.disabled = true;
            btn.innerText = '⏳ Đang kiểm tra...';
            resultDiv.className = 'result';
            resultDiv.innerHTML = '';
            
            try {
                const response = await fetch('/api/getkey/{{ sid }}');
                const data = await response.json();
                
                if (data.key) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = `
                        <div style="text-align:center">
                            ✅ <strong>THÀNH CÔNG!</strong><br>
                            <div class="key-display">🔑 ${data.key}</div>
                            <button class="copy-btn" onclick="copyKey('${data.key}')">📋 Sao chép key</button>
                        </div>
                    `;
                    btn.style.display = 'none';
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `
                        ❌ <strong>CHƯA HOÀN THÀNH!</strong><br>
                        Bạn cần bấm vào 2 link và xem hết quảng cáo trước.
                    `;
                    btn.disabled = false;
                    btn.innerText = originalText;
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `❌ Lỗi: ${error.message}`;
                btn.disabled = false;
                btn.innerText = originalText;
            }
            
            isProcessing = false;
        }
        
        function copyKey(key) {
            navigator.clipboard.writeText(key);
            alert('✅ Đã sao chép key: ' + key);
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
    <title>Thành công - BuffTiền</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif}
        .card{background:rgba(15,23,42,0.95);backdrop-filter:blur(10px);border-radius:24px;padding:40px;text-align:center;border:1px solid rgba(0,255,136,0.3);max-width:500px}
        h2{color:#00ff88;margin-bottom:16px}
        .key{font-family:monospace;font-size:20px;background:rgba(0,0,0,0.4);padding:15px;border-radius:12px;margin:20px 0;word-break:break-all;color:#00ff88}
        .btn{background:linear-gradient(135deg,#00ff88,#00cc66);border:none;padding:12px 24px;border-radius:40px;color:#0a0f1a;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block}
        .footer{margin-top:24px;font-size:11px;color:#666}
    </style>
</head>
<body>
    <div class="card">
        <h2>🎉 CHÚC MỪNG!</h2>
        <p>Bạn đã hoàn thành nhiệm vụ</p>
        <div class="key">🔑 {{ key }}</div>
        <button class="btn" onclick="copyKey()">📋 Sao chép key</button>
        <div class="footer">📞 @QanhXMod | Zalo: 84798179321</div>
    </div>
    <script>
        function copyKey() {
            navigator.clipboard.writeText('{{ key }}');
            alert('✅ Đã sao chép key!');
        }
    </script>
</body>
</html>
"""

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey_page():
    sid = secrets.token_hex(16)
    
    # Tạo link callback cho mỗi nhiệm vụ
    callback1 = f"{BASE_URL}/callback/{sid}/1"
    callback2 = f"{BASE_URL}/callback/{sid}/2"
    
    # Tạo shortlink: TrafficVN -> callback1, Link4m -> callback2
    task1_url = short_link('trafficvn', callback1)
    task2_url = short_link('link4m', callback2)
    
    tasks[sid] = {
        'task1_done': False,
        'task2_done': False,
        'key': None,
        'created_at': datetime.now().isoformat()
    }
    
    return render_template_string(INDEX_HTML, sid=sid, task1_url=task1_url, task2_url=task2_url)

@app.route('/callback/<sid>/<int:num>')
def callback(sid, num):
    """Callback được gọi khi user vượt qua shortlink thành công"""
    if sid in tasks:
        if num == 1:
            tasks[sid]['task1_done'] = True
        elif num == 2:
            tasks[sid]['task2_done'] = True
    
    # Trả về trang thông báo (sẽ tự đóng)
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Đã xác nhận</title></head>
    <body style="background:#0a0f1a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh">
        <div style="text-align:center">
            <h2>✅ ĐÃ GHI NHẬN!</h2>
            <p>Đóng tab này và quay lại trang chính.</p>
            <script>setTimeout(() => window.close(), 3000);</script>
        </div>
    </body>
    </html>
    """

@app.route('/api/getkey/<sid>')
def api_getkey(sid):
    """API để web gọi lấy key"""
    if sid not in tasks:
        return jsonify({'key': None, 'message': 'Phiên không hợp lệ!'})
    
    task = tasks[sid]
    
    # Nếu đã có key thì trả về
    if task.get('key'):
        return jsonify({'key': task['key']})
    
    # Kiểm tra nếu cả 2 nhiệm vụ đều hoàn thành
    if task.get('task1_done') and task.get('task2_done'):
        key = generate_key()
        task['key'] = key
        tasks[sid] = task
        return jsonify({'key': key})
    
    return jsonify({'key': None, 'message': 'Chưa hoàn thành nhiệm vụ!'})

@app.route('/stats')
def stats():
    """Thống kê số key đã cấp"""
    total = len([t for t in tasks.values() if t.get('key')])
    return jsonify({'total': total})

from datetime import datetime

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)