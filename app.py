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
LINK4M_API = "65c47d157fbdff4d79625e57"
BASE_URL = "https://roszmodxqanhno1.onrender.com"  # Link web thật

tasks = {}

def short_link_trafficvn(url):
    """Tạo shortlink TrafficVN từ URL callback"""
    try:
        enc = urllib.parse.quote(url, safe='')
        api = f"https://trafficvn.com/api?api_key={TRAFFICVN_API}&url={enc}&format=json"
        r = requests.get(api, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get('shortenedUrl') or data.get('short_url')
    except:
        pass
    return url

def short_link_link4m(url):
    """Tạo shortlink Link4m từ URL callback"""
    try:
        enc = urllib.parse.quote(url, safe='')
        api = f"https://link4m.co/api-shorten/v2?api={LINK4M_API}&url={enc}"
        r = requests.get(api, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == 'success':
                return data.get('shortenedUrl')
    except:
        pass
    return url

def generate_key():
    p1 = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789') for _ in range(6))
    p2 = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789') for _ in range(4))
    raw = f"BUF-{p1}-{p2}"
    ck = hashlib.md5(raw.encode()).hexdigest()[:2].upper()
    return f"{raw}-{ck}"

# ==================== HTML ====================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BuffTiền - Nhận Key</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Arial;background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .card{max-width:500px;width:100%;background:rgba(15,23,42,0.95);border-radius:24px;padding:32px;text-align:center;border:1px solid #00ff88}
        h1{color:#00ff88;margin-bottom:16px}
        .task-box{background:rgba(0,0,0,0.4);border-radius:16px;padding:16px;margin:16px 0}
        .task-title{color:#00ff88;font-weight:bold;margin-bottom:10px}
        .task-link{word-break:break-all;margin:10px 0}
        .task-link a{color:#00ff88;text-decoration:none;background:rgba(0,255,136,0.1);padding:8px 12px;border-radius:8px;display:inline-block}
        .btn{background:#00ff88;color:#0a0f1a;padding:12px 24px;border-radius:40px;border:none;font-weight:bold;cursor:pointer;width:100%}
        .result{margin-top:16px;padding:12px;border-radius:12px;display:none}
        .result.success{background:rgba(0,255,136,0.2);border:1px solid #00ff88;display:block}
        .result.error{background:rgba(255,68,68,0.2);border:1px solid #ff4444;display:block}
        .warning{font-size:12px;color:#ffaa00;margin-top:16px}
        .footer{font-size:11px;color:#666;margin-top:16px}
        .key-display{font-family:monospace;font-size:18px;margin:10px 0;word-break:break-all}
        .copy-btn{background:rgba(0,255,136,0.2);border:1px solid #00ff88;padding:8px 16px;border-radius:8px;color:#00ff88;cursor:pointer}
    </style>
</head>
<body>
    <div class="card">
        <h1>💰 BuffTiền</h1>
        <p>Hoàn thành 2 nhiệm vụ bên dưới để nhận Key</p>
        
        <div class="task-box">
            <div class="task-title">📌 NHIỆM VỤ 1: TRAFFICVN</div>
            <div class="task-link"><a href="{{ task1_url }}" target="_blank" rel="noopener noreferrer">{{ task1_url }}</a></div>
            <div style="font-size:11px;color:#888">⬆️ Bấm vào link, xem hết quảng cáo</div>
        </div>
        
        <div class="task-box">
            <div class="task-title">📌 NHIỆM VỤ 2: LINK4M</div>
            <div class="task-link"><a href="{{ task2_url }}" target="_blank" rel="noopener noreferrer">{{ task2_url }}</a></div>
            <div style="font-size:11px;color:#888">⬆️ Bấm vào link, xem hết quảng cáo</div>
        </div>
        
        <button class="btn" onclick="getKey()" id="getKeyBtn">🎁 NHẬN KEY</button>
        
        <div class="result" id="result"></div>
        <div class="warning">⚠️ Bấm vào từng link, đợi quảng cáo hiển thị xong, SAU ĐÓ bấm NHẬN KEY</div>
        <div class="footer">📞 @QanhXMod | Zalo: 84798179321</div>
    </div>
    
    <script>
        async function getKey() {
            const btn = document.getElementById('getKeyBtn');
            const result = document.getElementById('result');
            
            btn.disabled = true;
            btn.innerText = '⏳ Đang kiểm tra...';
            result.className = 'result';
            result.innerHTML = '';
            
            try {
                const response = await fetch('/api/getkey/{{ sid }}');
                const data = await response.json();
                
                if (data.key) {
                    result.className = 'result success';
                    result.innerHTML = `
                        ✅ <strong>THÀNH CÔNG!</strong><br>
                        <div class="key-display">🔑 ${data.key}</div>
                        <button class="copy-btn" onclick="copyKey('${data.key}')">📋 Sao chép key</button>
                    `;
                    btn.style.display = 'none';
                } else {
                    result.className = 'result error';
                    result.innerHTML = '❌ CHƯA HOÀN THÀNH! Bạn cần bấm vào 2 link và xem hết quảng cáo.';
                    btn.disabled = false;
                    btn.innerText = '🎁 NHẰN KEY';
                }
            } catch (error) {
                result.className = 'result error';
                result.innerHTML = '❌ Lỗi: ' + error.message;
                btn.disabled = false;
                btn.innerText = '🎁 NHẬN KEY';
            }
        }
        
        function copyKey(key) {
            navigator.clipboard.writeText(key);
            alert('✅ Đã sao chép key: ' + key);
        }
    </script>
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
    
    # Tạo callback URL
    callback1 = f"{BASE_URL}/callback/{sid}/1"
    callback2 = f"{BASE_URL}/callback/{sid}/2"
    
    # Tạo shortlink thật từ TrafficVN và Link4m
    task1_url = short_link_trafficvn(callback1)
    task2_url = short_link_link4m(callback2)
    
    tasks[sid] = {
        'task1_done': False,
        'task2_done': False,
        'created_at': datetime.now().isoformat()
    }
    
    return render_template_string(INDEX_HTML, sid=sid, task1_url=task1_url, task2_url=task2_url)

@app.route('/callback/<sid>/<int:num>')
def callback(sid, num):
    """Callback khi user hoàn thành nhiệm vụ"""
    if sid in tasks:
        if num == 1:
            tasks[sid]['task1_done'] = True
            print(f"[{sid}] Đã hoàn thành task {num}")
        elif num == 2:
            tasks[sid]['task2_done'] = True
            print(f"[{sid}] Đã hoàn thành task {num}")
    
    # Trả về trang thông báo thành công
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Đã xác nhận</title>
        <style>
            body{background:#0a0f1a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Arial}
            .card{text-align:center}
            h2{color:#00ff88}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>✅ ĐÃ XÁC NHẬN!</h2>
            <p>Đóng tab này và quay lại trang chính.</p>
            <script>setTimeout(() => window.close(), 3000);</script>
        </div>
    </body>
    </html>
    """

@app.route('/api/getkey/<sid>')
def api_getkey(sid):
    """API lấy key khi user đã hoàn thành nhiệm vụ"""
    if sid not in tasks:
        return jsonify({'key': None})
    
    task = tasks[sid]
    
    # Nếu đã có key thì trả về
    if task.get('key'):
        return jsonify({'key': task['key']})
    
    # Kiểm tra nếu đã hoàn thành cả 2 nhiệm vụ
    if task.get('task1_done') and task.get('task2_done'):
        key = generate_key()
        task['key'] = key
        tasks[sid] = task
        print(f"[{sid}] Đã cấp key: {key}")
        return jsonify({'key': key})
    
    return jsonify({'key': None})

@app.route('/stats')
def stats():
    total = len([t for t in tasks.values() if t.get('key')])
    return jsonify({'total': total})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)