from flask import Flask, request, jsonify, render_template_string
import requests
import random
import string
from datetime import datetime, timedelta
import os
import json
import uuid
import hashlib

app = Flask(__name__)
app.secret_key = os.urandom(24)

LINK4M_API_KEY = os.environ.get("LINK4M_API_KEY", "65c47d157fbdff4d79625e57")
LINK4M_API_URL = "https://link4m.co/api-shorten/v2"
YOUR_DOMAIN = "https://roszmodxqanhno1.onrender.com"

DATA_FILE = "keys.json"

def load_keys():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_keys(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def generate_dragon_key():
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=6))
    part2 = ''.join(random.choices(chars, k=4))
    return f"DRP-{part1}-{part2}"

ADMIN_KEYS = ["QanhNo1Cracker", "Dragonlocut", "DRAGONLOCUT"]

# Lưu session với timeout
sessions = {}

def clean_expired_sessions():
    now = datetime.now()
    expired = []
    for sid, data in sessions.items():
        created = datetime.fromisoformat(data.get('created_at', '2024-01-01T00:00:00'))
        if now - created > timedelta(minutes=10):
            expired.append(sid)
    for sid in expired:
        sessions.pop(sid, None)

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
            background: linear-gradient(135deg, #0a0a0a 0%, #0f0f1a 50%, #0a0a0a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            position: relative;
            overflow-x: hidden;
        }
        .particle {
            position: fixed;
            width: 4px;
            height: 4px;
            background: #b000ff;
            border-radius: 50%;
            opacity: 0;
            animation: float 8s infinite;
        }
        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 0.8; }
            90% { opacity: 0.5; }
            100% { transform: translateY(-100px) rotate(360deg); opacity: 0; }
        }
        .hero {
            text-align: center;
            max-width: 600px;
            animation: fadeInUp 0.8s ease;
            position: relative;
            z-index: 2;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .badge {
            display: inline-block;
            background: rgba(176,0,255,0.15);
            backdrop-filter: blur(10px);
            padding: 0.5rem 1.5rem;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            color: #b000ff;
            border: 1px solid rgba(176,0,255,0.4);
            margin-bottom: 2rem;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(176,0,255,0.4); }
            50% { box-shadow: 0 0 0 10px rgba(176,0,255,0); }
        }
        h1 {
            font-size: 3.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #b000ff, #ff44ff, #b000ff);
            background-size: 300% 300%;
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 0.5rem;
            animation: gradientShift 4s ease infinite;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .sub { font-size: 1.1rem; color: #aaa; margin-bottom: 2rem; line-height: 1.6; }
        .btn-primary {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border: none;
            padding: 1rem 2.8rem;
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
            box-shadow: 0 5px 20px rgba(176,0,255,0.4);
        }
        .btn-primary:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 15px 35px rgba(176,0,255,0.6); }
        .stats {
            display: flex;
            justify-content: center;
            gap: 2.5rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(176,0,255,0.2);
        }
        .stat-item { text-align: center; }
        .stat-number { font-size: 1.8rem; font-weight: 700; color: #b000ff; }
        .stat-label { font-size: 0.75rem; color: #888; }
        .glow {
            position: fixed;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(176,0,255,0.15) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1;
        }
    </style>
</head>
<body>
    <div id="glow1" class="glow" style="top: -100px; left: -100px;"></div>
    <div id="glow2" class="glow" style="bottom: -100px; right: -100px;"></div>
    <div class="hero">
        <div class="badge">✨ DRAGON PINGX PREMIUM | CHÍNH THỨC ✨</div>
        <h1>𝕯𝕽𝕬𝕲𝖔𝕹 𝕻𝕴𝕹𝕲𝖃</h1>
        <div class="sub">⚡ Hệ thống kích hoạt bản quyền tự động ⚡<br>🔒 Bảo mật tuyệt đối - 🚀 Tốc độ thần tốc - 👑 Uy tín hàng đầu</div>
        <a href="/getkey" class="btn-primary">
            🎁 NHẬN KEY MIỄN PHÍ
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
        <div class="stats">
            <div class="stat-item"><div class="stat-number">24/7</div><div class="stat-label">Hỗ trợ</div></div>
            <div class="stat-item"><div class="stat-number">2.5k+</div><div class="stat-label">Người dùng</div></div>
            <div class="stat-item"><div class="stat-number">100%</div><div class="stat-label">Uptime</div></div>
        </div>
    </div>
    <script>
        for(let i=0;i<50;i++) {
            let p = document.createElement('div');
            p.className = 'particle';
            p.style.left = Math.random() * 100 + '%';
            p.style.animationDelay = Math.random() * 8 + 's';
            p.style.animationDuration = (5 + Math.random() * 5) + 's';
            document.body.appendChild(p);
        }
        document.addEventListener('mousemove', function(e) {
            document.getElementById('glow1').style.transform = `translate(${e.clientX * 0.05}px, ${e.clientY * 0.05}px)`;
            document.getElementById('glow2').style.transform = `translate(${-e.clientX * 0.03}px, ${-e.clientY * 0.03}px)`;
        });
    </script>
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
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
            padding: 2rem;
            border: 1px solid rgba(176, 0, 255, 0.3);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 30px rgba(176,0,255,0.1);
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        .icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border-radius: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            animation: rotate 4s linear infinite;
        }
        @keyframes rotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        h2 { color: white; text-align: center; margin-bottom: 0.5rem; font-size: 1.8rem; }
        .desc { color: #aaa; text-align: center; font-size: 0.9rem; margin-bottom: 1.5rem; }
        .info-box {
            background: rgba(0,0,0,0.4);
            border-radius: 1.2rem;
            padding: 1.2rem;
            margin: 1.5rem 0;
            border: 1px solid rgba(176,0,255,0.2);
        }
        .info-item { display: flex; align-items: center; gap: 0.75rem; color: #b000ff; font-size: 0.85rem; margin-bottom: 0.8rem; }
        .btn-get {
            width: 100%;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border: none;
            padding: 1rem;
            border-radius: 1rem;
            color: white;
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
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
        .result-box {
            margin-top: 1.5rem;
            padding: 1rem;
            background: rgba(0,0,0,0.4);
            border-radius: 1rem;
            border-left: 3px solid #b000ff;
            display: none;
        }
        .result-box.show { display: block; animation: slideUp 0.4s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .key-display {
            background: linear-gradient(135deg, #0f172a, #1a1a2e);
            padding: 0.8rem;
            border-radius: 0.8rem;
            font-family: monospace;
            font-size: 1rem;
            font-weight: 700;
            color: #b000ff;
            text-align: center;
            margin: 0.75rem 0;
            word-break: break-all;
            letter-spacing: 1px;
        }
        .copy-btn {
            background: rgba(176,0,255,0.2);
            border: 1px solid rgba(176,0,255,0.5);
            padding: 0.5rem 1.5rem;
            border-radius: 2rem;
            color: #b000ff;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s;
        }
        .copy-btn:hover { background: #b000ff; color: white; }
        .footer-note { margin-top: 1.5rem; text-align: center; font-size: 0.7rem; color: #475569; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">
            <svg width="40" height="40" fill="none" stroke="white" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
        </div>
        <h2>✨ NHẬN KEY NGAY ✨</h2>
        <div class="desc">Hoàn thành nhiệm vụ nhận key kích hoạt bản quyền</div>
        
        <div class="info-box">
            <div class="info-item">💎 Key có hiệu lực 24 giờ</div>
            <div class="info-item">🔐 1 key = 1 thiết bị duy nhất</div>
            <div class="info-item">⚡ Kích hoạt ngay sau khi nhận</div>
            <div class="info-item">🎁 Hỗ trợ 24/7 từ đội ngũ</div>
        </div>
        
        <button class="btn-get" onclick="generateKey()" id="getKeyBtn">🔥 LẤY KEY NGAY 🔥</button>
        
        <div id="resultBox" class="result-box">
            <div id="resultContent"></div>
        </div>
        
        <div class="footer-note">
            💜 DRAGON PINGX PREMIUM - Bảo mật tuyệt đối 💜
        </div>
    </div>
    
    <script>
        let sessionId = null;
        let checkInterval = null;
        
        function generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        
        async function generateKey() {
            const btn = document.getElementById('getKeyBtn');
            const resultBox = document.getElementById('resultBox');
            const resultContent = document.getElementById('resultContent');
            
            sessionId = generateUUID();
            
            btn.innerHTML = '<span class="loading-spinner"></span> Đang tạo nhiệm vụ...';
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/create_task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                const data = await response.json();
                
                if (data.success) {
                    resultContent.innerHTML = `
                        <div style="text-align:center">
                            <div style="color:#b000ff; margin-bottom:10px;">✅ NHIỆM VỤ ĐÃ SẴN SÀNG</div>
                            <div style="font-size:0.85rem; margin:10px 0;">📌 Bấm vào link bên dưới để hoàn thành nhiệm vụ:</div>
                            <a href="${data.task_url}" target="_blank" style="color:#b000ff; word-break:break-all; display:block; margin:10px 0; padding:8px; background:rgba(176,0,255,0.1); border-radius:10px;">🔗 ${data.task_url}</a>
                            <div style="font-size:0.7rem; color:#64748b; margin-top:10px;">⏳ Sau khi hoàn thành, key sẽ tự động hiển thị bên dưới (có thể mất vài giây)</div>
                            <div id="waitingKey" style="margin-top:15px;"><span class="loading-spinner"></span> Đang chờ xác nhận...</div>
                        </div>
                    `;
                    resultBox.classList.add('show');
                    
                    window.open(data.task_url, '_blank');
                    startChecking();
                } else {
                    alert('Lỗi: ' + (data.message || 'Không thể tạo link'));
                    btn.innerHTML = '🔥 LẤY KEY NGAY 🔥';
                    btn.disabled = false;
                }
            } catch (error) {
                alert('Lỗi kết nối! Vui lòng thử lại.');
                btn.innerHTML = '🔥 LẤY KEY NGAY 🔥';
                btn.disabled = false;
            }
        }
        
        function startChecking() {
            if (checkInterval) clearInterval(checkInterval);
            
            let checkCount = 0;
            checkInterval = setInterval(async () => {
                checkCount++;
                try {
                    const response = await fetch(`/api/check_task/${sessionId}`);
                    const data = await response.json();
                    
                    if (data.completed && data.key) {
                        clearInterval(checkInterval);
                        const waitingDiv = document.getElementById('waitingKey');
                        if (waitingDiv) {
                            waitingDiv.innerHTML = `
                                <div style="background:linear-gradient(135deg,#b000ff20,#ff44ff10); padding:1rem; border-radius:0.8rem; margin-top:0.5rem; border:1px solid #b000ff30;">
                                    <div style="color:#b000ff; font-weight:700; margin-bottom:8px;">🎉 CHÚC MỪNG! KEY CỦA BẠN 🎉</div>
                                    <div class="key-display" id="licenseKey">${data.key}</div>
                                    <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
                                    <div style="font-size:0.7rem; color:#64748b; margin-top:10px;">⏰ Hạn sử dụng: 24 giờ</div>
                                </div>
                            `;
                        }
                    } else if (checkCount > 60) {
                        clearInterval(checkInterval);
                        const waitingDiv = document.getElementById('waitingKey');
                        if (waitingDiv) {
                            waitingDiv.innerHTML = '<div style="color:#ff6666;">⏰ Hết thời gian chờ (3 phút). Vui lòng thử lại.</div>';
                        }
                        document.getElementById('getKeyBtn').innerHTML = '🔥 LẤY KEY NGAY 🔥';
                        document.getElementById('getKeyBtn').disabled = false;
                    }
                } catch (error) {
                    console.error('Check error:', error);
                }
            }, 3000);
        }
        
        function copyKey() {
            const key = document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(key).then(() => {
                alert('✅ Đã sao chép key: ' + key);
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .card {
            max-width: 520px;
            width: 100%;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(176, 0, 255, 0.4);
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
            background: linear-gradient(135deg, #00ff88, #00cc66);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        h2 { color: white; font-size: 2rem; margin-bottom: 0.5rem; }
        .desc { color: #aaa; margin-bottom: 1.5rem; }
        .key-box {
            background: linear-gradient(135deg, #0f172a, #1a1a2e);
            border-radius: 1.2rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px dashed #b000ff;
        }
        .key-label { font-size: 0.7rem; color: #b000ff; text-transform: uppercase; letter-spacing: 2px; }
        .key-value {
            font-family: monospace;
            font-size: 1.2rem;
            font-weight: 700;
            color: #b000ff;
            word-break: break-all;
            margin: 0.8rem 0;
            letter-spacing: 1px;
        }
        .copy-btn {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border: none;
            padding: 0.6rem 1.8rem;
            border-radius: 2rem;
            color: white;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .warning { font-size: 0.7rem; color: #64748b; margin: 1rem 0; }
        .btn-back {
            display: inline-block;
            background: rgba(176,0,255,0.2);
            text-decoration: none;
            color: #b000ff;
            padding: 0.7rem 1.5rem;
            border-radius: 2rem;
            font-weight: 600;
            margin-top: 1rem;
            border: 1px solid rgba(176,0,255,0.3);
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="success-icon">
            <svg width="48" height="48" fill="none" stroke="white" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
        </div>
        <h2>🎉 THÀNH CÔNG! 🎉</h2>
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
                alert('✅ Đã sao chép key!\\nKey: ' + key);
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
            background: linear-gradient(135deg, #0a0a0a, #0f0f1a);
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
            border: 1px solid rgba(239, 68, 68, 0.4);
        }
        .error-icon { font-size: 4rem; margin-bottom: 1rem; }
        h2 { color: #f87171; margin-bottom: 0.5rem; }
        p { color: #aaa; margin-bottom: 1.5rem; }
        .btn-back {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            color: white;
            text-decoration: none;
            padding: 0.8rem 1.8rem;
            border-radius: 2rem;
            display: inline-block;
            font-weight: 600;
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

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/getkey')
def getkey():
    return render_template_string(GETKEY_HTML)

@app.route('/api/create_task', methods=['POST'])
def create_task():
    try:
        clean_expired_sessions()
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'message': 'Invalid session'}), 400
        
        callback_url = f"{YOUR_DOMAIN}/api/callback?session_id={session_id}"
        
        try:
            params = {'api': LINK4M_API_KEY, 'url': callback_url}
            response = requests.get(LINK4M_API_URL, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' and result.get('shortenedUrl'):
                    task_url = result.get('shortenedUrl')
                else:
                    task_url = callback_url
            else:
                task_url = callback_url
        except Exception as e:
            print(f"Link4m error: {e}")
            task_url = callback_url
        
        sessions[session_id] = {
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'task_url': task_url})
        
    except Exception as e:
        print(f"Create task error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check_task/<session_id>')
def check_task(session_id):
    try:
        clean_expired_sessions()
        if session_id in sessions and sessions[session_id].get('status') == 'completed':
            return jsonify({
                'completed': True,
                'key': sessions[session_id].get('key')
            })
        return jsonify({'completed': False})
    except Exception as e:
        return jsonify({'completed': False, 'error': str(e)})

@app.route('/api/callback')
def callback():
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return render_template_string(ERROR_HTML, message="Thiếu mã phiên!")
        
        if session_id not in sessions:
            return render_template_string(ERROR_HTML, message="Phiên không hợp lệ hoặc đã hết hạn!")
        
        if sessions[session_id].get('status') == 'completed':
            existing_key = sessions[session_id].get('key')
            if existing_key:
                return render_template_string(SUCCESS_HTML, key=existing_key, expires="24 giờ")
            return render_template_string(ERROR_HTML, message="Key đã được tạo trước đó!")
        
        new_key = generate_dragon_key()
        expires_at = datetime.now() + timedelta(hours=24)
        
        keys = load_keys()
        keys[new_key] = {
            'expires_at': expires_at.isoformat(),
            'used': False,
            'created_at': datetime.now().isoformat(),
            'session_id': session_id
        }
        save_keys(keys)
        
        sessions[session_id]['status'] = 'completed'
        sessions[session_id]['key'] = new_key
        sessions[session_id]['expires_at'] = expires_at.isoformat()
        
        return render_template_string(SUCCESS_HTML, key=new_key, expires="24 giờ")
        
    except Exception as e:
        print(f"Callback error: {e}")
        return render_template_string(ERROR_HTML, message=f"Lỗi: {str(e)}")

@app.route('/api/verify', methods=['POST'])
def verify_key():
    try:
        data = request.json
        key = data.get('key', '').strip().upper()
        
        if not key:
            return jsonify({'status': 'error', 'message': 'Vui lòng nhập key!'})
        
        # ===== QUAN TRỌNG: NHẬN KEY DRAGONLOCUT =====
        if key == "DRAGONLOCUT":
            return jsonify({
                'status': 'success',
                'message': '✅ Kích hoạt thành công! Chào mừng Admin!',
                'key': key,
                'expires_at': (datetime.now() + timedelta(days=365)).isoformat(),
                'app_name': 'DRAGON PINGX PREMIUM'
            })
        
        if key in ADMIN_KEYS:
            return jsonify({
                'status': 'success',
                'message': '✅ Admin Key! Kích hoạt thành công!',
                'key': key,
                'expires_at': (datetime.now() + timedelta(days=365)).isoformat(),
                'app_name': 'DRAGON PINGX PREMIUM'
            })
        
        keys = load_keys()
        
        if key not in keys:
            return jsonify({'status': 'invalid', 'message': '❌ Key không hợp lệ!'})
        
        info = keys[key]
        expires_at = datetime.fromisoformat(info['expires_at'])
        
        if datetime.now() > expires_at:
            return jsonify({'status': 'expired', 'message': '❌ Key đã hết hạn!'})
        
        if info.get('used', False):
            return jsonify({'status': 'used', 'message': '❌ Key đã được sử dụng!'})
        
        info['used'] = True
        info['used_at'] = datetime.now().isoformat()
        save_keys(keys)
        
        return jsonify({
            'status': 'success',
            'message': '✅ Key hợp lệ!',
            'key': key,
            'expires_at': expires_at.isoformat(),
            'app_name': 'DRAGON PINGX PREMIUM'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check/<key>')
def check_key(key):
    try:
        key = key.upper()
        
        if key == "DRAGONLOCUT" or key in ADMIN_KEYS:
            return "VALID"
        
        keys = load_keys()
        if key not in keys:
            return "INVALID"
        info = keys[key]
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
    try:
        keys = load_keys()
        total = len([k for k in keys if k.startswith("DRP-")])
        valid = 0
        for k, v in keys.items():
            if k.startswith("DRP-") and not v.get('used', False):
                try:
                    if datetime.now() < datetime.fromisoformat(v['expires_at']):
                        valid += 1
                except:
                    pass
        return jsonify({
            'total_keys': total,
            'valid_keys': valid + len(ADMIN_KEYS),
            'server_time': datetime.now().isoformat()
        })
    except:
        return jsonify({'total_keys': 0, 'valid_keys': 0})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)