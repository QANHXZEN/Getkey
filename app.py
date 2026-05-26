from flask import Flask, render_template_string, redirect

app = Flask(__name__)

# === LINK VUOTNHANH.COM ===
VUOTNHANH_LINKS = {
    "esp_vip": "https://vuotnhanh.com/28uK",
    "aimbot": "https://vuotnhanh.com/CRKh",
    "freefire_vip": "https://vuotnhanh.com/MFCO",
    "naruto_ping": "https://vuotnhanh.com/x24C",
    "henry_ping": "https://vuotnhanh.com/vmqo",
    "tangnhay_v1": "https://vuotnhanh.com/cXXE",
    "script_doraemon": "https://vuotnhanh.com/KYhj",
    "xuyen_keo": "https://vuotnhanh.com/vh8w",
    "dam_ra_van_go": "https://vuotnhanh.com/WuFE",
    "xuyen_all_map": "https://vuotnhanh.com/xc3u",
    "fix_lag": "https://vuotnhanh.com/OYSE",
    "nhe_tam": "https://vuotnhanh.com/sMvv",
    "aim_dau_v2": "https://vuotnhanh.com/0n1q",
    "magic_bullet": "https://vuotnhanh.com/YswI",
    "ff_global": "https://vuotnhanh.com/mu6L"
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>QANHNO1 - Shop Tool Game</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 10% 20%, #0a0a1a, #03030f);
            color: #fff;
            min-height: 100vh;
        }

        /* Animated background */
        .bg-animation {
            position: fixed;
            width: 100%;
            height: 100%;
            z-index: 0;
            overflow: hidden;
        }

        .bg-animation span {
            position: absolute;
            width: 4px;
            height: 4px;
            background: rgba(0, 255, 136, 0.3);
            border-radius: 50%;
            animation: floatStar 8s infinite linear;
        }

        @keyframes floatStar {
            0% {
                transform: translateY(100vh) scale(0);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) scale(1);
                opacity: 0;
            }
        }

        .container {
            position: relative;
            z-index: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .logo {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00ff88, #00b8ff, #ff6b6b);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: shimmer 3s infinite;
        }

        @keyframes shimmer {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }

        .slogan {
            color: rgba(255,255,255,0.5);
            font-size: 0.9rem;
            margin-top: 8px;
        }

        /* Stats */
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }

        .stat-card {
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0,255,136,0.2);
            border-radius: 60px;
            padding: 8px 24px;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: 0.3s;
        }

        .stat-card:hover {
            border-color: #00ff88;
            transform: translateY(-3px);
        }

        .stat-card i {
            font-size: 1.4rem;
            color: #00ff88;
        }

        .stat-card span {
            font-weight: 600;
        }

        .stat-card small {
            color: rgba(255,255,255,0.5);
            font-size: 0.8rem;
        }

        /* Game Grid */
        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 25px;
        }

        /* Game Card */
        .game-card {
            background: rgba(15, 20, 35, 0.6);
            backdrop-filter: blur(12px);
            border-radius: 24px;
            border: 1px solid rgba(0,255,136,0.15);
            overflow: hidden;
            transition: 0.4s;
        }

        .game-card:hover {
            transform: translateY(-8px);
            border-color: #00ff88;
            box-shadow: 0 20px 40px rgba(0,255,136,0.1);
        }

        .game-header {
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .game-header h2 {
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }

        .game-header.ff h2 { color: #ff6b6b; }
        .game-header.rbx h2 { color: #ffd93d; }
        .game-header.pubg h2 { color: #6bcbff; }

        .hot-tag {
            position: absolute;
            top: 15px;
            right: 15px;
            background: linear-gradient(135deg, #ff6b6b, #ff0000);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.05); }
        }

        .platform-section {
            padding: 16px;
        }

        .platform-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 12px;
            padding-left: 10px;
            border-left: 3px solid #00ff88;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Feature Grid */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
        }

        .feature-item {
            background: rgba(0,0,0,0.4);
            border-radius: 14px;
            padding: 12px;
            text-align: center;
            transition: 0.3s;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .feature-item:hover {
            transform: translateY(-2px);
            background: rgba(0,255,136,0.1);
            border-color: #00ff88;
        }

        .feature-name {
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-bottom: 6px;
        }

        .feature-name i {
            font-size: 1rem;
        }

        .feature-acc {
            font-size: 0.6rem;
            font-family: monospace;
            background: rgba(0,0,0,0.5);
            padding: 4px 8px;
            border-radius: 8px;
            margin: 6px 0;
            color: rgba(255,255,255,0.7);
        }

        .btn-down {
            width: 100%;
            padding: 8px;
            margin-top: 8px;
            background: linear-gradient(135deg, #00ff88, #0099ff);
            border: none;
            border-radius: 30px;
            color: #0a0f1e;
            font-weight: 700;
            font-size: 0.75rem;
            cursor: pointer;
            transition: 0.3s;
        }

        .btn-down:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(0,255,136,0.4);
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 30px;
            margin-top: 40px;
            border-top: 1px solid rgba(255,255,255,0.05);
            color: rgba(255,255,255,0.3);
            font-size: 0.8rem;
        }

        @media (max-width: 768px) {
            .container { padding: 15px; }
            .logo { font-size: 2rem; }
            .stats { gap: 12px; }
            .stat-card { padding: 5px 16px; font-size: 0.8rem; }
            .games-grid { grid-template-columns: 1fr; }
            .feature-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<div class="bg-animation" id="stars"></div>

<div class="container">
    <div class="header">
        <div class="logo">⚡ QANHNO1 SHOP ⚡</div>
        <div class="slogan"><i class="fas fa-gem"></i> Tool Game - Mod Skin - Hỗ trợ 24/7 <i class="fas fa-gem"></i></div>
    </div>

    <div class="stats">
        <div class="stat-card"><i class="fas fa-users"></i> <span>10,000+</span> <small>Thành viên</small></div>
        <div class="stat-card"><i class="fas fa-download"></i> <span>50,000+</span> <small>Lượt tải</small></div>
        <div class="stat-card"><i class="fas fa-star"></i> <span>4.9</span> <small>Đánh giá</small></div>
        <div class="stat-card"><i class="fas fa-shield-alt"></i> <span>Uy tín</span> <small>#1</small></div>
    </div>

    <div class="games-grid">
        <!-- FREE FIRE -->
        <div class="game-card">
            <div class="hot-tag"><i class="fas fa-fire"></i> HOT</div>
            <div class="game-header ff">
                <h2><i class="fas fa-gamepad"></i> FREE FIRE <i class="fas fa-skull"></i></h2>
            </div>
            <div class="platform-section">
                <div class="platform-title"><i class="fab fa-android"></i> ANDROID</div>
                <div class="feature-grid">
                    <div class="feature-item" onclick="location.href='/download/esp_vip'">
                        <div class="feature-name"><i class="fas fa-eye"></i> Esp Vip</div>
                        <div class="feature-acc"><i class="fas fa-user"></i> LIMON-GAMING-OFC <br> <i class="fas fa-lock"></i> 248194848323</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/aimbot'">
                        <div class="feature-name"><i class="fas fa-crosshairs"></i> AimBot 90%</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/freefire_vip'">
                        <div class="feature-name"><i class="fas fa-crown"></i> Menu Free Fire VIP</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/naruto_ping'">
                        <div class="feature-name"><i class="fas fa-user-ninja"></i> Naruto Ping Crack</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/henry_ping'">
                        <div class="feature-name"><i class="fas fa-bolt"></i> Henry Ping Crack</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/tangnhay_v1'">
                        <div class="feature-name"><i class="fas fa-tachometer-alt"></i> Tăng Nhạy V1</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/script_doraemon'">
                        <div class="feature-name"><i class="fas fa-robot"></i> Script Doraemon V3</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/xuyen_keo'">
                        <div class="feature-name"><i class="fas fa-ghost"></i> Đi xuyên keo</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/dam_ra_van_go'">
                        <div class="feature-name"><i class="fas fa-fist-raised"></i> Đấm ra ván gỗ</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/xuyen_all_map'">
                        <div class="feature-name"><i class="fas fa-map"></i> Đi xuyên all map, đán ra sàn kính</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/fix_lag'">
                        <div class="feature-name"><i class="fas fa-wrench"></i> Fix lag</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/nhe_tam'">
                        <div class="feature-name"><i class="fas fa-leaf"></i> Nhẹ tâm</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/aim_dau_v2'">
                        <div class="feature-name"><i class="fas fa-bullseye"></i> Aim đầu v2</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/magic_bullet'">
                        <div class="feature-name"><i class="fas fa-magic"></i> Magic Bullet, xuyên keo</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                    <div class="feature-item" onclick="location.href='/download/ff_global'">
                        <div class="feature-name"><i class="fas fa-globe"></i> Free Fire Global</div>
                        <button class="btn-down"><i class="fas fa-download"></i> TẢI NGAY</button>
                    </div>
                </div>
            </div>
            <div class="platform-section">
                <div class="platform-title"><i class="fab fa-apple"></i> iOS</div>
                <div style="text-align:center; padding:20px; color:#666;"><i class="fas fa-clock"></i> Đang cập nhật...</div>
            </div>
        </div>

        <!-- ROBLOX -->
        <div class="game-card">
            <div class="game-header rbx">
                <h2><i class="fab fa-fort-awesome"></i> ROBLOX</h2>
            </div>
            <div class="platform-section">
                <div class="platform-title"><i class="fab fa-android"></i> ANDROID</div>
                <div style="text-align:center; padding:20px; color:#666;"><i class="fas fa-clock"></i> Đang cập nhật...</div>
            </div>
            <div class="platform-section">
                <div class="platform-title"><i class="fab fa-apple"></i> iOS</div>
                <div style="text-align:center; padding:20px; color:#666;"><i class="fas fa-clock"></i> Đang cập nhật...</div>
            </div>
        </div>

        <!-- PUBG -->
        <div class="game-card">
            <div class="game-header pubg">
                <h2><i class="fas fa-gun"></i> PUBG</h2>
            </div>
            <div class="platform-section">
                <div class="platform-title"><i class="fab fa-android"></i> ANDROID</div>
                <div style="text-align:center; padding:20px; color:#666;"><i class="fas fa-clock"></i> Đang cập nhật...</div>
            </div>
            <div class="platform-section">
                <div class="platform-title"><i class="fab fa-apple"></i> iOS</div>
                <div style="text-align:center; padding:20px; color:#666;"><i class="fas fa-clock"></i> Đang cập nhật...</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <i class="fas fa-shield-alt"></i> QANHNO1 SHOP - Uy tín hàng đầu Việt Nam<br>
        © 2026 - All rights reserved
    </div>
</div>

<script>
    // Tạo hiệu ứng sao bay
    const starsContainer = document.getElementById('stars');
    for (let i = 0; i < 100; i++) {
        const star = document.createElement('span');
        star.style.left = Math.random() * 100 + '%';
        star.style.animationDelay = Math.random() * 8 + 's';
        star.style.animationDuration = 4 + Math.random() * 6 + 's';
        star.style.width = star.style.height = (Math.random() * 3 + 1) + 'px';
        star.style.background = `rgba(0, 255, ${100 + Math.random() * 155}, ${0.3 + Math.random() * 0.5})`;
        starsContainer.appendChild(star);
    }
</script>

</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download/<file_type>')
def download(file_type):
    if file_type not in VUOTNHANH_LINKS:
        return "Invalid file type", 400
    return redirect(VUOTNHANH_LINKS[file_type])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)