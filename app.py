from flask import Flask, request, jsonify, render_template_string, redirect, session
import requests
import random
import string
from datetime import datetime, timedelta
import os
import json
import hashlib
import secrets
import re
import urllib.parse

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ========== CẤU HÌNH ==========
LINK4M_API_KEY = "65c47d157fbdff4d79625e57"
TRAFFICVN_API_KEY = "eef4080ff90f6180b109ecc46a78f33b"
VUOTNHANH_API_KEY = "e7c716d2-996f-4bdd-bcbf-7653223a400b"
YOUR_DOMAIN = "https://YOUR_RENDER_URL.onrender.com"  # ⚠️ THAY URL CỦA BẠN

KEYS_FILE = "keys.json"
TASKS_FILE = "tasks.json"

def load_json(f, d=None):
    if d is None: d = {}
    if not os.path.exists(f): return d
    try:
        with open(f, 'r') as x: return json.load(x)
    except: return d

def save_json(f, d):
    try:
        with open(f, 'w') as x: json.dump(d, x, indent=2)
        return True
    except: return False

def gen_key():
    p1 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    p2 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    raw = f"BUF-{p1}-{p2}"
    ck = hashlib.md5(raw.encode()).hexdigest()[:2].upper()
    return f"{raw}-{ck}"

def short_link(service, url):
    try:
        enc = urllib.parse.quote(url, safe='')
        if service == 'vuotnhanh':
            api = f"https://vuotnhanh.com/api?api={VUOTNHANH_API_KEY}&url={enc}&format=text"
            r = requests.get(api, timeout=10)
            if r.status_code == 200:
                return r.text.strip()
        elif service == 'trafficvn':
            api = f"https://trafficvn.com/api?api_key={TRAFFICVN_API_KEY}&url={enc}&format=json"
            r = requests.get(api, timeout=10)
            if r.status_code == 200:
                d = r.json()
                return d.get('shortenedUrl') or d.get('short_url') or url
        elif service == 'link4m':
            api = f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={enc}"
            r = requests.get(api, timeout=5)
            if r.status_code == 200:
                d = r.json()
                if d.get('status') == 'success' and d.get('shortenedUrl'):
                    return d.get('shortenedUrl')
    except Exception as e:
        print(f"Lỗi {service}: {e}")
    return url

# ========== TRANG CHỦ ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot BuffTiền - Nhận Key Miễn Phí</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
        .card{max-width:500px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:40px;text-align:center;border:1px solid rgba(0,255,136,0.3);animation:fadeIn 0.6s}
        @keyframes fadeIn{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
        .logo{width:70px;height:70px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:36px}
        h1{font-size:28px;background:linear-gradient(135deg,#fff,#00ff88);background-clip:text;-webkit-background-clip:text;color:transparent}
        .sub{color:#aaa;margin:10px 0 30px;font-size:14px}
        .btn{background:linear-gradient(135deg,#00ff88,#00cc66);border:none;padding:14px 28px;border-radius:40px;color:#0a0f1a;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;transition:0.3s}
        .btn:hover{transform:scale(1.05);box-shadow:0 10px 20px rgba(0,255,136,0.3)}
        .stats{display:flex;justify-content:center;gap:30px;margin-top:30px;padding-top:20px;border-top:1px solid rgba(0,255,136,0.2)}
        .stat-number{font-size:24px;font-weight:700;color:#00ff88}
        .stat-label{font-size:11px;color:#666}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">💰</div>
        <h1>Bot BuffTiền</h1>
        <div class="sub">Hoàn thành nhiệm vụ → Nhận Key Premium</div>
        <a href="/start" class="btn">🎁 BẮT ĐẦU NHẬN KEY</a>
        <div class="stats">
            <div><div class="stat-number" id="totalKeys">0</div><div class="stat-label">Key đã cấp</div></div>
            <div><div class="stat-number">3</div><div class="stat-label">Bước</div></div>
            <div><div class="stat-number">24h</div><div class="stat-label">Hạn key</div></div>
        </div>
    </div>
    <script>fetch('/api/stats').then(r=>r.json()).then(d=>document.getElementById('totalKeys').innerText=d.total_keys||0)</script>
</body>
</html>
"""

# ========== TRANG NHIỆM VỤ ==========
TASK_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bước {{ step }}/3 - Bot BuffTiền</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
        .card{max-width:550px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:32px;border:1px solid rgba(0,255,136,0.3);animation:fadeIn 0.4s}
        @keyframes fadeIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
        .step-badge{background:rgba(0,255,136,0.15);padding:6px 16px;border-radius:100px;font-size:12px;color:#00ff88;display:inline-block;margin-bottom:20px}
        h2{font-size:24px;color:#fff;margin-bottom:10px}
        .desc{color:#aaa;font-size:14px;margin-bottom:20px}
        .task-box{background:rgba(0,0,0,0.4);border-radius:16px;padding:20px;margin:20px 0;border:1px dashed rgba(0,255,136,0.3)}
        .task-link{word-break:break-all;margin-bottom:15px}
        .task-link a{color:#00ff88;text-decoration:none;font-size:14px}
        .verify-input{width:100%;padding:12px;border-radius:12px;border:1px solid #333;background:#0a0f1a;color:#fff;margin:15px 0;font-size:14px}
        .verify-input:focus{outline:none;border-color:#00ff88}
        .btn-group{display:flex;gap:12px}
        .btn-check{flex:1;background:linear-gradient(135deg,#00ff88,#00cc66);border:none;padding:12px;border-radius:12px;color:#0a0f1a;font-weight:600;cursor:pointer}
        .btn-back{flex:1;background:rgba(255,255,255,0.1);border:1px solid rgba(0,255,136,0.5);padding:12px;border-radius:12px;color:#00ff88;font-weight:600;text-align:center;text-decoration:none}
        .message{padding:10px;border-radius:10px;margin-top:15px;font-size:13px;display:none}
        .message.show{display:block}
        .message.success{background:rgba(0,255,136,0.2);color:#00ff88;border:1px solid #00ff88}
        .message.error{background:rgba(255,68,68,0.2);color:#ff4444;border:1px solid #ff4444}
        .warning{font-size:12px;color:#ffaa00;margin-top:10px}
    </style>
</head>
<body>
    <div class="card">
        <div class="step-badge">📌 BƯỚC {{ step }}/3</div>
        <h2>{{ title }}</h2>
        <div class="desc">{{ desc }}</div>
        
        <div class="task-box">
            <div class="task-link">🔗 <a href="{{ task_url }}" target="_blank" id="taskLink">{{ task_url }}</a></div>
            <input type="text" class="verify-input" id="verifyCode" placeholder="Nhập mã xác nhận từ trang nhiệm vụ...">
            <div class="btn-group">
                <a href="{{ back_url }}" class="btn-back">🔙 Quay lại</a>
                <button class="btn-check" onclick="verify()">✅ XÁC NHẬN</button>
            </div>
            <div class="warning">⚠️ Sau khi bấm vào link, đợi 10-15 giây và sao chép MÃ HIỂN THỊ</div>
        </div>
        <div id="msg" class="message"></div>
    </div>
    <script>
        async function verify() {
            const code = document.getElementById('verifyCode').value.trim();
            if(!code) {
                showMsg('Vui lòng nhập mã xác nhận!', 'error');
                return;
            }
            const btn = document.querySelector('.btn-check');
            const original = btn.innerHTML;
            btn.innerHTML = '⏳ Đang xác nhận...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({sid: '{{ sid }}', step: {{ step }}, code: code})
                });
                const data = await res.json();
                if(data.status === 'success') {
                    showMsg('✅ Xác nhận thành công! Chuyển tiếp...', 'success');
                    setTimeout(() => { window.location.href = data.next_url; }, 1500);
                } else {
                    showMsg(data.message || 'Mã không đúng! Thử lại.', 'error');
                }
            } catch(e) {
                showMsg('Lỗi kết nối, thử lại!', 'error');
            }
            btn.innerHTML = original;
            btn.disabled = false;
        }
        function showMsg(msg, type) {
            const el = document.getElementById('msg');
            el.innerHTML = msg;
            el.className = `message ${type} show`;
            setTimeout(() => el.classList.remove('show'), 3000);
        }
    </script>
</body>
</html>
"""

# ========== TRANG HOÀN THÀNH ==========
SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thành công - Bot BuffTiền</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
        .card{max-width:500px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:40px;text-align:center;border:1px solid rgba(0,255,136,0.3);animation:bounce 0.6s}
        @keyframes bounce{0%{opacity:0;transform:scale(0.8)}50%{transform:scale(1.05)}100%{transform:scale(1)}}
        .success-icon{width:80px;height:80px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:45px}
        h2{font-size:28px;color:#00ff88;margin-bottom:10px}
        .key-box{background:linear-gradient(135deg,#0f172a,#1a1a2e);border-radius:20px;padding:20px;margin:20px 0;border:1px dashed #00ff88}
        .key-value{font-family:monospace;font-size:18px;font-weight:700;color:#00ff88;word-break:break-all}
        .btn{background:linear-gradient(135deg,#00ff88,#00cc66);border:none;padding:12px 24px;border-radius:40px;color:#0a0f1a;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;margin:5px}
        .warning{font-size:12px;color:#666;margin-top:20px}
    </style>
</head>
<body>
    <div class="card">
        <div class="success-icon">🎉</div>
        <h2>CHÚC MỪNG!</h2>
        <div class="desc">Bạn đã hoàn thành tất cả nhiệm vụ</div>
        <div class="key-box">
            <div style="font-size:11px;color:#00ff88;margin-bottom:10px">🔑 KEY CỦA BẠN</div>
            <div class="key-value" id="licenseKey">{{ key }}</div>
        </div>
        <button class="btn" onclick="copyKey()">📋 Sao chép key</button>
        <a href="/" class="btn" style="background:rgba(0,255,136,0.2)">🏠 Về trang chủ</a>
        <div class="warning">⏰ Key có hiệu lực trong 24 giờ</div>
    </div>
    <script>
        function copyKey() {
            const k = document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(k);
            alert('✅ Đã sao chép key!\\nKey: ' + k);
        }
    </script>
</body>
</html>
"""

# ========== ROUTES ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/start')
def start():
    sid = secrets.token_hex(16)
    tasks = load_json(TASKS_FILE, {})
    
    # Tạo link cho từng bước (VuotNhanh -> TrafficVN -> Link4m)
    step1_url = short_link('vuotnhanh', f"{YOUR_DOMAIN}/api/task/{sid}/1")
    step2_url = short_link('trafficvn', f"{YOUR_DOMAIN}/api/task/{sid}/2")
    step3_url = short_link('link4m', f"{YOUR_DOMAIN}/api/task/{sid}/3")
    
    tasks[sid] = {
        'step': 1,
        'completed': [False, False, False],
        'step1_code': None, 'step2_code': None, 'step3_code': None,
        'created_at': datetime.now().isoformat()
    }
    save_json(TASKS_FILE, tasks)
    
    return redirect(f'/task/{sid}/1')

@app.route('/task/<sid>/<int:step>')
def task_page(sid, step):
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks:
        return "Phiên không hợp lệ!", 404
    
    task = tasks[sid]
    if step > 3:
        if task.get('key'):
            return render_template_string(SUCCESS_HTML, key=task['key'])
        return redirect(f'/task/{sid}/1')
    
    # Tạo mã xác nhận ngẫu nhiên cho bước này
    code_key = f'step{step}_code'
    if not task.get(code_key):
        task[code_key] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        save_json(TASKS_FILE, tasks)
    
    # Tạo link nhiệm vụ (dạng web giả lập hiển thị mã)
    task_link = f"{YOUR_DOMAIN}/api/task/{sid}/{step}"
    
    config = {
        1: {'title': '🚀 BƯỚC 1: VUOTNHANH', 'desc': 'Hoàn thành nhiệm vụ trên VuotNhanh.com'},
        2: {'title': '📈 BƯỚC 2: TRAFFICVN', 'desc': 'Hoàn thành nhiệm vụ trên TrafficVN.com'},
        3: {'title': '🔗 BƯỚC 3: LINK4M', 'desc': 'Hoàn thành nhiệm vụ cuối cùng'}
    }
    cfg = config.get(step)
    
    back_url = f'/task/{sid}/{step-1}' if step > 1 else '/start'
    
    return render_template_string(TASK_HTML, 
                                  step=step, 
                                  title=cfg['title'], 
                                  desc=cfg['desc'],
                                  task_url=task_link,
                                  sid=sid,
                                  back_url=back_url)

@app.route('/api/task/<sid>/<int:step>')
def api_task(sid, step):
    """Trang hiển thị mã xác nhận - người dùng copy mã này"""
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks:
        return "Phiên không hợp lệ!", 404
    
    task = tasks[sid]
    code_key = f'step{step}_code'
    code = task.get(code_key, 'ERROR')
    
    # Tạo link rút gọn thực tế để người dùng click (VD: link đến nội dung gì đó)
    # Ở đây tạo link ảo để họ thấy mã
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Xác nhận nhiệm vụ - Bot BuffTiền</title>
        <style>
            body{{font-family:Arial;background:#0a0f1a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;text-align:center}}
            .code{{font-size:40px;font-weight:bold;background:#00ff88;color:#0a0f1a;padding:20px;border-radius:20px;letter-spacing:5px;margin:20px}}
        </style>
    </head>
    <body>
        <div>
            <h2>✅ NHIỆM VỤ BƯỚC {step}</h2>
            <p>Mã xác nhận của bạn:</p>
            <div class="code">{code}</div>
            <p>📋 Sao chép mã này và quay lại trang trước để dán vào ô xác nhận</p>
            <p><small>Mã có hiệu lực trong 10 phút</small></p>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.json
    sid = data.get('sid')
    step = data.get('step')
    code = data.get('code', '').strip().upper()
    
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks:
        return jsonify({'status': 'error', 'message': 'Phiên không hợp lệ!'})
    
    task = tasks[sid]
    code_key = f'step{step}_code'
    expected_code = task.get(code_key, '')
    
    if code != expected_code:
        return jsonify({'status': 'error', 'message': 'Mã xác nhận không đúng!'})
    
    # Đánh dấu bước đã hoàn thành
    task['completed'][step-1] = True
    
    if step < 3:
        task['step'] = step + 1
        save_json(TASKS_FILE, tasks)
        return jsonify({'status': 'success', 'next_url': f'/task/{sid}/{step+1}'})
    else:
        # Hoàn thành cả 3 bước, tạo key
        key = gen_key()
        task['key'] = key
        task['expires'] = (datetime.now() + timedelta(hours=24)).isoformat()
        save_json(TASKS_FILE, tasks)
        
        # Lưu key vào keys.json
        keys = load_json(KEYS_FILE, {})
        keys[key] = {'expires': task['expires'], 'used': False, 'created_at': datetime.now().isoformat()}
        save_json(KEYS_FILE, keys)
        
        return jsonify({'status': 'success', 'next_url': f'/task/{sid}/4'})

@app.route('/api/stats')
def api_stats():
    keys = load_json(KEYS_FILE, {})
    return jsonify({'total_keys': len(keys)})

# ========== API CHO BOT TELEGRAM ==========
@app.route('/api/check_user', methods=['POST'])
def api_check_user():
    """Bot gọi để check user đã hoàn thành nhiệm vụ chưa"""
    data = request.json
    sid = data.get('sid')
    
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks:
        return jsonify({'status': 'error', 'message': 'SID không tồn tại'})
    
    task = tasks[sid]
    if task.get('key'):
        return jsonify({'status': 'success', 'key': task['key'], 'expires': task.get('expires')})
    elif all(task['completed']):
        return jsonify({'status': 'pending', 'message': 'Đã hoàn thành, đang tạo key...'})
    else:
        completed_steps = sum(task['completed'])
        return jsonify({'status': 'incomplete', 'completed': completed_steps, 'total': 3})

@app.route('/api/get_key', methods=['POST'])
def api_get_key():
    """Bot gọi để lấy key nếu đã hoàn thành"""
    data = request.json
    sid = data.get('sid')
    
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks:
        return jsonify({'status': 'error', 'message': 'SID không tồn tại'})
    
    task = tasks[sid]
    if task.get('key'):
        return jsonify({'status': 'success', 'key': task['key']})
    elif all(task['completed']):
        key = gen_key()
        task['key'] = key
        task['expires'] = (datetime.now() + timedelta(hours=24)).isoformat()
        save_json(TASKS_FILE, tasks)
        
        keys = load_json(KEYS_FILE, {})
        keys[key] = {'expires': task['expires'], 'used': False}
        save_json(KEYS_FILE, keys)
        
        return jsonify({'status': 'success', 'key': key})
    else:
        return jsonify({'status': 'incomplete', 'message': 'Chưa hoàn thành nhiệm vụ'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)