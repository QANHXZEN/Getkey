package com.dragon.pingx;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.animation.Animation;
import android.view.animation.TranslateAnimation;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Timer;
import java.util.TimerTask;

public class MainActivity extends Activity {
    
    private boolean isRunning = false;
    private Timer pingTimer;
    private int pingCount = 0;
    private Handler handler = new Handler();
    private boolean isBypassed = false;
    
    private LinearLayout loginScreen;
    private LinearLayout mainScreen;
    
    private EditText edtKey;
    private TextView tvError;
    private TextView tvStatus;
    private TextView tvUptime;
    private TextView tvUserCount;
    private TextView tvSupport;
    private Button btnAction;
    private Button btnBypass;
    private ProgressDialog progressDialog;
    
    // API URL - DOMAIN RENDER CỦA BẠN
    private static final String API_URL = "https://roszmodxqanhno1.onrender.com/api/verify";
    private static final String WEB_URL = "https://roszmodxqanhno1.onrender.com/";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Root layout - nền đen
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF000000);
        root.setGravity(Gravity.CENTER);
        root.setPadding(30, 50, 30, 50);
        
        // ========== MÀN HÌNH LOGIN ==========
        loginScreen = new LinearLayout(this);
        loginScreen.setOrientation(LinearLayout.VERTICAL);
        loginScreen.setGravity(Gravity.CENTER);
        loginScreen.setVisibility(View.VISIBLE);
        
        // Title Premium
        TextView tvTitle = new TextView(this);
        tvTitle.setText("✦ DRAGON PINGX V1 PREMIUM ✦");
        tvTitle.setTextSize(24);
        tvTitle.setTextColor(0xFFB000FF);
        tvTitle.setGravity(Gravity.CENTER);
        tvTitle.setTypeface(null, Typeface.BOLD);
        tvTitle.setPadding(0, 0, 0, 10);
        tvTitle.setShadowLayer(15, 0, 0, 0xFFB000FF);
        
        // Verified
        TextView tvVerified = new TextView(this);
        tvVerified.setText("◈ CHÍNH THỨC | VERIFIED ◈");
        tvVerified.setTextSize(12);
        tvVerified.setTextColor(0xFFB000FF);
        tvVerified.setGravity(Gravity.CENTER);
        tvVerified.setPadding(0, 0, 0, 40);
        
        // Mô tả
        TextView tvDesc = new TextView(this);
        tvDesc.setText("⚡ Hệ thống kích hoạt bản quyền tự động");
        tvDesc.setTextSize(14);
        tvDesc.setTextColor(0xFF888888);
        tvDesc.setGravity(Gravity.CENTER);
        tvDesc.setPadding(0, 0, 0, 50);
        
        // Ô nhập key
        edtKey = new EditText(this);
        edtKey.setHint("🔑 NHẬP KEY BẢN QUYỀN");
        edtKey.setTextSize(16);
        edtKey.setTextColor(0xFFB000FF);
        edtKey.setHintTextColor(0xFF444444);
        edtKey.setGravity(Gravity.CENTER);
        edtKey.setPadding(50, 30, 50, 30);
        
        GradientDrawable editBg = new GradientDrawable();
        editBg.setShape(GradientDrawable.RECTANGLE);
        editBg.setCornerRadius(20);
        editBg.setColor(0xFF111111);
        editBg.setStroke(2, 0xFFB000FF);
        edtKey.setBackground(editBg);
        
        // Nút đăng nhập
        Button btnLogin = createHologramButton("🔓 KÍCH HOẠT →", 0xFFB000FF);
        btnLogin.setTextSize(16);
        btnLogin.setPadding(0, 20, 0, 20);
        
        // Nút GET KEY
        Button btnGetKey = createHologramOutlineButton("🎁 GET KEY NGAY", 0xFFB000FF);
        btnGetKey.setTextSize(14);
        btnGetKey.setPadding(0, 18, 0, 18);
        
        tvError = new TextView(this);
        tvError.setText("");
        tvError.setTextColor(0xFFB000FF);
        tvError.setGravity(Gravity.CENTER);
        tvError.setTextSize(12);
        tvError.setPadding(0, 20, 0, 0);
        
        loginScreen.addView(tvTitle);
        loginScreen.addView(tvVerified);
        loginScreen.addView(tvDesc);
        loginScreen.addView(edtKey);
        loginScreen.addView(btnLogin);
        loginScreen.addView(btnGetKey);
        loginScreen.addView(tvError);
        
        // ========== MÀN HÌNH CHÍNH ==========
        mainScreen = new LinearLayout(this);
        mainScreen.setOrientation(LinearLayout.VERTICAL);
        mainScreen.setGravity(Gravity.CENTER);
        mainScreen.setVisibility(View.GONE);
        
        // Header
        TextView tvMainTitle = new TextView(this);
        tvMainTitle.setText("✦ DRAGON PINGX V1 PREMIUM ✦");
        tvMainTitle.setTextSize(22);
        tvMainTitle.setTextColor(0xFFB000FF);
        tvMainTitle.setGravity(Gravity.CENTER);
        tvMainTitle.setTypeface(null, Typeface.BOLD);
        tvMainTitle.setPadding(0, 0, 0, 10);
        tvMainTitle.setShadowLayer(12, 0, 0, 0xFFB000FF);
        
        TextView tvMainVerified = new TextView(this);
        tvMainVerified.setText("◈ CHÍNH THỨC | VERIFIED ◈");
        tvMainVerified.setTextSize(11);
        tvMainVerified.setTextColor(0xFFB000FF);
        tvMainVerified.setGravity(Gravity.CENTER);
        tvMainVerified.setPadding(0, 0, 0, 30);
        
        TextView tvMainDesc = new TextView(this);
        tvMainDesc.setText("⚡ Hệ thống kích hoạt bản quyền tự động");
        tvMainDesc.setTextSize(13);
        tvMainDesc.setTextColor(0xFF888888);
        tvMainDesc.setGravity(Gravity.CENTER);
        
        TextView tvSlogan = new TextView(this);
        tvSlogan.setText("🔒 Bảo mật | ⚡ Nhanh chóng | ⭐ Uy tín");
        tvSlogan.setTextSize(11);
        tvSlogan.setTextColor(0xFF666666);
        tvSlogan.setGravity(Gravity.CENTER);
        tvSlogan.setPadding(0, 8, 0, 40);
        
        // Nút KHỞI CHẠY
        btnAction = createHologramButton("▶ KHỞI CHẠY", 0xFFB000FF);
        btnAction.setTextSize(15);
        btnAction.setPadding(0, 20, 0, 20);
        
        // Nút BYPASS
        btnBypass = createHologramOutlineButton("🔓 BYPASS", 0xFFB000FF);
        btnBypass.setTextSize(14);
        btnBypass.setPadding(0, 18, 0, 18);
        
        // Nút THÔNG TIN
        Button btnInfo = createHologramOutlineButton("ℹ THÔNG TIN", 0xFFB000FF);
        btnInfo.setTextSize(14);
        btnInfo.setPadding(0, 18, 0, 18);
        
        // TextView trạng thái
        tvStatus = new TextView(this);
        tvStatus.setText("⚡ Sẵn sàng");
        tvStatus.setTextSize(13);
        tvStatus.setTextColor(0xFFB000FF);
        tvStatus.setGravity(Gravity.CENTER);
        tvStatus.setPadding(0, 30, 0, 20);
        
        // 3 chỉ số
        LinearLayout statsRow = new LinearLayout(this);
        statsRow.setOrientation(LinearLayout.HORIZONTAL);
        statsRow.setPadding(0, 20, 0, 10);
        
        LinearLayout col1 = new LinearLayout(this);
        col1.setOrientation(LinearLayout.VERTICAL);
        col1.setGravity(Gravity.CENTER);
        col1.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        tvSupport = new TextView(this);
        tvSupport.setText("24/7");
        tvSupport.setTextSize(20);
        tvSupport.setTextColor(0xFFB000FF);
        tvSupport.setTypeface(null, Typeface.BOLD);
        TextView tvSupportLabel = new TextView(this);
        tvSupportLabel.setText("Hỗ trợ");
        tvSupportLabel.setTextSize(11);
        tvSupportLabel.setTextColor(0xFF666666);
        col1.addView(tvSupport);
        col1.addView(tvSupportLabel);
        
        LinearLayout col2 = new LinearLayout(this);
        col2.setOrientation(LinearLayout.VERTICAL);
        col2.setGravity(Gravity.CENTER);
        col2.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        tvUserCount = new TextView(this);
        tvUserCount.setText("1.2k+");
        tvUserCount.setTextSize(20);
        tvUserCount.setTextColor(0xFFB000FF);
        tvUserCount.setTypeface(null, Typeface.BOLD);
        TextView tvUserLabel = new TextView(this);
        tvUserLabel.setText("Người dùng");
        tvUserLabel.setTextSize(11);
        tvUserLabel.setTextColor(0xFF666666);
        col2.addView(tvUserCount);
        col2.addView(tvUserLabel);
        
        LinearLayout col3 = new LinearLayout(this);
        col3.setOrientation(LinearLayout.VERTICAL);
        col3.setGravity(Gravity.CENTER);
        col3.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        tvUptime = new TextView(this);
        tvUptime.setText("99.9%");
        tvUptime.setTextSize(20);
        tvUptime.setTextColor(0xFFB000FF);
        tvUptime.setTypeface(null, Typeface.BOLD);
        TextView tvUptimeLabel = new TextView(this);
        tvUptimeLabel.setText("Uptime");
        tvUptimeLabel.setTextSize(11);
        tvUptimeLabel.setTextColor(0xFF666666);
        col3.addView(tvUptime);
        col3.addView(tvUptimeLabel);
        
        statsRow.addView(col1);
        statsRow.addView(col2);
        statsRow.addView(col3);
        
        mainScreen.addView(tvMainTitle);
        mainScreen.addView(tvMainVerified);
        mainScreen.addView(tvMainDesc);
        mainScreen.addView(tvSlogan);
        mainScreen.addView(btnAction);
        mainScreen.addView(btnBypass);
        mainScreen.addView(btnInfo);
        mainScreen.addView(tvStatus);
        mainScreen.addView(statsRow);
        
        root.addView(loginScreen);
        root.addView(mainScreen);
        setContentView(root);
        
        // Kiểm tra key đã lưu
        SharedPreferences prefs = getSharedPreferences("DragonPrefs", MODE_PRIVATE);
        String savedKey = prefs.getString("user_key", "");
        
        if (!savedKey.isEmpty()) {
            checkKeyFromWeb(savedKey, true);
        }
        
        // ĐĂNG NHẬP
        btnLogin.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                final String key = edtKey.getText().toString().trim().toUpperCase();
                if (key.isEmpty()) {
                    tvError.setText("❌ Vui lòng nhập KEY bản quyền!");
                    tvError.startAnimation(shakeAnimation());
                } else {
                    checkKeyFromWeb(key, false);
                }
            }
        });
        
        // GET KEY
        btnGetKey.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent browser = new Intent(Intent.ACTION_VIEW, Uri.parse(WEB_URL));
                startActivity(browser);
            }
        });
        
        // KHỞI CHẠY/DỪNG
        btnAction.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!isRunning) {
                    isRunning = true;
                    btnAction.setText("⏹ DỪNG");
                    GradientDrawable newBg = new GradientDrawable();
                    newBg.setShape(GradientDrawable.RECTANGLE);
                    newBg.setCornerRadius(35);
                    newBg.setColor(0xFFB000FF);
                    btnAction.setBackground(newBg);
                    tvStatus.setText("🟣 ĐANG PING...");
                    pingCount = 0;
                    
                    pingTimer = new Timer();
                    pingTimer.schedule(new TimerTask() {
                        @Override
                        public void run() {
                            pingCount++;
                            handler.post(new Runnable() {
                                @Override
                                public void run() {
                                    tvStatus.setText("🟣 Đã ping: " + pingCount + " lần");
                                }
                            });
                        }
                    }, 0, 1000);
                    Toast.makeText(MainActivity.this, "🚀 Bắt đầu ping!", Toast.LENGTH_SHORT).show();
                } else {
                    isRunning = false;
                    btnAction.setText("▶ KHỞI CHẠY");
                    GradientDrawable newBg = new GradientDrawable();
                    newBg.setShape(GradientDrawable.RECTANGLE);
                    newBg.setCornerRadius(35);
                    newBg.setColor(0xFFB000FF);
                    btnAction.setBackground(newBg);
                    tvStatus.setText("⚫ Đã dừng");
                    if (pingTimer != null) {
                        pingTimer.cancel();
                        pingTimer = null;
                    }
                    Toast.makeText(MainActivity.this, "⏹️ Đã dừng ping!", Toast.LENGTH_SHORT).show();
                }
            }
        });
        
        // BYPASS
        btnBypass.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!isBypassed) {
                    isBypassed = true;
                    GradientDrawable bypassSuccessBg = new GradientDrawable();
                    bypassSuccessBg.setShape(GradientDrawable.RECTANGLE);
                    bypassSuccessBg.setCornerRadius(35);
                    bypassSuccessBg.setColor(0xFFB000FF);
                    btnBypass.setBackground(bypassSuccessBg);
                    btnBypass.setTextColor(0xFFFFFFFF);
                    btnBypass.setText("✓ ĐÃ BYPASS");
                    Toast.makeText(MainActivity.this, "✅ Đã bypass thành công!", Toast.LENGTH_LONG).show();
                } else {
                    Toast.makeText(MainActivity.this, "🔓 Bạn đã bypass rồi!", Toast.LENGTH_SHORT).show();
                }
            }
        });
        
        // THÔNG TIN
        btnInfo.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                AlertDialog.Builder builder = new AlertDialog.Builder(MainActivity.this);
                builder.setTitle("📱 THÔNG TIN APP");
                builder.setMessage(
                    "✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦\n" +
                    "     🟣 DRAGON PINGX V1 PREMIUM\n" +
                    "✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦\n\n" +
                    "👑 ADMIN:\n" +
                    "   ✦ QANHXMOD\n" +
                    "   ✦ RoszGumball\n" +
                    "   ✦ StockAnv MOD VIP PRO\n" +
                    "   ✦ THANHDO BÁ SÀN\n\n" +
                    "────────────────────────\n" +
                    "📱 TikTok: @QANHXMOD\n" +
                    "📨 Telegram: @QANH NO1\n" +
                    "🌐 Web: roszmodxqanhno1.onrender.com\n" +
                    "💬 Hỗ trợ: 24/7\n" +
                    "────────────────────────"
                );
                builder.setPositiveButton("ĐÓNG", null);
                builder.show();
            }
        });
    }
    
    // Hàm check key từ web API
    private void checkKeyFromWeb(final String key, final boolean isAutoCheck) {
        progressDialog = new ProgressDialog(this);
        progressDialog.setMessage("🟣 Đang kiểm tra KEY...");
        progressDialog.setCancelable(false);
        progressDialog.show();
        
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url = new URL(API_URL);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setDoOutput(true);
                    conn.setConnectTimeout(15000);
                    conn.setReadTimeout(15000);
                    
                    JSONObject json = new JSONObject();
                    json.put("key", key);
                    
                    OutputStream os = conn.getOutputStream();
                    os.write(json.toString().getBytes("UTF-8"));
                    os.flush();
                    os.close();
                    
                    int responseCode = conn.getResponseCode();
                    if (responseCode == HttpURLConnection.HTTP_OK) {
                        BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                        StringBuilder response = new StringBuilder();
                        String line;
                        while ((line = br.readLine()) != null) {
                            response.append(line);
                        }
                        br.close();
                        
                        final JSONObject result = new JSONObject(response.toString());
                        final String status = result.getString("status");
                        
                        handler.post(new Runnable() {
                            @Override
                            public void run() {
                                progressDialog.dismiss();
                                
                                if (status.equals("success")) {
                                    SharedPreferences prefs = getSharedPreferences("DragonPrefs", MODE_PRIVATE);
                                    prefs.edit().putString("user_key", key).apply();
                                    
                                    loginScreen.setVisibility(View.GONE);
                                    mainScreen.setVisibility(View.VISIBLE);
                                    Toast.makeText(MainActivity.this, "✅ Kích hoạt thành công!", Toast.LENGTH_SHORT).show();
                                } else if (status.equals("expired")) {
                                    tvError.setText("❌ KEY đã hết hạn! Vui lòng gia hạn.");
                                    tvError.startAnimation(shakeAnimation());
                                    if (isAutoCheck) {
                                        SharedPreferences prefs = getSharedPreferences("DragonPrefs", MODE_PRIVATE);
                                        prefs.edit().remove("user_key").apply();
                                    }
                                } else if (status.equals("used")) {
                                    tvError.setText("❌ KEY đã được sử dụng!");
                                    tvError.startAnimation(shakeAnimation());
                                    if (isAutoCheck) {
                                        SharedPreferences prefs = getSharedPreferences("DragonPrefs", MODE_PRIVATE);
                                        prefs.edit().remove("user_key").apply();
                                    }
                                } else {
                                    tvError.setText("❌ KEY không hợp lệ! Vui lòng GET KEY trên web.");
                                    tvError.startAnimation(shakeAnimation());
                                    if (isAutoCheck) {
                                        SharedPreferences prefs = getSharedPreferences("DragonPrefs", MODE_PRIVATE);
                                        prefs.edit().remove("user_key").apply();
                                    }
                                }
                            }
                        });
                    } else {
                        throw new Exception("Server error");
                    }
                    conn.disconnect();
                    
                } catch (Exception e) {
                    handler.post(new Runnable() {
                        @Override
                        public void run() {
                            progressDialog.dismiss();
                            tvError.setText("❌ Không thể kết nối server! Kiểm tra mạng.");
                            tvError.startAnimation(shakeAnimation());
                            if (isAutoCheck) {
                                SharedPreferences prefs = getSharedPreferences("DragonPrefs", MODE_PRIVATE);
                                prefs.edit().remove("user_key").apply();
                                loginScreen.setVisibility(View.VISIBLE);
                                mainScreen.setVisibility(View.GONE);
                            }
                        }
                    });
                }
            }
        }).start();
    }
    
    // Tạo nút hologram tím đặc
    private Button createHologramButton(String text, int color) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(0xFFFFFFFF);
        button.setTypeface(null, Typeface.BOLD);
        button.setAllCaps(false);
        
        GradientDrawable bg = new GradientDrawable();
        bg.setShape(GradientDrawable.RECTANGLE);
        bg.setCornerRadius(35);
        bg.setColor(color);
        button.setBackground(bg);
        
        button.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        button.setAlpha(0.7f);
                        break;
                    case MotionEvent.ACTION_UP:
                        button.setAlpha(1.0f);
                        break;
                }
                return false;
            }
        });
        
        return button;
    }
    
    // Tạo nút hologram viền tím
    private Button createHologramOutlineButton(String text, int color) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(color);
        button.setTypeface(null, Typeface.BOLD);
        button.setAllCaps(false);
        
        GradientDrawable bg = new GradientDrawable();
        bg.setShape(GradientDrawable.RECTANGLE);
        bg.setCornerRadius(35);
        bg.setColor(0xFF111111);
        bg.setStroke(2, color);
        button.setBackground(bg);
        
        button.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        button.setAlpha(0.7f);
                        break;
                    case MotionEvent.ACTION_UP:
                        button.setAlpha(1.0f);
                        break;
                }
                return false;
            }
        });
        
        return button;
    }
    
    private Animation shakeAnimation() {
        TranslateAnimation shake = new TranslateAnimation(0, 10, 0, 0);
        shake.setDuration(80);
        shake.setRepeatMode(Animation.REVERSE);
        shake.setRepeatCount(3);
        return shake;
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (pingTimer != null) {
            pingTimer.cancel();
        }
    }
}