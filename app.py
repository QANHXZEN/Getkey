from flask import Flask, request, jsonify, render_template_string, redirect, make_response
import requests
import random
import string
from datetime import datetime, timedelta
import os
import json
import hashlib
import secrets
import time
from functools import wraps
import re
import urllib.parse
import threading

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ========== CẤU HÌNH ==========
LINK4M_API_KEY = "65c47d157fbdff4d79625e57"
YEUMONEY_API_KEY = "4e3bbf63ff3ac2f780f246675412f35c3f31946a74f195992dbaf2a6d6c26eee"
VUOTNHANH_API_KEY = "e7c716d2-996f-4bdd-bcbf-7653223a400b"
YOUR_DOMAIN = "https://roszmodxqanhno1.onrender.com"
TELEGRAM_BOT_TOKEN = "8448578289:AAH2Pp6s3V1Le-cV5I1Qc-gFKQzTDBMXnvA"
TELEGRAM_CHAT_ID = "8588555065"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Dragon@2024"

KEYS_FILE = "keys.json"
TASKS_FILE = "tasks.json"
BLACKLIST_FILE = "blacklist.json"
EARNINGS_FILE = "earnings.json"

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

def send_tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg[:4000], 'parse_mode': 'HTML'}, timeout=5)
    except: pass

def gen_key():
    p1 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    p2 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    raw = f"DRP-{p1}-{p2}"
    ck = hashlib.md5(raw.encode()).hexdigest()[:2].upper()
    return f"{raw}-{ck}"

def verify_key(key):
    if not key or len(key) < 15: return False
    m = re.match(r'^DRP-[A-Z0-9]{6}-[A-Z0-9]{4}-([A-Z0-9]{2})$', key)
    if not m: return False
    return m.group(1) == hashlib.md5(key[:-3].encode()).hexdigest()[:2].upper()

def get_fp():
    return hashlib.sha256(f"{request.remote_addr}|{request.headers.get('User-Agent', 'unknown')}".encode()).hexdigest()[:32]

def gen_sid():
    return secrets.token_hex(16)

def is_blocked(ip, fp):
    b = load_json(BLACKLIST_FILE, {'ips': [], 'fps': []})
    return ip in b.get('ips', []) or fp in b.get('fps', [])

def block(ip, fp, reason):
    b = load_json(BLACKLIST_FILE, {'ips': [], 'fps': []})
    if ip and ip not in b['ips']: b['ips'].append(ip)
    if fp and fp not in b['fps']: b['fps'].append(fp)
    save_json(BLACKLIST_FILE, b)
    send_tg(f"🚫 BLACKLIST: {ip} | {reason}")

def check_rate_limit(act, id):
    r = load_json('rate.json', {})
    now = time.time()
    k = f"{act}:{id}"
    if k not in r:
        r[k] = {'c': 1, 't': now}
        save_json('rate.json', r)
        return True
    if now - r[k]['t'] > 60:
        r[k] = {'c': 1, 't': now}
        save_json('rate.json', r)
        return True
    if r[k]['c'] >= 30:
        return False
    r[k]['c'] += 1
    save_json('rate.json', r)
    return True

def short_link(service, url):
    try:
        enc = urllib.parse.quote(url, safe='')
        if service == 'yeumoney':
            r = requests.get(f"https://yeumoney.com/QL_api.php?token={YEUMONEY_API_KEY}&url={enc}&format=json", timeout=5)
            if r.status_code == 200:
                d = r.json()
                return d.get('shortenedUrl') or d.get('shortUrl') or url
        elif service == 'link4m':
            r = requests.get(f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={enc}", timeout=5)
            if r.status_code == 200:
                d = r.json()
                if d.get('status') == 'success' and d.get('shortenedUrl'):
                    return d.get('shortenedUrl')
        else:
            r = requests.get(f"https://vuotnhanh.com/api?token={VUOTNHANH_API_KEY}&url={enc}&format=json", timeout=5)
            if r.status_code == 200:
                d = r.json()
                return d.get('shortenedUrl') or d.get('short_url') or d.get('url') or url
    except: pass
    return url

def create_key(expires_hours=24, note=""):
    key = gen_key()
    keys = load_json(KEYS_FILE, {})
    keys[key] = {'expires': (datetime.now() + timedelta(hours=expires_hours)).isoformat(), 'used': False, 'created': datetime.now().isoformat(), 'note': note}
    save_json(KEYS_FILE, keys)
    return key

def use_key(key, fp, ip):
    keys = load_json(KEYS_FILE, {})
    if key not in keys: return False, "Key không tồn tại"
    info = keys[key]
    if datetime.now() > datetime.fromisoformat(info['expires']): return False, "Key hết hạn"
    if info.get('used'): return False, "Key đã dùng"
    info['used'] = True
    info['used_at'] = datetime.now().isoformat()
    info['used_by'] = fp
    info['used_ip'] = ip
    save_json(KEYS_FILE, keys)
    send_tg(f"✅ KEY ĐÃ DÙNG: {key} | IP: {ip}")
    return True, "OK"

def create_task(sid, fp, ip):
    tasks = load_json(TASKS_FILE, {})
    cb1 = f"{YOUR_DOMAIN}/cb/{sid}/1"
    cb2 = f"{YOUR_DOMAIN}/cb/{sid}/2"
    cb3 = f"{YOUR_DOMAIN}/cb/{sid}/3"
    tasks[sid] = {
        'step': 1, 's1': False, 's2': False, 's3': False,
        'url1': short_link('vuotnhanh', cb1),
        'url2': short_link('yeumoney', cb2),
        'url3': short_link('link4m', cb3),
        'fp': fp, 'ip': ip, 'created': datetime.now().isoformat()
    }
    save_json(TASKS_FILE, tasks)
    return tasks[sid]

def get_task(sid):
    return load_json(TASKS_FILE, {}).get(sid)

def complete_step(sid, step):
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks: return False
    t = tasks[sid]
    f = f's{step}'
    if t.get(f): return False
    t[f] = True
    t['step'] = step + 1
    save_json(TASKS_FILE, tasks)
    return True

def finish_task(sid):
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks: return None
    t = tasks[sid]
    if not t.get('s3'): return None
    if t.get('key'): return t['key']
    key = create_key(24, f"Session {sid}")
    t['key'] = key
    save_json(TASKS_FILE, tasks)
    send_tg(f"🔑 KEY MỚI: {key} | IP: {t.get('ip', 'unknown')}")
    return key

def update_earnings(service, amount, link, sid, ip, fp):
    earn = load_json(EARNINGS_FILE, {})
    today = datetime.now().strftime('%Y-%m-%d')
    if 'daily' not in earn: earn['daily'] = {}
    if today not in earn['daily']: earn['daily'][today] = {}
    earn['daily'][today][service] = earn['daily'][today].get(service, 0) + amount
    earn['total'] = earn.get('total', 0) + amount
    if 'trans' not in earn: earn['trans'] = []
    earn['trans'].append({'time': datetime.now().isoformat(), 'service': service, 'amount': amount, 'link': link, 'sid': sid})
    if len(earn['trans']) > 500: earn['trans'] = earn['trans'][-500:]
    save_json(EARNINGS_FILE, earn)
    send_tg(f"💰 +${amount} từ {service}\n🔗 {link[:60]}...\n📊 {YOUR_DOMAIN}/earning/{sid}")

def clean_tasks():
    tasks = load_json(TASKS_FILE, {})
    expired = [sid for sid, t in tasks.items() if datetime.now() - datetime.fromisoformat(t['created']) > timedelta(hours=1)]
    for sid in expired: del tasks[sid]
    if expired: save_json(TASKS_FILE, tasks)

def clean_keys():
    keys = load_json(KEYS_FILE, {})
    expired = [k for k, v in keys.items() if datetime.now() > datetime.fromisoformat(v['expires'])]
    for k in expired: del keys[k]
    if expired: save_json(KEYS_FILE, keys)

# ========== HTML TEMPLATES ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>DRAGON PINGX PREMIUM</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a 0%,#0f0f1a 50%,#0a0a0a 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;position:relative;overflow:hidden}.star{position:fixed;width:2px;height:2px;background:#fff;border-radius:50%;animation:shoot 4s linear infinite;z-index:1}@keyframes shoot{0%{transform:translateX(0)translateY(0);opacity:0}10%{opacity:1}20%{opacity:1}30%{opacity:0}100%{transform:translateX(-200px)translateY(200px);opacity:0}}.magic-particle{position:fixed;width:4px;height:4px;background:linear-gradient(135deg,#b000ff,#ff44ff);border-radius:50%;opacity:0;animation:floatMagic 6s infinite;z-index:1}@keyframes floatMagic{0%{transform:translateY(100vh) rotate(0deg);opacity:0}20%{opacity:0.8}80%{opacity:0.6}100%{transform:translateY(-100px) rotate(360deg);opacity:0}}.glow{position:fixed;width:400px;height:400px;background:radial-gradient(circle,rgba(176,0,255,0.1),transparent);border-radius:50%;pointer-events:none;z-index:1;transition:all 0.3s ease}.hero{text-align:center;max-width:650px;animation:fadeUp 0.8s;z-index:2}@keyframes fadeUp{from{opacity:0;transform:translateY(50px)}to{opacity:1;transform:translateY(0)}}.badge{display:inline-block;background:rgba(176,0,255,0.15);backdrop-filter:blur(10px);padding:8px 24px;border-radius:100px;font-size:12px;font-weight:600;color:#b000ff;border:1px solid rgba(176,0,255,0.4);margin-bottom:30px;animation:pulse 2s infinite}@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(176,0,255,0.4)}50%{box-shadow:0 0 0 20px rgba(176,0,255,0)}}h1{font-size:60px;font-weight:800;background:linear-gradient(135deg,#fff,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px;animation:gradient 4s infinite}@keyframes gradient{0%{background-position:0%50%}50%{background-position:100%50%}100%{background-position:0%50%}}.sub{font-size:16px;color:#aaa;margin-bottom:30px;line-height:1.6}.btn{background:linear-gradient(135deg,#b000ff,#ff44ff);border:none;padding:16px 45px;font-size:16px;font-weight:600;color:#fff;border-radius:60px;display:inline-flex;align-items:center;gap:10px;text-decoration:none;box-shadow:0 5px 20px rgba(176,0,255,0.4);transition:0.3s;position:relative;overflow:hidden}.btn::before{content:'';position:absolute;top:50%;left:50%;width:0;height:0;border-radius:50%;background:rgba(255,255,255,0.3);transform:translate(-50%,-50%);transition:width 0.6s,height 0.6s}.btn:hover::before{width:400px;height:400px}.btn:hover{transform:translateY(-5px) scale(1.05);box-shadow:0 15px 40px rgba(176,0,255,0.6)}.stats{display:flex;justify-content:center;gap:40px;margin-top:50px;padding-top:30px;border-top:1px solid rgba(176,0,255,0.2)}.stat-number{font-size:28px;font-weight:700;background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent}.stat-label{font-size:12px;color:#888;margin-top:5px}</style></head>
<body><div id="g1" class="glow" style="top:-150px;left:-150px"></div><div id="g2" class="glow" style="bottom:-150px;right:-150px"></div><div class="hero"><div class="badge">✨ DRAGON PINGX PREMIUM | CHÍNH THỨC ✨</div><h1>DRAGON PINGX</h1><div class="sub">⚡ Hệ thống kích hoạt bản quyền tự động ⚡<br>🔒 Bảo mật tuyệt đối - 🚀 Tốc độ thần tốc</div><a href="/getkey" class="btn">🎁 NHẬN KEY MIỄN PHÍ →</a><div class="stats"><div><div class="stat-number">24/7</div><div class="stat-label">Hỗ trợ</div></div><div><div class="stat-number">2.5K+</div><div class="stat-label">Người dùng</div></div><div><div class="stat-number">100%</div><div class="stat-label">Bảo mật</div></div></div></div><script>for(let i=0;i<50;i++){let s=document.createElement('div');s.className='star';s.style.top=Math.random()*100+'%';s.style.left=Math.random()*100+'%';s.style.animationDelay=Math.random()*8+'s';document.body.appendChild(s)}for(let i=0;i<60;i++){let p=document.createElement('div');p.className='magic-particle';p.style.left=Math.random()*100+'%';p.style.animationDelay=Math.random()*8+'s';document.body.appendChild(p)}document.addEventListener('mousemove',function(e){let g1=document.getElementById('g1');let g2=document.getElementById('g2');if(g1)g1.style.transform=`translate(${e.clientX*0.05}px,${e.clientY*0.05}px)`;if(g2)g2.style.transform=`translate(${-e.clientX*0.03}px,${-e.clientY*0.03}px)`})</script></body></html>
"""

STEP_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Bước {{ step }} - DRAGON PINGX</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;position:relative}.bg-effect{position:fixed;top:0;left:0;width:100%;height:100%;overflow:hidden;z-index:0}.bg-circle{position:absolute;border-radius:50%;background:rgba(176,0,255,0.05);animation:float 20s infinite}@keyframes float{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-50px) rotate(180deg)}}.card{position:relative;z-index:2;max-width:550px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:32px;border:1px solid rgba(176,0,255,0.3);text-align:center;animation:fadeScale 0.6s}@keyframes fadeScale{from{opacity:0;transform:scale(0.9)}to{opacity:1;transform:scale(1)}}.step-icon{width:80px;height:80px;background:linear-gradient(135deg,#b000ff,#ff44ff);border-radius:2rem;display:flex;align-items:center;justify-content:center;margin:0 auto 1.5rem;animation:rotate3D 4s infinite}@keyframes rotate3D{0%{transform:rotateY(0deg)}50%{transform:rotateY(180deg)}100%{transform:rotateY(360deg)}}.step-badge{background:linear-gradient(135deg,#b000ff,#ff44ff);padding:6px 20px;border-radius:100px;font-size:12px;font-weight:600;color:#fff;display:inline-block;margin-bottom:20px}h2{font-size:28px;background:linear-gradient(135deg,#fff,#b000ff);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px}.desc{color:#aaa;margin-bottom:20px}.info{background:rgba(255,193,7,0.1);border:1px solid rgba(255,193,7,0.3);border-radius:12px;padding:12px;margin:15px 0;font-size:13px;color:#ffc107}.task-link{background:rgba(0,0,0,0.4);border-radius:16px;padding:16px;margin:20px 0;word-break:break-all;border:1px dashed rgba(176,0,255,0.3);transition:0.3s}.task-link:hover{border-color:#b000ff;background:rgba(176,0,255,0.05)}.task-link a{color:#b000ff;text-decoration:none;font-size:14px}.btn-group{display:flex;gap:16px;margin-top:24px}.btn-continue{flex:1;background:linear-gradient(135deg,#00cc66,#00ff88);border:none;padding:14px;border-radius:16px;color:#fff;font-weight:600;cursor:pointer;transition:0.3s;position:relative;overflow:hidden}.btn-continue::before{content:'';position:absolute;top:50%;left:50%;width:0;height:0;border-radius:50%;background:rgba(255,255,255,0.3);transform:translate(-50%,-50%);transition:width 0.6s,height 0.6s}.btn-continue:hover::before{width:300px;height:300px}.btn-continue:hover{transform:translateY(-2px);box-shadow:0 10px 20px rgba(0,255,136,0.3)}.btn-back{flex:1;background:rgba(176,0,255,0.2);border:1px solid rgba(176,0,255,0.5);padding:14px;border-radius:16px;color:#b000ff;font-weight:600;text-decoration:none;display:inline-block;text-align:center;transition:0.3s}.btn-back:hover{background:rgba(176,0,255,0.4)}.loading{display:inline-block;width:18px;height:18px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.warning{font-size:13px;color:#f87171;margin-top:16px;padding:10px;background:rgba(239,68,68,0.1);border-radius:10px;display:none}.warning.show{display:block;animation:shake 0.5s}@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-5px)}75%{transform:translateX(5px)}}</style></head>
<body><div class="bg-effect" id="bgEffect"></div><div class="card"><div class="step-icon"><svg width="40" height="40" fill="none" stroke="white" viewBox="0 0 24 24">{% if step == 1 %}<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>{% elif step == 2 %}<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>{% else %}<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>{% endif %}</svg></div><div class="step-badge">📌 BƯỚC {{ step }}/3</div><h2>{{ title }}</h2><div class="desc">{{ desc }}</div><div class="info">💰 Hoàn thành nhiệm vụ để nhận KEY MIỄN PHÍ!</div><div class="task-link"><div style="font-size:12px;color:#666;margin-bottom:8px;">🔗 Link nhiệm vụ của bạn:</div><a href="{{ url }}" target="_blank" id="taskLink">{{ url }}</a></div><div class="btn-group"><a href="{{ back_url }}" class="btn-back">🔙 Quay lại</a><button class="btn-continue" onclick="check()" id="continueBtn">✅ Tiếp tục</button></div><div class="warning" id="warningMsg">⚠️ Bạn chưa hoàn thành nhiệm vụ!</div></div><script>for(let i=0;i<15;i++){let c=document.createElement('div');c.className='bg-circle';let s=100+Math.random()*200;c.style.width=s+'px';c.style.height=s+'px';c.style.left=Math.random()*100+'%';c.style.top=Math.random()*100+'%';c.style.animationDelay=Math.random()*20+'s';document.getElementById('bgEffect').appendChild(c)}let sid="{{ sid }}",step={{ step }},checking=false;async function check(){if(checking)return;checking=true;const btn=document.getElementById('continueBtn'),original=btn.innerHTML;btn.innerHTML='<span class="loading"></span> Đang kiểm tra...';btn.disabled=true;document.getElementById('warningMsg').classList.remove('show');try{const res=await fetch(`/api/check/${sid}/${step}`),data=await res.json();if(data.completed){window.location.href=data.next}else{document.getElementById('warningMsg').classList.add('show');btn.innerHTML=original;btn.disabled=false;checking=false;window.open(document.getElementById('taskLink').href,'_blank')}}catch(e){document.getElementById('warningMsg').innerHTML='⚠️ Lỗi, thử lại!';document.getElementById('warningMsg').classList.add('show');btn.innerHTML=original;btn.disabled=false;checking=false}}window.open(document.getElementById('taskLink').href,'_blank');setInterval(()=>{if(!checking&&window.location.pathname.includes('/step'))check()},5000);</script></body></html>
"""

FINAL_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Thành Công - DRAGON PINGX</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;position:relative;overflow:hidden}.confetti{position:fixed;width:10px;height:10px;position:absolute;animation:fall 3s linear forwards;z-index:9999}@keyframes fall{0%{transform:translateY(-100vh) rotate(0deg)}100%{transform:translateY(100vh) rotate(360deg);opacity:0}}.card{max-width:520px;width:100%;background:rgba(15,23,42,0.95);backdrop-filter:blur(20px);border-radius:32px;padding:40px;text-align:center;border:1px solid rgba(176,0,255,0.4);animation:bounce 0.8s;z-index:2}@keyframes bounce{0%{opacity:0;transform:scale(0.7)}50%{transform:scale(1.05)}100%{transform:scale(1)}}.success-icon{width:80px;height:80px;background:linear-gradient(135deg,#00ff88,#00cc66);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;animation:pulseSuccess 1s infinite}@keyframes pulseSuccess{0%,100%{transform:scale(1);box-shadow:0 0 0 0 rgba(0,255,136,0.4)}50%{transform:scale(1.05);box-shadow:0 0 0 20px rgba(0,255,136,0)}}h2{font-size:32px;background:linear-gradient(135deg,#fff,#00ff88);background-clip:text;-webkit-background-clip:text;color:transparent;margin-bottom:10px}.key-box{background:linear-gradient(135deg,#0f172a,#1a1a2e);border-radius:20px;padding:24px;margin:24px 0;border:1px dashed #b000ff;transition:0.3s}.key-box:hover{border-color:#ff44ff;box-shadow:0 0 20px rgba(176,0,255,0.3)}.key-value{font-family:monospace;font-size:20px;font-weight:700;background:linear-gradient(135deg,#b000ff,#ff44ff);background-clip:text;-webkit-background-clip:text;color:transparent;word-break:break-all;margin:12px 0;cursor:pointer}.copy-btn{background:linear-gradient(135deg,#b000ff,#ff44ff);border:none;padding:12px 32px;border-radius:40px;color:#fff;cursor:pointer;font-weight:600;position:relative;overflow:hidden}.copy-btn::before{content:'';position:absolute;top:50%;left:50%;width:0;height:0;border-radius:50%;background:rgba(255,255,255,0.3);transform:translate(-50%,-50%);transition:width 0.6s,height 0.6s}.copy-btn:hover::before{width:300px;height:300px}.copy-btn:hover{transform:translateY(-3px);box-shadow:0 10px 20px rgba(176,0,255,0.4)}.btn-back{display:inline-block;background:rgba(176,0,255,0.2);text-decoration:none;color:#b000ff;padding:10px 24px;border-radius:40px;margin-top:16px;transition:0.3s}.btn-back:hover{background:rgba(176,0,255,0.4)}.warning{font-size:12px;color:#666;margin:16px 0}</style></head>
<body><div class="card"><div class="success-icon"><svg width="48" height="48" fill="none" stroke="white" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg></div><h2>🎉 THÀNH CÔNG!</h2><div class="desc">Bạn đã hoàn thành tất cả nhiệm vụ</div><div class="key-box"><div style="font-size:11px;color:#b000ff;letter-spacing:2px;margin-bottom:10px">🔑 KEY KÍCH HOẠT</div><div class="key-value" id="licenseKey" onclick="copyKey()">{{ key }}</div><button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button></div><div class="warning">⏰ Key có hiệu lực trong 24 giờ<br>📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM</div><a href="/" class="btn-back">🏠 Về trang chủ</a></div><script>const colors=['#b000ff','#ff44ff','#00ff88','#ffaa00'];for(let i=0;i<150;i++){let c=document.createElement('div');c.className='confetti';c.style.left=Math.random()*100+'%';c.style.animationDelay=Math.random()*2+'s';c.style.backgroundColor=colors[Math.floor(Math.random()*colors.length)];c.style.width=(5+Math.random()*10)+'px';c.style.height=(5+Math.random()*10)+'px';document.body.appendChild(c);setTimeout(()=>c.remove(),5000)}function copyKey(){const k=document.getElementById('licenseKey').innerText;navigator.clipboard.writeText(k);alert('✅ Đã sao chép key!\\nKey: '+k)}</script></body></html>
"""

ERROR_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Lỗi</title><style>body{background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Arial}.card{background:#1a1a2e;padding:40px;border-radius:20px;text-align:center}.btn{background:#b000ff;color:#fff;padding:10px 20px;border-radius:10px;text-decoration:none;display:inline-block;margin-top:20px}</style></head><body><div class="card"><div class="error-icon">⚠️</div><h2>Đã xảy ra lỗi</h2><p>{{ msg }}</p><a href="/getkey" class="btn">Thử lại</a></div></body></html>
"""

EARNING_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Thu nhập</title><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:40px}.card{background:#1a1a2e;border-radius:16px;padding:20px;margin-bottom:20px}.total{font-size:32px;color:#00ff88}table{width:100%;border-collapse:collapse}th,td{padding:10px;text-align:left;border-bottom:1px solid #333}</style></head><body><h1>💰 Thu nhập của bạn</h1><div class="card"><div class="total">${{ "%.4f"|format(total) }} USD</div></div><div class="card"><table><th>Thời gian</th><th>Dịch vụ</th><th>Tiền</th><th>Link</th></tr>{% for e in earnings %}<tr><td>{{ e.time[:16] }}</td><td>{{ e.service }}</td><td>${{ "%.4f"|format(e.amount) }}</td><td><a href="{{ e.link }}" target="_blank" style="color:#b000ff">Xem</a></td></tr>{% endfor %}</table></div><a href="/" style="color:#b000ff">← Về trang chủ</a></body></html>
"""

ADMIN_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin Panel</title><style>body{background:#0a0a0a;color:#fff;font-family:Arial;padding:40px}.container{max-width:1200px;margin:0 auto}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:30px}.stat{background:#1a1a2e;border-radius:16px;padding:20px;text-align:center}.stat .value{font-size:32px;color:#b000ff}.card{background:#1a1a2e;border-radius:16px;padding:20px;margin-bottom:20px}table{width:100%;border-collapse:collapse}th,td{padding:10px;text-align:left;border-bottom:1px solid #333}input,button{padding:10px;border-radius:8px;border:none}input{background:#333;color:#fff}button{background:#b000ff;color:#fff;cursor:pointer}.logout{position:fixed;top:20px;right:20px;background:#ef4444;color:#fff;padding:8px 16px;border-radius:8px;text-decoration:none}</style></head><body><a href="/admin/logout" class="logout">🚪 Đăng xuất</a><div class="container"><h1>🔐 ADMIN PANEL</h1><div class="stats"><div class="stat"><h3>📊 Tổng key</h3><div class="value">{{ stats.total_keys }}</div></div><div class="stat"><h3>✅ Key đã dùng</h3><div class="value">{{ stats.total_used }}</div></div><div class="stat"><h3>👥 Người dùng</h3><div class="value">{{ stats.total_users }}</div></div><div class="stat"><h3>💰 Thu nhập</h3><div class="value">${{ "%.2f"|format(earnings.total) }}</div></div></div><div class="card"><h2>🔑 Tạo key mới</h2><form method="POST" action="/admin/create_key"><input type="text" name="note" placeholder="Ghi chú"><button type="submit">➕ Tạo</button></form></div><div class="card"><h2>🚫 Blacklist IP</h2><form method="POST" action="/admin/blacklist"><input type="text" name="ip" placeholder="IP cần chặn"><button type="submit">🚫 Thêm</button></form><table style="margin-top:15px"><tr><th>IP</th><th>Hành động</th></tr>{% for ip in blacklist.ips %}<tr><td>{{ ip }}</td><td><a href="/admin/unban?ip={{ ip }}" style="color:#f87171">Xóa</a></td></tr>{% endfor %}</table></div><div class="card"><h2>📋 Key gần đây</h2><table><th>Key</th><th>Trạng thái</th><th>Hết hạn</th></table>{% for k in keys %}<tr><td><code>{{ k.key }}</code></td><td>{% if k.used %}✅ Đã dùng{% else %}🟢 Còn{% endif %}</td><td>{{ k.expires[:16] }}</td></tr>{% endfor %}</table></div></div></body></html>
"""

# ========== ROUTES ==========
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    fp = get_fp()
    ip = request.remote_addr
    if is_blocked(ip, fp):
        return render_template_string(ERROR_HTML, msg="Truy cập bị chặn!")
    if not check_rate_limit('getkey', fp):
        block(ip, fp, "Rate limit")
        return render_template_string(ERROR_HTML, msg="Quá nhiều yêu cầu!")
    sid = gen_sid()
    create_task(sid, fp, ip)
    send_tg(f"👤 NGƯỜI DÙNG MỚI | IP: {ip}")
    return redirect(f'/step/{sid}/1')

@app.route('/step/<sid>/<int:s>')
def step_page(sid, s):
    task = get_task(sid)
    if not task:
        return render_template_string(ERROR_HTML, msg="Phiên không hợp lệ!")
    if task.get('fp') != get_fp():
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!")
    cfg = {
        1: {'title': '🚀 BƯỚC 1: VƯỢT NHANH', 'desc': 'Hoàn thành nhiệm vụ trên Vuotnhanh.com', 'url': task.get('url1', '#'), 'back': '/getkey'},
        2: {'title': '💰 BƯỚC 2: YEUMONEY', 'desc': 'Hoàn thành nhiệm vụ trên Yeumoney.com', 'url': task.get('url2', '#'), 'back': f'/step/{sid}/1'},
        3: {'title': '🔗 BƯỚC 3: LINK4M', 'desc': 'Hoàn thành nhiệm vụ cuối cùng', 'url': task.get('url3', '#'), 'back': f'/step/{sid}/2'}
    }
    c = cfg.get(s)
    if not c:
        return render_template_string(ERROR_HTML, msg="Bước không hợp lệ!")
    return render_template_string(STEP_HTML, step=s, title=c['title'], desc=c['desc'], url=c['url'], sid=sid, back_url=c['back'])

@app.route('/cb/<sid>/<int:s>')
def callback(sid, s):
    tasks = load_json(TASKS_FILE, {})
    if sid not in tasks:
        return "Session not found", 404
    task = tasks[sid]
    fp = get_fp()
    if task.get('fp') != fp:
        return "Invalid fingerprint", 403
    if s == 1 and not task.get('s1'):
        task['s1'] = True
        task['step'] = 2
        save_json(TASKS_FILE, tasks)
        update_earnings('vuotnhanh', 0.0005, task.get('url1', ''), sid, task.get('ip', 'unknown'), fp)
    elif s == 2 and not task.get('s2'):
        task['s2'] = True
        task['step'] = 3
        save_json(TASKS_FILE, tasks)
        update_earnings('yeumoney', 0.001, task.get('url2', ''), sid, task.get('ip', 'unknown'), fp)
    elif s == 3 and not task.get('s3'):
        task['s3'] = True
        key = create_key(24, f"Session {sid}")
        task['key'] = key
        save_json(TASKS_FILE, tasks)
        update_earnings('link4m', 0.002, task.get('url3', ''), sid, task.get('ip', 'unknown'), fp)
        send_tg(f"🔑 KEY MỚI: {key} | IP: {task.get('ip', 'unknown')}")
    return "OK"

@app.route('/api/check/<sid>/<int:s>')
def check(sid, s):
    task = get_task(sid)
    if not task:
        return jsonify({'completed': False})
    if task.get('fp') != get_fp():
        return jsonify({'completed': False})
    if s == 1 and task.get('s1'):
        return jsonify({'completed': True, 'next': f'/step/{sid}/2'})
    elif s == 2 and task.get('s2'):
        return jsonify({'completed': True, 'next': f'/step/{sid}/3'})
    elif s == 3 and task.get('s3'):
        if task.get('key'):
            return jsonify({'completed': True, 'next': f'/final/{sid}'})
    return jsonify({'completed': False})

@app.route('/final/<sid>')
def final(sid):
    task = get_task(sid)
    if not task:
        return render_template_string(ERROR_HTML, msg="Phiên không hợp lệ!")
    if task.get('fp') != get_fp():
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!")
    key = task.get('key')
    if not key:
        return render_template_string(ERROR_HTML, msg="Chưa có key!")
    return render_template_string(FINAL_HTML, key=key)

@app.route('/earning/<sid>')
def earning(sid):
    task = get_task(sid)
    if not task:
        return render_template_string(ERROR_HTML, msg="Phiên không hợp lệ!")
    if task.get('fp') != get_fp():
        return render_template_string(ERROR_HTML, msg="Truy cập trái phép!")
    earn = load_json(EARNINGS_FILE, {})
    trans = [t for t in earn.get('trans', []) if t.get('sid') == sid]
    total = sum(t.get('amount', 0) for t in trans)
    return render_template_string(EARNING_HTML, earnings=trans, total=total)

@app.route('/api/verify', methods=['POST'])
def verify():
    fp = get_fp()
    ip = request.remote_addr
    if is_blocked(ip, fp):
        return jsonify({'status': 'error', 'message': 'Bị chặn'}), 403
    if not check_rate_limit('verify', fp):
        block(ip, fp, "Verify rate limit")
        return jsonify({'status': 'error', 'message': 'Quá nhiều lần thử!'}), 429
    data = request.json
    key = data.get('key', '').strip().upper()
    if not key:
        return jsonify({'status': 'error', 'message': 'Nhập key!'})
    if not verify_key(key):
        return jsonify({'status': 'invalid', 'message': 'Key không hợp lệ!'})
    admin_keys = ["QANHNO1CRACKER", "DRAGONLOCUT"]
    if key in admin_keys:
        return jsonify({'status': 'success', 'message': 'Kích hoạt thành công!'})
    success, msg = use_key(key, fp, ip)
    if success:
        return jsonify({'status': 'success', 'message': 'Key hợp lệ!'})
    return jsonify({'status': 'error', 'message': msg})

@app.route('/api/stats')
def api_stats():
    keys = load_json(KEYS_FILE, {})
    earn = load_json(EARNINGS_FILE, {})
    return jsonify({'total_keys': len(keys), 'total_used': sum(1 for k in keys.values() if k.get('used')), 'earnings_usd': earn.get('total', 0)})

# ========== ADMIN ==========
def admin_auth(f):
    @wraps(f)
    def dec(*a, **k):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin"'}))
        return f(*a, **k)
    return dec

@app.route('/admin')
@admin_auth
def admin():
    stats = {'total_keys': len(load_json(KEYS_FILE, {})), 'total_used': sum(1 for k in load_json(KEYS_FILE, {}).values() if k.get('used')), 'total_users': len(load_json(TASKS_FILE, {}))}
    earn = load_json(EARNINGS_FILE, {})
    blacklist = load_json(BLACKLIST_FILE, {'ips': []})
    keys = [{'key': k, **v} for k, v in load_json(KEYS_FILE, {}).items()][-50:]
    return render_template_string(ADMIN_HTML, stats=stats, earnings=earn, blacklist=blacklist, keys=keys)

@app.route('/admin/create_key', methods=['POST'])
@admin_auth
def admin_create():
    note = request.form.get('note', '')
    key = create_key(720, note)
    send_tg(f"👑 Admin tạo key: {key}")
    return redirect('/admin')

@app.route('/admin/blacklist', methods=['POST'])
@admin_auth
def admin_blacklist():
    ip = request.form.get('ip', '')
    if ip:
        block(ip, '', 'Admin add')
    return redirect('/admin')

@app.route('/admin/unban')
@admin_auth
def admin_unban():
    ip = request.args.get('ip', '')
    if ip:
        b = load_json(BLACKLIST_FILE, {'ips': []})
        if ip in b['ips']:
            b['ips'].remove(ip)
            save_json(BLACKLIST_FILE, b)
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    return make_response(('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Admin"'}))

# ========== CLEANUP ==========
def schedule_cleanup():
    def cleanup():
        while True:
            time.sleep(3600)
            clean_tasks()
            clean_keys()
    threading.Thread(target=cleanup, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    schedule_cleanup()
    app.run(host='0.0.0.0', port=port, debug=False)