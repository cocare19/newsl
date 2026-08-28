import sys
import os

# การันตี Path โฟลเดอร์ปัจจุบันสำหรับระบบ Import โมดูลย่อยทั้งหมด
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import urllib.parse
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pytz

# นำเข้าโมดูลย่อยและโมดูล RSS ที่แยกออกมา
from config import CUSTOM_CSS
from data_loader import (
    fetch_gold_and_spot_data, fetch_thai_oil, get_historical_thai_oil_data,
    fetch_real_historical_oil_table, fetch_today_oil_all_brands,
    fetch_macro_indicators, fetch_tech_ai_stocks, fetch_skysports_standings,
    fetch_skysports_fixtures
)
from rss_module import render_rss_page
from tech_hub_module import render_tech_hub_page  # Media & Playlist Module
try:
    from youtube_search_module import render_youtube_search_page  # YouTube Search & Explorer Module
except ImportError:
    import youtube_search_module
    render_youtube_search_page = youtube_search_module.render_youtube_search_page

st.set_page_config(page_title="NewsL Lite Matrix", page_icon="⚡", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- ระบบล็อกรหัสผ่านความปลอดภัย (Private Password Gatekeeper) ---
target_pwd = st.secrets.get("APP_PASSWORD", "9999")
if not st.session_state.get("authenticated", False):
    st.markdown("""
        <div style='max-width: 460px; margin: 60px auto 10px auto; text-align: center;'>
            <div style='font-size: 3.2rem; margin-bottom: 8px;'>⚡</div>
            <h2 style='margin-bottom: 6px; font-weight: 800; background: linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #6366F1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                NewsL • Real-Time Hub
            </h2>
            <p style='color: #64748B; font-size: 0.88rem; margin-bottom: 25px;'>
                🔒 Private Intelligence Matrix • กรุณากรอกรหัสผ่านเพื่อเข้าใช้งาน
            </p>
        </div>
    """, unsafe_allow_html=True)

    login_col1, login_col2, login_col3 = st.columns([1, 1.6, 1])
    with login_col2:
        with st.form("login_form", clear_on_submit=False):
            pwd_input = st.text_input("🔑 รหัสผ่านเข้าสู่ระบบ (Password):", type="password", placeholder="กรอกรหัสผ่านของคุณ...", key="app_pwd_input")
            submit_btn = st.form_submit_button("🚀 ปลดล็อกและเข้าสู่ระบบ", use_container_width=True)

            if submit_btn:
                if pwd_input == str(target_pwd):
                    st.session_state["authenticated"] = True
                    st.success("✅ รหัสผ่านถูกต้อง กำลังเปิดระบบ...")
                    st.rerun()
                else:
                    st.error("❌ รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")

    st.stop()

# เมนูนำทางด้านข้าง
with st.sidebar:
    st.markdown("""
        <div style='margin-bottom: 10px;'>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span style='font-size: 1.35rem;'>⚡</span>
                <span style='font-size: 1.20rem; font-weight: 700; color: #0F172A; letter-spacing: -0.01em;'>NewsL Real-Time Hub</span>
            </div>
            <p style='color: #10B981; font-size: 0.76rem; font-weight: 600; margin: 4px 0 0 2px;'>🟢 100% Free • Zero-API-Key Mode</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; margin-top: 12px; margin-bottom: 6px;'>NAVIGATION MENU</p>", unsafe_allow_html=True)
    menu_selection = st.radio(
        label="Select Page",
        options=[
            "📈 1. Real-Time Market & Pricing",
            "🏆 2. Premier League Tables",
            "📅 3. Premier League Fixtures",
            "📡 4. Curated RSS Feeds",
            "📺 5. Media & Video Hub",
            "🔍 6. YouTube Search Hub"
        ]
    )

    st.markdown("---")
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; margin-bottom: 6px;'>DISPLAY & FONT SETTINGS</p>", unsafe_allow_html=True)
    font_size_choice = st.radio(
        label="Font Size:",
        options=["Compact", "Normal", "Large"],
        index=1,
        key="app_font_size_ctrl"
    )

    st.markdown("---")
    if st.button("🔒 ล็อกระบบ (Logout)", use_container_width=True, key="btn_logout"):
        st.session_state["authenticated"] = False
        st.rerun()

# ปรับขนาดตัวอักษรทั้งหน้าจอแบบ Dynamic CSS
if font_size_choice == "Compact":
    st.markdown("""
        <style>
        html, body, [class*="css"], .stMarkdown, .stText, p, span, div, table, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            font-size: 0.86rem !important;
        }
        h1, [data-testid="stMarkdownContainer"] h1 { font-size: 1.25rem !important; }
        h2, [data-testid="stMarkdownContainer"] h2 { font-size: 1.12rem !important; }
        h3, [data-testid="stMarkdownContainer"] h3 { font-size: 1.02rem !important; }
        h4, [data-testid="stMarkdownContainer"] h4 { font-size: 0.92rem !important; }
        h5, [data-testid="stMarkdownContainer"] h5 { font-size: 0.84rem !important; }
        .stMetric [data-testid="stMetricValue"] { font-size: 1.22rem !important; }
        </style>
    """, unsafe_allow_html=True)
elif font_size_choice == "Large":
    st.markdown("""
        <style>
        html, body, [class*="css"], .stMarkdown, .stText, p, span, div, table {
            font-size: 1.05rem !important;
        }
        h1, [data-testid="stMarkdownContainer"] h1 { font-size: 1.65rem !important; }
        h2, [data-testid="stMarkdownContainer"] h2 { font-size: 1.42rem !important; }
        h3, [data-testid="stMarkdownContainer"] h3 { font-size: 1.26rem !important; }
        h4, [data-testid="stMarkdownContainer"] h4 { font-size: 1.14rem !important; }
        h5, [data-testid="stMarkdownContainer"] h5 { font-size: 1.02rem !important; }
        .stMetric [data-testid="stMetricValue"] { font-size: 1.60rem !important; }
        .stMetric [data-testid="stMetricLabel"] { font-size: 0.95rem !important; }
        </style>
    """, unsafe_allow_html=True)

# ส่วนหัวหลักของ Dashboard (สวยงาม กะทัดรัด โมเดิร์น คมชัดทั้ง Light & Dark Mode)
st.markdown("""
    <div style="margin-top: -15px; margin-bottom: 22px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 2px;">
            <span style="font-size: 1.6rem; line-height: 1;">⚡</span>
            <span style="font-size: 1.55rem; font-weight: 800; letter-spacing: -0.02em; background: linear-gradient(135deg, #0284C7 0%, #2563EB 45%, #6366F1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                NewsL • Real-Time Intelligence Matrix
            </span>
        </div>
        <p style="color: #64748B; font-size: 0.88rem; margin: 0; padding-left: 2px; font-weight: 400;">
            ระบบศูนย์ข้อมูลและสารสนเทศเรียลไทม์รอบโลก (100% Free • Zero-API-Key Edition)
        </p>
    </div>
""", unsafe_allow_html=True)

# --- 1. REAL-TIME MARKET ---
if menu_selection == "📈 1. Real-Time Market & Pricing":
    tz_bkk = pytz.timezone('Asia/Bangkok')
    now_bkk = datetime.now(tz_bkk).strftime('%d/%m/%Y เวลา %H:%M:%S น.')
    st.markdown("#### 📈 Real-Time Asset, Gold, Thai Fuel & Tech Markets")
    st.caption(f"🕒 อัปเดตข้อมูลสด ณ เวลา: **{now_bkk}**")

    if st.button("🔄 รีเฟรชราคาทองคำ, น้ำมันไทย และตลาดโลกสด", key="btn_market_refresh"):
        st.cache_data.clear()

    st.markdown("### 🥇 ราคาทองคำแท่งไทย & ค่าเงินบาท")
    gold_info = fetch_gold_and_spot_data()
    g_cols = st.columns(3)
    g_cols[0].metric("ทองคำแท่ง 96.5% (ขายออก)", f"{gold_info['sell']} ฿", delta="สมาคมค้าทองคำ")
    g_cols[1].metric("ทองคำแท่ง 96.5% (รับซื้อ)", f"{gold_info['buy']} ฿", delta="สมาคมค้าทองคำ")
    g_cols[2].metric(
        "อัตราแลกเปลี่ยน USD/THB (OANDA)", 
        gold_info.get('usd_thb', 'N/A'), 
        delta=gold_info.get('usd_thb_diff') or "OANDA Live"
    )

    st.markdown("---")
    st.markdown("### 🌍 เปรียบเทียบราคา Gold Spot (XAU/USD) ตามแหล่งข้อมูลสด")
    spot_cols = st.columns(3)
    spot_cols[0].metric(
        "🥇 XAU/USD (OANDA)", 
        gold_info.get('oanda_spot', 'N/A'), 
        delta=gold_info.get('oanda_diff') or "OANDA SG / Global"
    )
    spot_cols[1].metric(
        "🌐 XAU/USD (FXStreet)", 
        gold_info.get('fxstreet_spot', 'N/A'), 
        delta=gold_info.get('fxstreet_diff') or "FXStreet Interbank"
    )
    spot_cols[2].metric(
        "🇨🇭 XAU/USD (Swissquote)", 
        gold_info.get('swissquote_spot', 'N/A'), 
        delta="Swissquote Bank Live Feed"
    )

    # ปุ่มลิงก์ไปยังแหล่งข้อมูลอ้างอิงตรง
    src_c1, src_c2, src_c3, src_c4 = st.columns(4)
    with src_c1:
        st.link_button("🌐 OANDA: XAU/USD", "https://www.oanda.com/sg-en/trading/instruments/xau-usd/")
    with src_c2:
        st.link_button("🌐 OANDA: USD/THB", "https://www.oanda.com/sg-en/trading/instruments/usd-thb/")
    with src_c3:
        st.link_button("🌐 FXStreet: Gold", "https://www.fxstreet.com/rates-charts/xauusd")
    with src_c4:
        st.link_button("🌐 ทองคำราคา.com", "https://xn--42cah7d0cxcvbbb9x.com/ราคาทองประจำวัน/")

    # Interactive Widget จาก OANDA & TradingView
    with st.expander("📈 ดูกราฟราคาทองคำ & ค่าเงินบาทเรียลไทม์ (Multi-Chart)", expanded=False):
        chart_tab1, chart_tab2, chart_tab3 = st.tabs([
            "📊 เปรียบเทียบ ทองคำ & เงินบาท (บน-ล่าง)",
            "🥇 ทองคำตลาดโลก XAU/USD (OANDA)",
            "🇹🇭 อัตราแลกเปลี่ยน USD/THB (OANDA)"
        ])
        
        with chart_tab1:
            st.caption("กราฟราคาทองคำตลาดโลก (บน) และอัตราแลกเปลี่ยนเงินบาท (ล่าง) เรียงซ้อนเพื่อเปรียบเทียบเรียลไทม์")
            double_chart_html = """
            <div style="display: flex; flex-direction: column; gap: 15px; height: 720px; width: 100%;">
                <div class="tradingview-widget-container" style="flex: 1; min-height: 340px;">
                    <div id="tv_gold_top" style="height:100%;width:100%"></div>
                </div>
                <div class="tradingview-widget-container" style="flex: 1; min-height: 340px;">
                    <div id="tv_thb_bottom" style="height:100%;width:100%"></div>
                </div>
            </div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({
                "autosize": true,
                "symbol": "OANDA:XAUUSD",
                "interval": "D",
                "timezone": "Asia/Bangkok",
                "theme": "light",
                "style": "1",
                "locale": "th_TH",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_top_toolbar": true,
                "save_image": false,
                "container_id": "tv_gold_top"
            });
            new TradingView.widget({
                "autosize": true,
                "symbol": "OANDA:USDTHB",
                "interval": "D",
                "timezone": "Asia/Bangkok",
                "theme": "light",
                "style": "1",
                "locale": "th_TH",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_top_toolbar": true,
                "save_image": false,
                "container_id": "tv_thb_bottom"
            });
            </script>
            """
            components.html(double_chart_html, height=730)
            
        with chart_tab2:
            st.caption("กราฟวิเคราะห์ราคาทองคำตลาดโลก (XAU/USD) แบบโต้ตอบได้")
            tv_gold_html = """
            <div class="tradingview-widget-container" style="height:400px;width:100%">
              <div id="tradingview_gold_detailed" style="height:calc(100% - 32px);width:100%"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({
                "autosize": true,
                "symbol": "OANDA:XAUUSD",
                "interval": "15",
                "timezone": "Asia/Bangkok",
                "theme": "light",
                "style": "1",
                "locale": "th_TH",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_top_toolbar": false,
                "save_image": false,
                "container_id": "tradingview_gold_detailed"
              });
              </script>
            </div>
            """
            components.html(tv_gold_html, height=420)
            
        with chart_tab3:
            st.caption("กราฟวิเคราะห์อัตราแลกเปลี่ยนค่าเงินบาท (USD/THB) แบบโต้ตอบได้")
            tv_thb_html = """
            <div class="tradingview-widget-container" style="height:400px;width:100%">
              <div id="tradingview_thb_detailed" style="height:calc(100% - 32px);width:100%"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({
                "autosize": true,
                "symbol": "FX_IDC:USDTHB",
                "interval": "D",
                "timezone": "Asia/Bangkok",
                "theme": "light",
                "style": "1",
                "locale": "th_TH",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_top_toolbar": false,
                "save_image": false,
                "container_id": "tradingview_thb_detailed"
              });
              </script>
            </div>
            """
            components.html(tv_thb_html, height=420)
            
    st.markdown("---")
    st.markdown("### 💧 ราคาน้ำมันขายปลีกในประเทศ & สรุปราคาพรุ่งนี้")
    oil_data = fetch_thai_oil()
    oil_details = oil_data.get("_details", {})
    remark = oil_data.get("_remark", "")
    today_all_brands = fetch_today_oil_all_brands()
    
    # ตรวจสอบการปรับราคาล่วงหน้าพรุ่งนี้
    price_up_fuels = []
    price_down_fuels = []
    for k, v in oil_details.items():
        d_tom = v.get('diff_tom', 0.0)
        if d_tom > 0:
            price_up_fuels.append(f"{k} (+{d_tom:.2f} ฿)")
        elif d_tom < 0:
            price_down_fuels.append(f"{k} ({d_tom:.2f} ฿)")
            
    if price_up_fuels:
        st.error(f"🚨 **แจ้งเตือนด่วน: พรุ่งนี้ราคาน้ำมันปรับขึ้น!** แนะนำรีบไปเติมน้ำมันวันนี้ก่อน 05:00 น. วันพรุ่งนี้ครับ\n\n📌 รายการปรับขึ้น: {', '.join(price_up_fuels)} — *{remark}*")
    elif price_down_fuels:
        st.success(f"💚 **แจ้งเตือน: พรุ่งนี้ราคาน้ำมันปรับลดลง!** แนะนำให้อดใจรอเติมพรุ่งนี้หลัง 05:00 น. เพื่อประหยัดเงินครับ\n\n📌 รายการปรับลด: {', '.join(price_down_fuels)} — *{remark}*")
    elif remark:
        st.caption(f"📌 {remark} (สถานะพรุ่งนี้: ยังไม่มีการประกาศปรับราคา สามารถเติมได้ตามปกติ)")

    # แมปไอคอนน่ารักๆ ประจำแต่ละประเภทน้ำมัน
    fuel_icons_map = {
        "แก๊สโซฮอล์ 95": "🚗 แก๊สโซฮอล์ 95",
        "แก๊สโซฮอล์ 91": "🚙 แก๊สโซฮอล์ 91",
        "แก๊สโซฮอล์ E20": "🌱 แก๊สโซฮอล์ E20",
        "ดีเซล": "🚛 ดีเซล",
        "ไฮ พรีเมียม 98 พลัส": "💎 ไฮ พรีเมียม 98",
        "ไฮ พรีเมียม ดีเซล พลัส": "⚡ ดีเซล พรีเมียม",
        "แก๊สโซฮอล์ E85": "🍃 แก๊สโซฮอล์ E85",
        "ดีเซล B20": "🚜 ดีเซล B20"
    }

    # แสดง Metric Cards น้ำมัน 8 ประเภท (สไตล์ Macro Drivers สะอาด สบายตา ไม่รก)
    fuel_cols1 = st.columns(4)
    oils_row1 = ["แก๊สโซฮอล์ 95", "แก๊สโซฮอล์ 91", "แก๊สโซฮอล์ E20", "ดีเซล"]
    for i, o_name in enumerate(oils_row1):
        info = oil_details.get(o_name, {})
        price_val = oil_data.get(o_name, "0.00")
        label_with_icon = fuel_icons_map.get(o_name, o_name)
        try:
            today_p = float(info.get('today', price_val))
        except (ValueError, TypeError):
            today_p = 0.0
        try:
            tom_p = float(info.get('tomorrow', today_p))
        except (ValueError, TypeError):
            tom_p = today_p
        try:
            diff_tom = float(info.get('diff_tom', 0.0))
        except (ValueError, TypeError):
            diff_tom = 0.0
            
        with fuel_cols1[i]:
            if diff_tom > 0:
                st.metric(
                    label=label_with_icon,
                    value=f"{price_val} ฿",
                    delta=f"+{diff_tom:.2f} ฿ (พรุ่งนี้ {tom_p:.2f} ฿)",
                    delta_color="inverse"
                )
            elif diff_tom < 0:
                st.metric(
                    label=label_with_icon,
                    value=f"{price_val} ฿",
                    delta=f"{diff_tom:.2f} ฿ (พรุ่งนี้ {tom_p:.2f} ฿)",
                    delta_color="inverse"
                )
            else:
                st.metric(
                    label=label_with_icon,
                    value=f"{price_val} ฿",
                    delta=f"พรุ่งนี้: {tom_p:.2f} ฿ (คงเดิม)",
                    delta_color="off"
                )

    fuel_cols2 = st.columns(4)
    oils_row2 = ["ไฮ พรีเมียม 98 พลัส", "ไฮ พรีเมียม ดีเซล พลัส", "แก๊สโซฮอล์ E85", "ดีเซล B20"]
    for i, o_name in enumerate(oils_row2):
        info = oil_details.get(o_name, {})
        price_val = oil_data.get(o_name, "0.00")
        label_with_icon = fuel_icons_map.get(o_name, o_name)
        try:
            today_p = float(info.get('today', price_val))
        except (ValueError, TypeError):
            today_p = 0.0
        try:
            tom_p = float(info.get('tomorrow', today_p))
        except (ValueError, TypeError):
            tom_p = today_p
        try:
            diff_tom = float(info.get('diff_tom', 0.0))
        except (ValueError, TypeError):
            diff_tom = 0.0
            
        with fuel_cols2[i]:
            if diff_tom > 0:
                st.metric(
                    label=label_with_icon,
                    value=f"{price_val} ฿",
                    delta=f"+{diff_tom:.2f} ฿ (พรุ่งนี้ {tom_p:.2f} ฿)",
                    delta_color="inverse"
                )
            elif diff_tom < 0:
                st.metric(
                    label=label_with_icon,
                    value=f"{price_val} ฿",
                    delta=f"{diff_tom:.2f} ฿ (พรุ่งนี้ {tom_p:.2f} ฿)",
                    delta_color="inverse"
                )
            else:
                st.metric(
                    label=label_with_icon,
                    value=f"{price_val} ฿",
                    delta=f"พรุ่งนี้: {tom_p:.2f} ฿ (คงเดิม)",
                    delta_color="off"
                )

    # 1. ตารางเปรียบเทียบราคาน้ำมันวันนี้ทุกปั๊ม + คอลัมน์ 'พรุ่งนี้' ท้ายสุด (ทองคำราคา.com)
    with st.expander("🏢 **ตารางเปรียบเทียบราคาน้ำมันวันนี้ทุกปั๊ม & ราคาน้ำมันพรุ่งนี้**", expanded=True):
        st.caption("🌐 ข้อมูลอ้างอิงจาก https://xn--42cah7d0cxcvbbb9x.com/ราคาน้ำมันวันนี้/ (ทองคำราคา.com)")
        if not today_all_brands.empty:
            df_table_show = today_all_brands.rename(columns={
                "ประเภทน้ำมัน": "💧 ประเภทน้ำมัน",
                "ปตท.": "🔵 ปตท.",
                "บางจาก": "🟢 บางจาก",
                "เชลล์": "🟡 เชลล์",
                "คาลเท็กซ์": "⭐ คาลเท็กซ์",
                "ไออาร์พีซี": "🔷 IRPC",
                "พีที": "🟠 PT",
                "ซัสโก้": "🟡 ซัสโก้",
                "เพียว": "🔵 เพียว",
                "พรุ่งนี้": "✨ พรุ่งนี้"
            })
            st.dataframe(
                df_table_show,
                hide_index=True,
                column_config={
                    "💧 ประเภทน้ำมัน": st.column_config.TextColumn("💧 ประเภทน้ำมัน", width="medium"),
                    "🔵 ปตท.": st.column_config.TextColumn("🔵 ปตท."),
                    "🟢 บางจาก": st.column_config.TextColumn("🟢 บางจาก"),
                    "🟡 เชลล์": st.column_config.TextColumn("🟡 เชลล์"),
                    "⭐ คาลเท็กซ์": st.column_config.TextColumn("⭐ คาลเท็กซ์"),
                    "🔷 IRPC": st.column_config.TextColumn("🔷 IRPC"),
                    "🟠 PT": st.column_config.TextColumn("🟠 PT"),
                    "🟡 ซัสโก้": st.column_config.TextColumn("🟡 ซัสโก้"),
                    "🔵 เพียว": st.column_config.TextColumn("🔵 เพียว"),
                    "✨ พรุ่งนี้": st.column_config.TextColumn("✨ พรุ่งนี้ (Tomorrow)", width="medium")
                }
            )
        else:
            st.info("กำลังโหลดตารางเปรียบเทียบราคาปั๊ม...")

    # 2. Interactive Toggle Oil Price Chart & Historical Table (คงสถานะเปิดไว้ตลอดเวลาที่ปรับแต่งค่า ไม่ยุบหายเอง)
    show_oil_chart = st.toggle(
        "📈 ดูกราฟแนวโน้ม & ตารางบันทึกราคาน้ำมันย้อนหลังจริง (ปี 2569 / ทองคำราคา.com)",
        value=False,
        key="oil_chart_toggle"
    )
    
    if show_oil_chart:
        with st.container(border=True):
            oil_tab_chart, oil_tab_table = st.tabs([
                "📈 กราฟแนวโน้มรายวัน (Step Chart ปี 2569)",
                "📋 ตารางประวัติการปรับราคาจริง (ทองคำราคา.com)"
            ])
            
            with oil_tab_chart:
                st.caption("🌐 ข้อมูลสกัดจากประวัติการปรับราคาจริง — เชื่อมโยงราคาทุกวันอย่างต่อเนื่อง (ช่วงราคาไม่เปลี่ยนจะคงที่ และกระโดดในวันที่มีการประกาศปรับราคา)")
                
                # ตัวเลือกกรอบเวลาและประเภทน้ำมัน
                ctl_col1, ctl_col2 = st.columns([1, 2.5])
                with ctl_col1:
                    timeframe_choice = st.selectbox(
                        "⏳ เลือกช่วงเวลาย้อนหลัง:",
                        options=["ปี 2569 ทั้งหมด (ปีปัจจุบัน)", "1 เดือน (30 วัน)", "3 เดือน (90 วัน)", "6 เดือน (180 วัน)"],
                        index=0,
                        key="oil_timeframe_selector"
                    )
                
                days_map = {
                    "ปี 2569 ทั้งหมด (ปีปัจจุบัน)": None,
                    "1 เดือน (30 วัน)": 30,
                    "3 เดือน (90 วัน)": 90,
                    "6 เดือน (180 วัน)": 180
                }
                selected_days = days_map.get(timeframe_choice, None)
                
                # ดึงข้อมูลประวัติราคาน้ำมันรายวันต่อเนื่อง
                hist_oil_df = get_historical_thai_oil_data(oil_data, days_back=selected_days, year_be=2569)
                
                oil_types_all = [
                    "แก๊สโซฮอล์ 95", "แก๊สโซฮอล์ 91", "แก๊สโซฮอล์ E20", "ดีเซล", 
                    "ไฮ พรีเมียม 98 พลัส", "ไฮ พรีเมียม ดีเซล พลัส", "เบนซิน 95", "แก๊สโซฮอล์ E85", "ดีเซล B20"
                ]
                # กรองเฉพาะประเภทที่มีใน DataFrame
                avail_chart_oils = [o for o in oil_types_all if o in hist_oil_df.columns]
                default_selected = [o for o in ["แก๊สโซฮอล์ 95", "แก๊สโซฮอล์ 91", "แก๊สโซฮอล์ E20", "ดีเซล"] if o in avail_chart_oils]
                
                with ctl_col2:
                    selected_oils = st.multiselect(
                        "⛽ เลือกประเภทน้ำมันเพื่อเปรียบเทียบแนวโน้ม:",
                        options=avail_chart_oils,
                        default=default_selected if default_selected else avail_chart_oils[:4],
                        key="oil_chart_selector"
                    )
                
                if not hist_oil_df.empty and selected_oils:
                    # ละลายแกนข้อมูลให้เป็นรูปแบบ Long-form สำหรับ Plotly
                    df_melted = hist_oil_df.melt(id_vars=["Date"], value_vars=selected_oils, var_name="ประเภทน้ำมัน", value_name="ราคา (บาท/ลิตร)")
                    
                    import plotly.express as px
                    
                    fig_oil = px.line(
                        df_melted,
                        x="Date",
                        y="ราคา (บาท/ลิตร)",
                        color="ประเภทน้ำมัน",
                        markers=True,
                        color_discrete_map={
                            "แก๊สโซฮอล์ 95": "#EF4444",           # แดงส้มสด
                            "แก๊สโซฮอล์ 91": "#F59E0B",           # ส้มเหลือง
                            "แก๊สโซฮอล์ E20": "#10B981",          # เขียวรักษ์โลก
                            "ดีเซล": "#2563EB",                   # น้ำเงินพรีเมียม
                            "ไฮ พรีเมียม 98 พลัส": "#EC4899",     # ชมพูพรีเมียม
                            "ไฮ พรีเมียม ดีเซล พลัส": "#06B6D4",   # ฟ้าพรีเมียม
                            "เบนซิน 95": "#E11D48",               # แดงเข้ม
                            "แก๊สโซฮอล์ E85": "#8B5CF6",          # ม่วง
                            "ดีเซล B20": "#64748B"                # เทาเข้ม
                        },
                        line_shape="hv"
                    )
                    
                    # ปรับแต่งความสวยงามของกราฟสไตล์ล้ำสมัย (Premium Minimalist Theme)
                    fig_oil.update_layout(
                        font_family="'Plus Jakarta Sans', 'Prompt', sans-serif",
                        plot_bgcolor="rgba(255,255,255,0.9)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        hovermode="x unified",
                        margin=dict(l=40, r=40, t=25, b=40),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            title=None
                        ),
                        xaxis=dict(
                            title="วันที่",
                            gridcolor="#F1F5F9",
                            showgrid=True,
                            linecolor="#E2E8F0"
                        ),
                        yaxis=dict(
                            title="ราคาขายปลีก (บาท/ลิตร)",
                            gridcolor="#E2E8F0",
                            showgrid=True,
                            zeroline=False,
                            linecolor="#E2E8F0"
                        )
                    )
                    fig_oil.update_traces(
                        marker=dict(size=4),
                        hovertemplate="<b>%{y:.2f} บาท/ลิตร</b><extra></extra>"
                    )
                    st.plotly_chart(fig_oil, width="stretch")
                elif hist_oil_df.empty:
                    st.info("กำลังโหลดข้อมูลประวัติราคาน้ำมัน...")
                else:
                    st.warning("🚨 กรุณาเลือกประเภทน้ำมันอย่างน้อย 1 ประเภทเพื่อแสดงกราฟแนวโน้มครับ")
            
            with oil_tab_table:
                st.caption("📋 ข้อมูลดึงตรงจาก https://xn--42cah7d0cxcvbbb9x.com/ราคาน้ำมันย้อนหลัง/ (เฉพาะรอบที่มีการประกาศปรับราคา)")
                raw_oil_table = fetch_real_historical_oil_table()
                if not raw_oil_table.empty:
                    # แสดงเฉพาะปี 2569 เป็นค่าเริ่มต้น
                    filter_col1, filter_col2 = st.columns([1, 2])
                    with filter_col1:
                        available_years = sorted(raw_oil_table['year_be'].unique(), reverse=True)
                        chosen_year = st.selectbox(
                            "📅 เลือกปี พ.ศ.:",
                            options=available_years,
                            index=0 if 2569 in available_years else 0,
                            key="oil_table_year_selector"
                        )
                    
                    df_display = raw_oil_table[raw_oil_table['year_be'] == chosen_year].copy()
                    
                    # ตัดคอลัมน์ระบบออกเพื่อแสดงผล
                    show_cols = [c for c in df_display.columns if c not in ['date_iso', 'year_be']]
                    df_display = df_display[show_cols]
                    
                    with filter_col2:
                        st.markdown(f"📊 **พบการปรับราคาทั้งหมด:** `{len(df_display)}` ครั้ง ในปี พ.ศ. `{chosen_year}`")
                    
                    st.dataframe(
                        df_display,
                        hide_index=True,
                        column_config={
                            "วันที่": st.column_config.TextColumn("📅 วันที่ปรับราคา", width="medium"),
                            "แก๊สโซฮอล์ 95": st.column_config.TextColumn("⛽ แก๊สโซฮอล์ 95"),
                            "แก๊สโซฮอล์ 91": st.column_config.TextColumn("⛽ แก๊สโซฮอล์ 91"),
                            "แก๊สโซฮอล์ E20": st.column_config.TextColumn("🌱 E20"),
                            "แก๊สโซฮอล์ E85": st.column_config.TextColumn("🌱 E85"),
                            "ดีเซล": st.column_config.TextColumn("🚛 ดีเซล"),
                            "ดีเซล B20": st.column_config.TextColumn("🚛 B20"),
                            "ไฮ พรีเมียม ดีเซล พลัส": st.column_config.TextColumn("✨ ดีเซล พรีเมียม"),
                            "เบนซิน 95": st.column_config.TextColumn("🏎️ เบนซิน 95"),
                            "NGV": st.column_config.TextColumn("⚡ NGV")
                        }
                    )
                else:
                    st.warning("⚠️ ไม่สามารถโหลดตารางข้อมูลจากเว็บต้นทางได้ในขณะนี้")

    st.markdown("---")
    st.markdown("### 📊 Macro Drivers (ดอลลาร์, พันธบัตร, น้ำมันโลก & ดัชนีหลัก)")
    macro_data = fetch_macro_indicators()
    m_cols = st.columns(3)
    idx_m = 0
    for m_name, m_val in macro_data.items():
        if m_val is not None:
            curr_p, diff_p, pct_p = m_val
            with m_cols[idx_m % 3]:
                unit_prefix = "$" if "Oil" in m_name else ""
                unit_suffix = "%" if "Yield" in m_name else ""
                st.metric(label=m_name, value=f"{unit_prefix}{curr_p:,.2f}{unit_suffix}", delta=f"{diff_p:+,.2f} ({pct_p:+.2f}%)")
            idx_m += 1

    st.markdown("---")
    st.markdown("### 🚀 Mega Tech & AI Market Leaders (หุ้นเทคโนโลยี & AI สดตรง)")
    tech_data = fetch_tech_ai_stocks()
    t_cols = st.columns(3)
    idx_t = 0
    for t_name, t_val in tech_data.items():
        if t_val is not None:
            curr_p, diff_p, pct_p = t_val
            with t_cols[idx_t % 3]:
                st.metric(label=t_name, value=f"${curr_p:,.2f}", delta=f"{diff_p:+,.2f} ({pct_p:+.2f}%)")
            idx_t += 1

# --- 2. PREMIER LEAGUE TABLES ---
elif menu_selection == "🏆 2. Premier League Tables":
    st.markdown("#### 🏆 Premier League Standings")
    st.caption("ตารางคะแนนสดครบ 20 สโมสร (Real-Time Live Feed)")
    
    t2_c1, t2_c2 = st.columns([3.5, 8.5])
    with t2_c1:
        if st.button("🔄 รีเฟรชตารางคะแนนสด", key="btn_sky_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    df_sky = fetch_skysports_standings()
    if not df_sky.empty:
        # ฟังก์ชันสร้างตาราง HTML แบบกระชับพอดีหน้าจอมือถือและเดสก์ท็อป ไม่ต้องเลื่อนซ้ายขวา
        rows_html = []
        for _, row in df_sky.iterrows():
            pos = int(row['Pos'])
            if pos <= 4:
                pos_badge = f"<span style='background:#2563EB;color:#FFF;border-radius:4px;font-weight:700;padding:2px 5px;font-size:0.75rem;'>{pos}</span>"
            elif pos == 5:
                pos_badge = f"<span style='background:#EA580C;color:#FFF;border-radius:4px;font-weight:700;padding:2px 5px;font-size:0.75rem;'>{pos}</span>"
            elif pos >= 18:
                pos_badge = f"<span style='background:#DC2626;color:#FFF;border-radius:4px;font-weight:700;padding:2px 5px;font-size:0.75rem;'>{pos}</span>"
            else:
                pos_badge = f"<span style='font-weight:600;color:#64748B;'>{pos}</span>"

            badge_url = row.get('Badge', '')
            badge_tag = f"<img src='{badge_url}' style='width:18px;height:18px;vertical-align:middle;margin-right:5px;object-fit:contain;' onerror=\"this.style.display='none'\">" if badge_url else ""
            
            club_name = row['Club']
            gd_val = str(row['GD'])
            gd_color = "#16A34A" if gd_val.startswith('+') and gd_val != '+0' else ("#DC2626" if gd_val.startswith('-') else "#64748B")

            row_html = (
                f"<tr>"
                f"<td style='padding:6px 2px;'>{pos_badge}</td>"
                f"<td style='padding:6px 6px;text-align:left;font-weight:600;white-space:nowrap;'>{badge_tag}{club_name}</td>"
                f"<td style='padding:6px 2px;'>{row['Pl']}</td>"
                f"<td style='padding:6px 2px;'>{row['W']}</td>"
                f"<td style='padding:6px 2px;'>{row['D']}</td>"
                f"<td style='padding:6px 2px;'>{row['L']}</td>"
                f"<td style='padding:6px 2px;'>{row.get('F', '-')}</td>"
                f"<td style='padding:6px 2px;'>{row.get('A', '-')}</td>"
                f"<td style='padding:6px 2px;font-weight:700;color:{gd_color};'>{gd_val}</td>"
                f"<td class='pl-pts-col' style='padding:6px 4px;'>{row['Pts']}</td>"
                f"</tr>"
            )
            rows_html.append(row_html)

        table_body = "".join(rows_html)
        final_html = (
            "<div class='pl-table-container'>"
            "<table class='pl-table'>"
            "<thead><tr>"
            "<th style='width:30px;'>#</th>"
            "<th style='text-align:left;padding-left:8px;'>สโมสร (Club)</th>"
            "<th style='width:32px;'>แข่ง</th>"
            "<th style='width:32px;'>ชนะ</th>"
            "<th style='width:32px;'>เสมอ</th>"
            "<th style='width:32px;'>แพ้</th>"
            "<th style='width:34px;'>ได้</th>"
            "<th style='width:34px;'>เสีย</th>"
            "<th style='width:36px;'>+/-</th>"
            "<th class='pl-pts-col' style='width:42px;'>แต้ม</th>"
            "</tr></thead>"
            f"<tbody>{table_body}</tbody>"
            "</table></div>"
            "<div style='display:flex;flex-wrap:wrap;gap:12px;margin-top:6px;font-size:0.74rem;color:#64748B;padding-left:2px;'>"
            "<span><span style='display:inline-block;width:10px;height:10px;background:#2563EB;border-radius:2px;margin-right:4px;'></span>1-4: UCL</span>"
            "<span><span style='display:inline-block;width:10px;height:10px;background:#EA580C;border-radius:2px;margin-right:4px;'></span>5: UEL</span>"
            "<span><span style='display:inline-block;width:10px;height:10px;background:#DC2626;border-radius:2px;margin-right:4px;'></span>18-20: ตกชั้น</span>"
            "</div>"
        )
        st.html(final_html)
    else:
        st.error("⚠️ ไม่สามารถเชื่อมต่อกับฐานข้อมูลตารางคะแนนได้ในขณะนี้")

# --- 3. PREMIER LEAGUE FIXTURES & SCORES ---
elif menu_selection == "📅 3. Premier League Fixtures":
    st.markdown("#### 📅 Premier League Fixtures & Live Scores")
    st.caption("ผลการแข่งขันและตารางถ่ายทอดสดพรีเมียร์ลีก (GoalDaddy Live Feed ตรงตามเวลาไทย BKK)")

    t3_c1, t3_c2 = st.columns([3.5, 8.5])
    with t3_c1:
        if st.button("🔄 รีเฟรชผลและตารางสด", key="btn_fixtures_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    fixtures_raw = fetch_skysports_fixtures()
    df_all_fixtures = pd.DataFrame(fixtures_raw)

    if not df_all_fixtures.empty:
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 3, 1.4])
        with ctrl_col1:
            all_mws = list(dict.fromkeys(df_all_fixtures['MW'].tolist()))
            mw_options = ["🌟 แสดงทุกสัปดาห์ (All Matchweeks)"] + all_mws
            selected_mw = st.selectbox("📅 เลือกสัปดาห์การแข่งขัน:", mw_options, key="pl_mw_selector")
        with ctrl_col2:
            search_team = st.text_input("🔍 ค้นหาทีมโปรด:", placeholder="พิมพ์ เช่น Arsenal, Man Utd, Liverpool...", key="pl_team_search")
        with ctrl_col3:
            st.write("")
            st.write("")
            st.link_button("🌐 GoalDaddy", "https://www.goaldaddythai.info/leagueDetail/31/%E0%B8%AD%E0%B8%B1%E0%B8%87%E0%B8%81%E0%B8%A4%E0%B8%A9-%E0%B8%9E%E0%B8%A3%E0%B8%B5%E0%B9%80%E0%B8%A1%E0%B8%B5%E0%B8%A2%E0%B8%A3%E0%B9%8C-%E0%B8%A5%E0%B8%B5%E0%B8%81", use_container_width=True)

        st.markdown("---")
        df_filtered = df_all_fixtures.copy()
        if selected_mw != "🌟 แสดงทุกสัปดาห์ (All Matchweeks)":
            df_filtered = df_filtered[df_filtered['MW'] == selected_mw]
        if search_team:
            df_filtered = df_filtered[
                df_filtered['Home'].str.contains(search_team, case=False, na=False) | 
                df_filtered['Away'].str.contains(search_team, case=False, na=False)
            ]

        if not df_filtered.empty:
            rows_fix_html = []
            for _, row in df_filtered.iterrows():
                h_badge = f"<img src='{row['HomeBadge']}' style='width:22px;height:22px;vertical-align:middle;margin-left:6px;object-fit:contain;' onerror=\"this.style.display='none'\">" if row.get('HomeBadge') else ""
                a_badge = f"<img src='{row['AwayBadge']}' style='width:22px;height:22px;vertical-align:middle;margin-right:6px;object-fit:contain;' onerror=\"this.style.display='none'\">" if row.get('AwayBadge') else ""
                
                status_val = str(row.get('Status', ''))
                
                if "⚽" in status_val or "(FT)" in status_val:
                    status_badge = f"<span class='pl-badge-finished'>{status_val}</span>"
                elif "⏰" in status_val:
                    status_badge = f"<span class='pl-badge-upcoming'>{status_val}</span>"
                else:
                    status_badge = f"<span class='pl-badge-upcoming'>{status_val}</span>"

                row_html = (
                    f"<tr>"
                    f"<td style='padding:12px 10px;text-align:left;white-space:nowrap;width:22%;vertical-align:middle;'>"
                    f"<div class='pl-fixture-mw'>{row['MW']}</div>"
                    f"<div class='pl-fixture-date'>{row['Date']}</div>"
                    f"</td>"
                    f"<td style='padding:12px 14px;text-align:right;font-weight:600;font-size:0.92rem;white-space:nowrap;vertical-align:middle;width:30%;' class='pl-fixture-team'>"
                    f"<span>{row['Home']}</span>{h_badge}"
                    f"</td>"
                    f"<td style='padding:12px 6px;text-align:center;width:170px;vertical-align:middle;'>"
                    f"{status_badge}"
                    f"</td>"
                    f"<td style='padding:12px 14px;text-align:left;font-weight:600;font-size:0.92rem;white-space:nowrap;vertical-align:middle;width:30%;' class='pl-fixture-team'>"
                    f"{a_badge}<span>{row['Away']}</span>"
                    f"</td>"
                    f"</tr>"
                )
                rows_fix_html.append(row_html)

            fixtures_body = "".join(rows_fix_html)
            final_fix_html = (
                "<div class='pl-table-container' style='overflow-x:auto;'>"
                "<table class='pl-table' style='width:100%;border-collapse:collapse;'>"
                "<thead><tr style='background:#F8FAFC;border-bottom:2px solid #E2E8F0;'>"
                "<th style='width:22%;text-align:left;padding:10px 10px;color:#334155;font-weight:700;font-size:0.86rem;'>สัปดาห์ / วันแข่ง</th>"
                "<th style='width:30%;text-align:right;padding:10px 14px;color:#334155;font-weight:700;font-size:0.86rem;'>เจ้าบ้าน (Home)</th>"
                "<th style='width:170px;text-align:center;padding:10px 6px;color:#334155;font-weight:700;font-size:0.86rem;'>ผลบอล / เวลา Kickoff (ไทย)</th>"
                "<th style='width:30%;text-align:left;padding:10px 14px;color:#334155;font-weight:700;font-size:0.86rem;'>ทีมเยือน (Away)</th>"
                "</tr></thead>"
                f"<tbody>{fixtures_body}</tbody>"
                "</table></div>"
            )
            st.html(final_fix_html)
        else:
            st.warning("⚠️ ไม่พบคู่การแข่งขันที่ตรงกับเงื่อนไขการค้นหา")
    else:
        st.warning("⚠️ กำลังโหลดข้อมูลโปรแกรมการแข่งขันจาก GoalDaddy หรือไม่สามารถเชื่อมต่อได้ในขณะนี้")


# --- 4. CURATED RSS FEEDS ---
elif menu_selection == "📡 4. Curated RSS Feeds":
    render_rss_page()

# --- 5. MEDIA & VIDEO HUB ---
elif menu_selection == "📺 5. Media & Video Hub":
    render_tech_hub_page()

# --- 6. YOUTUBE SEARCH HUB ---
elif menu_selection == "🔍 6. YouTube Search Hub":
    render_youtube_search_page()