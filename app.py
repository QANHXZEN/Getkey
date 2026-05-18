from flask import Flask, request, jsonify, render_template_string, redirect
import requests
import random
import string
from datetime import datetime, timedelta
import os
import json

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

# ========== TRANG CHỦ VỚI ANIMATION ĐẸP ==========
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
        
        /* Hiệu ứng sao băng */
        .star {
            position: fixed;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            opacity: 0;
            animation: shootingStar 4s linear infinite;
        }
        @keyframes shootingStar {
            0% { transform: translateX(0) translateY(0); opacity: 0; }
            10% { opacity: 1; }
            20% { opacity: 1; }
            30% { opacity: 0; }
            100% { transform: translateX(-200px) translateY(200px); opacity: 0; }
        }
        
        /* Hiệu ứng hạt ma thuật */
        .magic-particle {
            position: fixed;
            width: 4px;
            height: 4px;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border-radius: 50%;
            opacity: 0;
            animation: floatMagic 6s infinite;
        }
        @keyframes floatMagic {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            20% { opacity: 0.8; }
            80% { opacity: 0.6; }
            100% { transform: translateY(-100px) rotate(360deg); opacity: 0; }
        }
        
        /* Hiệu ứng đèn nền */
        .glow {
            position: fixed;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(176,0,255,0.15) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1;
            transition: all 0.3s ease;
        }
        
        .hero {
            text-align: center;
            max-width: 600px;
            animation: fadeInUp 0.8s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            position: relative;
            z-index: 2;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(50px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
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
            animation: pulse 2s infinite, borderGlow 3s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(176,0,255,0.4); transform: scale(1); }
            50% { box-shadow: 0 0 0 15px rgba(176,0,255,0); transform: scale(1.02); }
        }
        
        @keyframes borderGlow {
            0%, 100% { border-color: rgba(176,0,255,0.4); }
            50% { border-color: rgba(176,0,255,1); }
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
            animation: gradientShift 4s ease infinite, textGlow 2s ease-in-out infinite;
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        @keyframes textGlow {
            0%, 100% { filter: drop-shadow(0 0 5px rgba(176,0,255,0.3)); }
            50% { filter: drop-shadow(0 0 20px rgba(176,0,255,0.6)); }
        }
        
        .sub {
            font-size: 1.1rem;
            color: #aaa;
            margin-bottom: 2rem;
            line-height: 1.6;
            animation: fadeInUp 0.8s 0.2s backwards;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border: none;
            padding: 1rem 2.8rem;
            font-size: 1rem;
            font-weight: 600;
            color: white;
            border-radius: 60px;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            display: inline-flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            box-shadow: 0 5px 20px rgba(176,0,255,0.4);
            animation: fadeInUp 0.8s 0.4s backwards;
            position: relative;
            overflow: hidden;
        }
        
        .btn-primary::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn-primary:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .btn-primary:hover {
            transform: translateY(-5px) scale(1.05);
            box-shadow: 0 15px 40px rgba(176,0,255,0.6);
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 2.5rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(176,0,255,0.2);
            animation: fadeInUp 0.8s 0.6s backwards;
        }
        
        .stat-item {
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .stat-item:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            animation: countUp 1s ease-out;
        }
        
        @keyframes countUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: #888;
            margin-top: 0.3rem;
        }
        
        /* Hiệu ứng loading cho trang */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #0a0a0a;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeOut 1s ease 1s forwards;
        }
        
        @keyframes fadeOut {
            to { opacity: 0; visibility: hidden; }
        }
        
        .loader {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(176,0,255,0.3);
            border-top-color: #b000ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loader"></div>
    </div>
    
    <div id="glow1" class="glow" style="top: -100px; left: -100px;"></div>
    <div id="glow2" class="glow" style="bottom: -100px; right: -100px;"></div>
    
    <div class="hero">
        <div class="badge">✨ DRAGON PINGX PREMIUM | CHÍNH THỨC ✨</div>
        <h1>DRAGON PINGX</h1>
        <div class="sub">⚡ Hệ thống kích hoạt bản quyền tự động ⚡<br>🔒 Bảo mật tuyệt đối - 🚀 Tốc độ thần tốc - 👑 Uy tín hàng đầu</div>
        <a href="/getkey" class="btn-primary">
            🎁 NHẬN KEY MIỄN PHÍ
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
        <div class="stats">
            <div class="stat-item"><div class="stat-number" data-target="24">0</div><div class="stat-label">Hỗ trợ</div></div>
            <div class="stat-item"><div class="stat-number" data-target="2500">0</div><div class="stat-label">Người dùng</div></div>
            <div class="stat-item"><div class="stat-number" data-target="100">0</div><div class="stat-label">Uptime</div></div>
        </div>
    </div>
    
    <script>
        // Tạo hiệu ứng sao băng và hạt ma thuật
        for(let i = 0; i < 30; i++) {
            let star = document.createElement('div');
            star.className = 'star';
            star.style.top = Math.random() * 100 + '%';
            star.style.left = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 8 + 's';
            star.style.animationDuration = (3 + Math.random() * 3) + 's';
            document.body.appendChild(star);
        }
        
        for(let i = 0; i < 40; i++) {
            let particle = document.createElement('div');
            particle.className = 'magic-particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 8 + 's';
            particle.style.animationDuration = (5 + Math.random() * 5) + 's';
            document.body.appendChild(particle);
        }
        
        // Hiệu ứng đuổi chuột
        document.addEventListener('mousemove', function(e) {
            document.getElementById('glow1').style.transform = `translate(${e.clientX * 0.05}px, ${e.clientY * 0.05}px)`;
            document.getElementById('glow2').style.transform = `translate(${-e.clientX * 0.03}px, ${-e.clientY * 0.03}px)`;
        });
        
        // Count up animation
        function animateNumber(element, target) {
            let current = 0;
            let increment = target / 50;
            let timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    element.textContent = target + (target === 2500 ? '+' : (target === 100 ? '%' : ''));
                    clearInterval(timer);
                } else {
                    element.textContent = Math.floor(current) + (target === 2500 ? '+' : (target === 100 ? '%' : ''));
                }
            }, 30);
        }
        
        setTimeout(() => {
            document.querySelectorAll('.stat-number').forEach(el => {
                let target = parseInt(el.dataset.target);
                animateNumber(el, target);
            });
        }, 500);
        
        // Ẩn loading sau 1.5s
        setTimeout(() => {
            document.getElementById('loadingOverlay').style.display = 'none';
        }, 1500);
    </script>
</body>
</html>
"""

# ========== TRANG LẤY KEY VỚI ANIMATION ĐẸP ==========
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
            position: relative;
            overflow-x: hidden;
        }
        
        /* Hiệu ứng nền động */
        .bg-effect {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0;
        }
        
        .bg-circle {
            position: absolute;
            border-radius: 50%;
            background: rgba(176,0,255,0.05);
            animation: float 20s infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-50px) rotate(180deg); }
        }
        
        .card {
            position: relative;
            z-index: 2;
            max-width: 500px;
            width: 100%;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            border: 1px solid rgba(176, 0, 255, 0.3);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 30px rgba(176,0,255,0.1);
            animation: cardGlow 3s infinite, fadeInScale 0.6s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        }
        
        @keyframes cardGlow {
            0%, 100% { box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 20px rgba(176,0,255,0.1); }
            50% { box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), 0 0 40px rgba(176,0,255,0.3); }
        }
        
        @keyframes fadeInScale {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        
        .icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border-radius: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            animation: rotate3D 4s ease-in-out infinite, pulseGlow 2s infinite;
        }
        
        @keyframes rotate3D {
            0% { transform: rotateY(0deg); }
            50% { transform: rotateY(180deg); }
            100% { transform: rotateY(360deg); }
        }
        
        @keyframes pulseGlow {
            0%, 100% { box-shadow: 0 0 0 0 rgba(176,0,255,0.4); }
            50% { box-shadow: 0 0 0 15px rgba(176,0,255,0); }
        }
        
        h2 {
            color: white;
            text-align: center;
            margin-bottom: 0.5rem;
            font-size: 1.8rem;
            background: linear-gradient(135deg, #fff, #b000ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            animation: textShine 3s infinite;
        }
        
        @keyframes textShine {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; letter-spacing: 1px; }
        }
        
        .desc {
            color: #aaa;
            text-align: center;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }
        
        .info-box {
            background: rgba(0,0,0,0.4);
            border-radius: 1.2rem;
            padding: 1.2rem;
            margin: 1.5rem 0;
            border: 1px solid rgba(176,0,255,0.2);
            animation: slideInLeft 0.5s 0.2s backwards;
        }
        
        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .info-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: #b000ff;
            font-size: 0.85rem;
            margin-bottom: 0.8rem;
            animation: fadeInItem 0.3s backwards;
        }
        
        .info-item:nth-child(1) { animation-delay: 0.3s; }
        .info-item:nth-child(2) { animation-delay: 0.4s; }
        .info-item:nth-child(3) { animation-delay: 0.5s; }
        .info-item:nth-child(4) { animation-delay: 0.6s; }
        
        @keyframes fadeInItem {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
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
            transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            position: relative;
            overflow: hidden;
            animation: slideInRight 0.5s 0.7s backwards;
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .btn-get::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn-get:hover::before {
            width: 300px;
            height: 300px;
        }
        
        .btn-get:hover {
            transform: translateY(-3px);
            filter: brightness(1.05);
            box-shadow: 0 10px 30px rgba(176,0,255,0.5);
        }
        
        .btn-get:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
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
            animation: slideUp 0.5s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        }
        
        .result-box.show { display: block; }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
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
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        
        .key-display:hover {
            background: #b000ff20;
            transform: scale(1.02);
            border-color: #b000ff;
        }
        
        .copy-btn {
            background: rgba(176,0,255,0.2);
            border: 1px solid rgba(176,0,255,0.5);
            padding: 0.5rem 1.5rem;
            border-radius: 2rem;
            color: #b000ff;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .copy-btn:hover {
            background: #b000ff;
            color: white;
            transform: scale(1.05);
        }
        
        .footer-note {
            margin-top: 1.5rem;
            text-align: center;
            font-size: 0.7rem;
            color: #475569;
            animation: fadeInUp 0.5s 1s backwards;
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .key-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .success-badge {
            display: inline-block;
            background: rgba(0,255,0,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            color: #00ff88;
            margin-bottom: 10px;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="bg-effect" id="bgEffect"></div>
    
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
        // Tạo hiệu ứng nền động
        for(let i = 0; i < 15; i++) {
            let circle = document.createElement('div');
            circle.className = 'bg-circle';
            let size = 100 + Math.random() * 200;
            circle.style.width = size + 'px';
            circle.style.height = size + 'px';
            circle.style.left = Math.random() * 100 + '%';
            circle.style.top = Math.random() * 100 + '%';
            circle.style.animationDelay = Math.random() * 20 + 's';
            circle.style.animationDuration = (15 + Math.random() * 10) + 's';
            document.getElementById('bgEffect').appendChild(circle);
        }
        
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
                            <div class="success-badge">✅ NHIỆM VỤ ĐÃ SẴN SÀNG</div>
                            <div style="font-size:0.85rem; margin:15px 0;">📌 Bấm vào link bên dưới để hoàn thành nhiệm vụ:</div>
                            <a href="${data.task_url}" target="_blank" style="color:#b000ff; word-break:break-all; display:block; margin:15px 0; padding:12px; background:linear-gradient(135deg,rgba(176,0,255,0.1),rgba(255,68,255,0.05)); border-radius:12px; text-decoration:none; transition:all 0.3s;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">🔗 ${data.task_url}</a>
                            <div style="font-size:0.7rem; color:#64748b; margin-top:10px;">⏳ Sau khi hoàn thành, key sẽ tự động hiển thị bên dưới (có thể mất vài giây)</div>
                            <div id="waitingKey" style="margin-top:20px;"><span class="loading-spinner"></span> Đang chờ xác nhận...</div>
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
                                <div style="background:linear-gradient(135deg,#b000ff20,#ff44ff10); padding:1.2rem; border-radius:1rem; margin-top:0.5rem; border:1px solid #b000ff30; animation: slideUp 0.5s ease">
                                    <div style="color:#b000ff; font-weight:700; margin-bottom:12px; font-size:1.1rem;">🎉 CHÚC MỪNG! KEY CỦA BẠN 🎉</div>
                                    <div class="key-display" id="licenseKey" onclick="copyKey()">${data.key}</div>
                                    <div class="key-wrapper">
                                        <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
                                    </div>
                                    <div style="font-size:0.7rem; color:#64748b; margin-top:12px;">⏰ Hạn sử dụng: 24 giờ | ✨ Bấm vào key để sao chép</div>
                                </div>
                            `;
                        }
                    } else if (checkCount > 60) {
                        clearInterval(checkInterval);
                        const waitingDiv = document.getElementById('waitingKey');
                        if(waitingDiv) waitingDiv.innerHTML = '<div style="color:#ff6666; padding:10px; background:rgba(255,0,0,0.1); border-radius:8px;">⏰ Hết thời gian chờ (3 phút). Vui lòng thử lại.</div>';
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
                const btn = event.target;
                const originalText = btn.innerText;
                btn.innerText = '✅ Đã sao chép!';
                setTimeout(() => { btn.innerText = originalText; }, 1500);
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
            position: relative;
            overflow: hidden;
        }
        
        /* Hiệu ứng confetti */
        .confetti {
            position: fixed;
            width: 10px;
            height: 10px;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            position: absolute;
            animation: confettiFall 3s linear forwards;
        }
        
        @keyframes confettiFall {
            0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
            100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
        }
        
        .card {
            max-width: 520px;
            width: 100%;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 2rem;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(176, 0, 255, 0.4);
            animation: bounceIn 0.8s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            z-index: 2;
        }
        
        @keyframes bounceIn {
            0% { opacity: 0; transform: scale(0.7); }
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
            animation: pulseSuccess 1s infinite, rotateIcon 2s ease;
        }
        
        @keyframes pulseSuccess {
            0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,255,136,0.4); }
            50% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(0,255,136,0); }
        }
        
        @keyframes rotateIcon {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        h2 {
            color: white;
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #fff, #00ff88);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
        }
        
        .desc {
            color: #aaa;
            margin-bottom: 1.5rem;
        }
        
        .key-box {
            background: linear-gradient(135deg, #0f172a, #1a1a2e);
            border-radius: 1.2rem;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px dashed #b000ff;
            animation: glowPulse 2s infinite;
        }
        
        @keyframes glowPulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(176,0,255,0.2); border-color: #b000ff; }
            50% { box-shadow: 0 0 20px 0 rgba(176,0,255,0.4); border-color: #ff44ff; }
        }
        
        .key-label {
            font-size: 0.7rem;
            color: #b000ff;
            text-transform: uppercase;
            letter-spacing: 3px;
        }
        
        .key-value {
            font-family: monospace;
            font-size: 1.3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            word-break: break-all;
            margin: 0.8rem 0;
            letter-spacing: 2px;
            cursor: pointer;
            padding: 10px;
            border-radius: 10px;
            transition: all 0.3s;
        }
        
        .key-value:hover {
            background: #b000ff20;
            transform: scale(1.02);
        }
        
        .copy-btn {
            background: linear-gradient(135deg, #b000ff, #ff44ff);
            border: none;
            padding: 0.7rem 1.8rem;
            border-radius: 2rem;
            color: white;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .copy-btn:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 10px 20px rgba(176,0,255,0.4);
        }
        
        .warning {
            font-size: 0.7rem;
            color: #64748b;
            margin: 1rem 0;
        }
        
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
            transition: all 0.3s;
        }
        
        .btn-back:hover {
            background: rgba(176,0,255,0.4);
            transform: translateY(-2px);
        }
        
        .flex-center {
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .sparkle {
            position: fixed;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }
    </style>
</head>
<body>
    <div class="sparkle" id="sparkle"></div>
    
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
            <div class="key-value" id="licenseKey" onclick="copyKey()">{{ key }}</div>
            <div class="flex-center">
                <button class="copy-btn" onclick="copyKey()">📋 Sao chép key</button>
            </div>
        </div>
        <div class="warning">
            ⏰ Key có hiệu lực trong {{ expires }}<br>
            📱 Nhập key vào ứng dụng DRAGON PINGX PREMIUM để kích hoạt
        </div>
        <a href="/" class="btn-back">🏠 Về trang chủ</a>
    </div>
    
    <script>
        // Tạo hiệu ứng confetti
        function createConfetti() {
            for(let i = 0; i < 100; i++) {
                let confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + '%';
                confetti.style.animationDelay = Math.random() * 2 + 's';
                confetti.style.animationDuration = (2 + Math.random() * 2) + 's';
                confetti.style.background = `linear-gradient(135deg, ${['#b000ff', '#ff44ff', '#00ff88', '#ffaa00'][Math.floor(Math.random()*4)]}, #fff)`;
                document.body.appendChild(confetti);
                setTimeout(() => confetti.remove(), 3000);
            }
        }
        
        // Tạo hiệu ứng lấp lánh
        function createSparkle() {
            const sparkleDiv = document.getElementById('sparkle');
            for(let i = 0; i < 30; i++) {
                let star = document.createElement('div');
                star.innerHTML = '✨';
                star.style.position = 'absolute';
                star.style.left = Math.random() * 100 + '%';
                star.style.top = Math.random() * 100 + '%';
                star.style.fontSize = (10 + Math.random() * 15) + 'px';
                star.style.opacity = Math.random();
                star.style.animation = 'fadeOut 1s forwards';
                sparkleDiv.appendChild(star);
                setTimeout(() => star.remove(), 1000);
            }
        }
        
        createConfetti();
        createSparkle();
        
        function copyKey() {
            const key = document.getElementById('licenseKey').innerText;
            navigator.clipboard.writeText(key).then(() => {
                const btn = event.target;
                const originalText = btn.innerText;
                btn.innerText = '✅ Đã sao chép!';
                setTimeout(() => { btn.innerText = originalText; }, 1500);
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
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Lỗi - DRAGON PINGX PREMIUM</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet"><style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0a0a,#0f0f1a);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1.5rem;position:relative;}
.shake{animation:shake 0.5s ease;}
@keyframes shake{0%,100%{transform:translateX(0);}25%{transform:translateX(-10px);}75%{transform:translateX(10px);}}
.card{max-width:450px;background:rgba(15,23,42,0.9);backdrop-filter:blur(20px);border-radius:2rem;padding:2rem;text-align:center;border:1px solid rgba(239,68,68,0.4);animation:fadeIn 0.5s ease;}
@keyframes fadeIn{from{opacity:0;transform:scale(0.9);}to{opacity:1;transform:scale(1);}}
.error-icon{font-size:4rem;margin-bottom:1rem;animation:bounce 1s infinite;}
@keyframes bounce{0%,100%{transform:translateY(0);}50%{transform:translateY(-10px);}}
h2{color:#f87171;margin-bottom:0.5rem;}
p{color:#aaa;margin-bottom:1.5rem;}
.btn-back{background:linear-gradient(135deg,#b000ff,#ff44ff);color:white;text-decoration:none;padding:0.8rem 1.8rem;border-radius:2rem;display:inline-block;font-weight:600;transition:all 0.3s;}
.btn-back:hover{transform:translateY(-2px);box-shadow:0 10px 20px rgba(176,0,255,0.3);}
</style></head>
<body><div class="card shake"><div class="error-icon">⚠️</div><h2>Đã xảy ra lỗi</h2><p>{{ message }}</p><a href="/getkey" class="btn-back">🔄 Thử lại</a></div></body></html>
"""

# ========== API ==========
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
        
        sessions[session_id] = {'status': 'pending', 'created_at': datetime.now().isoformat()}
        return jsonify({'success': True, 'task_url': task_url})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check_task/<session_id>')
def check_task(session_id):
    try:
        clean_expired_sessions()
        if session_id in sessions and sessions[session_id].get('status') == 'completed':
            return jsonify({'completed': True, 'key': sessions[session_id].get('key')})
        return jsonify({'completed': False})
    except Exception as e:
        return jsonify({'completed': False})

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
        keys[new_key] = {'expires_at': expires_at.isoformat(), 'used': False, 'created_at': datetime.now().isoformat(), 'session_id': session_id}
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
        if key == "DRAGONLOCUT" or key in ADMIN_KEYS:
            return jsonify({'status': 'success', 'message': '✅ Kích hoạt thành công!', 'key': key, 'expires_at': (datetime.now() + timedelta(days=365)).isoformat()})
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
        return jsonify({'status': 'success', 'message': '✅ Key hợp lệ!', 'key': key, 'expires_at': expires_at.isoformat()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/donekey')
def donekey():
    return redirect('/getkey')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)