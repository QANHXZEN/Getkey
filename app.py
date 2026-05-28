from flask import Flask, request, jsonify, render_template_string, redirect, session
import requests
import random
import string
import secrets
import hashlib
import urllib.parse
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ==================== CẤU HÌNH ====================
VUOTNHANH_API = "e7c716d2-996f-4bdd-bcbf-7653223a400b"
TRAFFICVN_API = "eef4080ff90f6180b109ecc46a78f33b"
LINK4M_API = "65c47d157fbdff4d79625e57"

# Lưu task tạm (có thể dùng database thay thế)
tasks = {}

# ==================== HÀM ====================
def short_link(service, url):
    try:
        enc = urllib.parse.quote(url, safe='')
        if service == 'vuotnhanh':
            api = f"https://vuotnhanh.com/api?api={VUOTNHANH_API}&url={enc}&format=text"
            resp = requests.get(api, timeout=10)
            if resp.status_code == 200:
                return resp.text.strip()
        elif service == 'trafficvn':
            api = f"https://trafficvn.com/api?api_key={TRAFFICVN_API}&url={enc}&format=json"
            resp = requests.get(api, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('shortenedUrl') or data.get('short_url')
        elif service == 'link4m':
            api = f"https://link4m.co/api-shorten/v2?api={LINK4M_API}&url={enc}"
            resp = requests.get(api, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    return data.get('shortenedUrl')
    except Exception as e:
        print(f"Lỗi {service}: {e}")
    return url

def generate_key():
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
    <title>Bot BuffTiền - Nhận Key Free</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
        .card{max-width:500px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:40px;text-align:center;border:1px solid rgba(0,255,136,0.3)}
        .logo{width:70px;height:70px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:36px}
        h1{font-size:28px;background:linear-gradient(135deg,#fff,#00ff88);background-clip:text;-webkit-background-clip:text;color:transparent}
        .sub{color:#aaa;margin:10px 0 30px}
        .btn{background:linear-gradient(135deg,#00ff88,#00cc66);border:none;padding:14px 28px;border-radius:40px;color:#0a0f1a;font-weight:600;text-decoration:none;display:inline-block;transition:0.3s}
        .btn:hover{transform:scale(1.05)}
        .stats{display:flex;justify-content:center;gap:30px;margin-top:30px;padding-top:20px;border-top:1px solid rgba(0,255,136,0.2)}
        .stat-number{font-size:24px;font-weight:700;color:#00ff88}
        .stat-label{font-size:11px;color:#666}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">💰</div>
        <h1>Bot BuffTiền</h1>
        <div class="sub">Hoàn thành 3 bước → Nhận Key Premium</div>
        <a href="/getkey" class="btn">🎁 BẮT ĐẦU NHẬN KEY</a>
        <div class="stats">
            <div><div class="stat-number" id="totalKeys">0</div><div class="stat-label">Key đã cấp</div></div>
            <div><div class="stat-number">3</div><div class="stat-label">Bước</div></div>
            <div><div class="stat-number">24h</div><div class="stat-label">Hạn key</div></div>
        </div>
    </div>
    <script>fetch('/stats').then(r=>r.json()).then(d=>document.getElementById('totalKeys').innerText=d.total||0)</script>
</body>
</html>
"""

STEP_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bước {{ step }}/3 - Bot BuffTiền</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .card{max-width:550px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:32px;border:1px solid rgba(0,255,136,0.3);text-align:center}
        .step-badge{background:rgba(0,255,136,0.15);padding:6px 16px;border-radius:100px;font-size:12px;color:#00ff88;display:inline-block;margin-bottom:20px}
        h2{font-size:24px;color:#fff;margin-bottom:10px}
        .desc{color:#aaa;margin-bottom:20px}
        .task-box{background:rgba(0,0,0,0.4);border-radius:16px;padding:20px;margin:20px 0}
        .task-link{word-break:break-all;margin-bottom:15px}
        .task-link a{color:#00ff88;text-decoration:none;font-size:14px}
        .btn-next{background:linear-gradient(135deg,#00ff88,#00cc66);border:none;padding:14px 24px;border-radius:40px;color:#0a0f1a;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block}
        .loading{display:inline-block;width:18px;height:18px;border:2px solid #fff;border-top-color:#00ff88;border-radius:50%;animation:spin 0.6s linear}
        @keyframes spin{to{transform:rotate(360deg)}}
        .warning{font-size:12px;color:#ffaa00;margin-top:15px}
    </style>
</head>
<body>
    <div class="card">
        <div class="step-badge">📌 BƯỚC {{ step }}/3</div>
        <h2>{{ title }}</h2>
        <div class="desc">{{ desc }}</div>
        <div class="task-box">
            <div class="task-link">🔗 <a href="{{ task_url }}" target="_blank" id="taskLink">{{ task_url }}</a></div>
            <button class="btn-next" onclick="checkComplete()" id="nextBtn">✅ TIẾP TỤC</button>
            <div class="warning">⚠️ Bấm vào link trên, đợi 10 giây, sau đó bấm TIẾP TỤC</div>
        </div>
    </div>
    <script>
        let checking = false;
        async function checkComplete() {
            if(checking) return;
            checking = true;
            const btn = document.getElementById('nextBtn');
            const original = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Đang kiểm tra...';
            btn.disabled = true;
            try {
                const res = await fetch('/api/check/{{ sid }}/{{ step }}');
                const data = await res.json();
                if(data.completed) {
                    window.location.href = data.next;
                } else {
                    alert('❌ Bạn chưa hoàn thành bước này! Hãy bấm vào link và đợi 10 giây.');
                    btn.innerHTML = original;
                    btn.disabled = false;
                    checking = false;
                }
            } catch(e) {
                alert('Lỗi: ' + e.message);
                btn.innerHTML = original;
                btn.disabled = false;
                checking = false;
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
    <title>Thành công - Bot BuffTiền</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0a0f1a,#0f1525);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
        .card{max-width:500px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:40px;text-align:center;border:1px solid rgba(0,255,136,0.3)}
        .success-icon{width:80px;height:80px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:45px}
        h2{font-size:28px;color:#00ff88}
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
            <div style="font-size:11px;color:#00ff88">🔑 KEY CỦA BẠN</div>
            <div class="key-value" id="keyValue">{{ key }}</div>
        </div>
        <button class="btn" onclick="copyKey()">📋 Sao chép key</button>
        <a href="/" class="btn" style="background:rgba(0,255,136,0.2)">🏠 Về trang chủ</a>
        <div class="warning">⏰ Key có hiệu lực 24 giờ</div>
    </div>
    <script>
        function copyKey() {
            const key = document.getElementById('keyValue').innerText;
            navigator.clipboard.writeText(key);
            alert('✅ Đã sao chép: ' + key);
        }
    </script>
</body>
</html>
"""

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/stats')
def stats():
    return jsonify({'total': len([t for t in tasks.values() if t.get('key')])})

@app.route('/getkey')
def getkey():
    sid = secrets.token_hex(16)
    
    # Tạo link cho 3 bước (VuotNhanh → TrafficVN → Link4m)
    step1_url = short_link('vuotnhanh', f"{request.host_url}api/callback/{sid}/1")
    step2_url = short_link('trafficvn', f"{request.host_url}api/callback/{sid}/2")
    step3_url = short_link('link4m', f"{request.host_url}api/callback/{sid}/3")
    
    tasks[sid] = {
        'step': 1,
        'completed': [False, False, False],
        'step1_url': step1_url,
        'step2_url': step2_url,
        'step3_url': step3_url,
        'created_at': datetime.now().isoformat()
    }
    
    return redirect(f'/step/{sid}/1')

@app.route('/step/<sid>/<int:step>')
def step_page(sid, step):
    if sid not in tasks:
        return "Phiên không hợp lệ!", 404
    
    task = tasks[sid]
    
    config = {
        1: {'title': '🚀 BƯỚC 1: VUOTNHANH', 'desc': 'Bấm vào link bên dưới, đợi 10 giây', 'url': task['step1_url']},
        2: {'title': '📈 BƯỚC 2: TRAFFICVN', 'desc': 'Bấm vào link bên dưới, đợi 10 giây', 'url': task['step2_url']},
        3: {'title': '🔗 BƯỚC 3: LINK4M', 'desc': 'Bấm vào link cuối cùng, đợi 10 giây', 'url': task['step3_url']}
    }
    
    cfg = config.get(step)
    if not cfg:
        return redirect(f'/success/{sid}')
    
    return render_template_string(STEP_HTML, step=step, title=cfg['title'], desc=cfg['desc'], task_url=cfg['url'], sid=sid)

@app.route('/api/callback/<sid>/<int:step>')
def api_callback(sid, step):
    """Callback khi user bấm vào shortlink"""
    if sid not in tasks:
        return "Session not found", 404
    
    task = tasks[sid]
    task['completed'][step-1] = True
    tasks[sid] = task
    
    # Hiển thị trang thông báo thành công cho bước
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta http-equiv="refresh" content="2;url=/step/{sid}/{step+1 if step<3 else 'success'}"><title>Đã xác nhận</title></head>
    <body style="background:#0a0f1a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh">
        <div style="text-align:center">
            <h2>✅ ĐÃ XÁC NHẬN BƯỚC {step}</h2>
            <p>Đang chuyển tiếp...</p>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/check/<sid>/<int:step>')
def api_check(sid, step):
    if sid not in tasks:
        return jsonify({'completed': False})
    
    task = tasks[sid]
    completed = task['completed'][step-1]
    
    if completed and step < 3:
        return jsonify({'completed': True, 'next': f'/step/{sid}/{step+1}'})
    elif completed and step == 3:
        # Tạo key
        key = generate_key()
        task['key'] = key
        tasks[sid] = task
        return jsonify({'completed': True, 'next': f'/success/{sid}'})
    else:
        return jsonify({'completed': False})

@app.route('/success/<sid>')
def success(sid):
    if sid not in tasks or not tasks[sid].get('key'):
        return redirect('/')
    
    key = tasks[sid]['key']
    return render_template_string(SUCCESS_HTML, key=key)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)