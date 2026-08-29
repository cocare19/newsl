import os
import streamlit as st

def load_api_keys():
    """โหลดรายการ API Keys จาก Hugging Face Secrets (os.environ) หรือ secrets.toml (st.secrets)"""
    keys = []
    
    # 1. เช็คจาก Environment Variables (Hugging Face Spaces Secrets)
    env_keys = os.getenv("GEMINI_API_KEYS")
    if env_keys:
        for k in env_keys.split(","):
            k_clean = k.strip()
            if k_clean and k_clean not in keys:
                keys.append(k_clean)
    env_single = os.getenv("GEMINI_API_KEY")
    if env_single and env_single not in keys:
        keys.insert(0, env_single)

    # 2. เช็คจาก Streamlit secrets.toml
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEYS" in st.secrets:
            raw = st.secrets["GEMINI_API_KEYS"]
            if isinstance(raw, list):
                for item in raw:
                    if item not in keys:
                        keys.append(item)
            elif isinstance(raw, str) and raw not in keys:
                keys.append(raw)
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            k = st.secrets["GEMINI_API_KEY"]
            if k not in keys:
                keys.insert(0, k)
    except Exception:
        pass

    return keys

# ตราสโมสรพรีเมียร์ลีกมาตรฐาน (Vector Icons)
CLUB_BADGES = {
    "arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "aston villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",
    "bournemouth": "https://a.espncdn.com/i/teamlogos/soccer/500/349.png",
    "brentford": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png",
    "brighton": "https://a.espncdn.com/i/teamlogos/soccer/500/331.png",
    "chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
    "coventry": "https://a.espncdn.com/i/teamlogos/soccer/500/392.png",
    "crystal palace": "https://a.espncdn.com/i/teamlogos/soccer/500/384.png",
    "palace": "https://a.espncdn.com/i/teamlogos/soccer/500/384.png",
    "everton": "https://a.espncdn.com/i/teamlogos/soccer/500/368.png",
    "fulham": "https://a.espncdn.com/i/teamlogos/soccer/500/370.png",
    "hull": "https://a.espncdn.com/i/teamlogos/soccer/500/306.png",
    "ipswich": "https://a.espncdn.com/i/teamlogos/soccer/500/373.png",
    "leeds": "https://a.espncdn.com/i/teamlogos/soccer/500/357.png",
    "leicester": "https://a.espncdn.com/i/teamlogos/soccer/500/375.png",
    "liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "manchester city": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "man city": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "manchester united": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "man utd": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "newcastle": "https://a.espncdn.com/i/teamlogos/soccer/500/361.png",
    "nottingham": "https://a.espncdn.com/i/teamlogos/soccer/500/393.png",
    "southampton": "https://a.espncdn.com/i/teamlogos/soccer/500/376.png",
    "sunderland": "https://a.espncdn.com/i/teamlogos/soccer/500/366.png",
    "tottenham": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "spurs": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "west ham": "https://a.espncdn.com/i/teamlogos/soccer/500/371.png",
    "wolves": "https://a.espncdn.com/i/teamlogos/soccer/500/380.png",
    "wolverhampton": "https://a.espncdn.com/i/teamlogos/soccer/500/380.png"
}

def get_club_logo(name):
    """จับคู่ชื่อสโมสรกับลิงก์รูปภาพตราสโมสร"""
    clean_name = str(name).lower()
    for k, v in CLUB_BADGES.items():
        if k in clean_name:
            return v
    return "https://a.espncdn.com/i/teamlogos/default-team-logo-500.png"

# ดีไซน์ตกแต่งหน้าจอ CSS Styling (อัปเดตสีตัวหนังสือเมนูที่ถูกเลือกให้เป็นสีขาวชัดเจน)
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Prompt', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp { background-color: #F8FAFC; color: #0F172A; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; padding-top: 1.2rem; }
    
    /* --- Modern Typography for All Headings (Keep Colorful Emojis & Modern Text Colors) --- */
    h1, [data-testid="stMarkdownContainer"] h1 {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        color: #1E3A8A !important;
        margin-top: 0.6rem !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.3 !important;
    }
    h2, [data-testid="stMarkdownContainer"] h2 {
        font-size: 1.26rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.015em !important;
        color: #1D4ED8 !important;
        margin-top: 0.55rem !important;
        margin-bottom: 0.45rem !important;
        line-height: 1.35 !important;
    }
    h3, [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        color: #2563EB !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.4rem !important;
        line-height: 1.35 !important;
    }
    h4, [data-testid="stMarkdownContainer"] h4 {
        font-size: 1.02rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        color: #0284C7 !important;
        margin-top: 0.45rem !important;
        margin-bottom: 0.35rem !important;
        line-height: 1.4 !important;
    }
    h5, [data-testid="stMarkdownContainer"] h5 {
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        color: #0369A1 !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0.3rem !important;
    }
    h6, [data-testid="stMarkdownContainer"] h6 {
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
    }

    /* --- Sidebar Navigation & Settings (Full Width, Equal Alignment & Modern Glow) --- */
    [data-testid="stSidebar"] div[data-testid="stRadio"] { width: 100% !important; }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > label { display: none; }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div { display: flex; flex-direction: column; gap: 5px; width: 100% !important; }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label {
        width: 100% !important;
        box-sizing: border-box !important;
        background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 7px;
        padding: 8px 12px; font-size: 0.83rem !important; font-weight: 600; color: #334155;
        cursor: pointer; transition: all 0.15s ease-in-out;
        display: flex !important; align-items: center !important;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:hover {
        background-color: #F1F5F9; color: #0F172A; border-color: #CBD5E1; transform: translateX(2px);
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label[data-checked="true"],
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        border-color: #1D4ED8 !important; box-shadow: 0 3px 10px rgba(37, 99, 235, 0.25);
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label[data-checked="true"] p,
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) p,
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label[data-checked="true"] span,
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label:has(input:checked) span {
        color: #FFFFFF !important; font-weight: 700 !important;
    }

    /* --- Main Page Radio Options (Compact & Sleek) --- */
    .main div[data-testid="stRadio"] > div {
        gap: 6px;
    }
    .main div[data-testid="stRadio"] > div > label {
        background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px;
        padding: 5px 10px !important; font-size: 0.81rem !important; font-weight: 600; color: #334155;
        cursor: pointer; transition: all 0.15s ease-in-out;
    }
    .main div[data-testid="stRadio"] > div > label:hover {
        background-color: #F1F5F9; border-color: #CBD5E1;
    }
    .main div[data-testid="stRadio"] > div > label[data-checked="true"],
    .main div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        border-color: #1D4ED8 !important; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.20);
    }
    .main div[data-testid="stRadio"] > div > label[data-checked="true"] p,
    .main div[data-testid="stRadio"] > div > label:has(input:checked) p,
    .main div[data-testid="stRadio"] > div > label[data-checked="true"] span,
    .main div[data-testid="stRadio"] > div > label:has(input:checked) span {
        color: #FFFFFF !important; font-weight: 700 !important;
    }

    /* --- Form Widgets & Dropdowns (Compact, Readable & Modern) --- */
    [data-testid="stWidgetLabel"] p, label p {
        font-size: 0.79rem !important; font-weight: 600 !important; color: #475569 !important;
        margin-bottom: 2px !important;
    }
    div[data-baseweb="select"] > div {
        font-size: 0.83rem !important; border-radius: 6px !important;
        min-height: 36px !important; padding-top: 1px !important; padding-bottom: 1px !important;
        background-color: #FFFFFF !important; border-color: #CBD5E1 !important;
    }
    div[data-baseweb="popover"] ul li {
        font-size: 0.83rem !important; padding: 6px 10px !important;
    }
    div[data-baseweb="input"] input {
        font-size: 0.83rem !important; min-height: 36px !important; border-radius: 6px !important;
    }

    /* --- Tabs (Modern & Compact) --- */
    button[data-baseweb="tab"] {
        font-size: 0.83rem !important; font-weight: 600 !important;
        padding: 5px 12px !important;
    }

    /* --- Alert Messages (Compact & Neat) --- */
    [data-testid="stAlert"] {
        padding: 8px 14px !important; border-radius: 7px !important;
        font-size: 0.83rem !important; margin-top: 8px !important; margin-bottom: 8px !important;
    }
    [data-testid="stAlert"] p {
        font-size: 0.83rem !important; margin: 0 !important;
    }

    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03); transition: all 0.15s ease-in-out;
    }
    [data-testid="stMetric"]:hover { border-color: #CBD5E1; box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06); transform: translateY(-1px); }
    [data-testid="stMetricLabel"] p { font-size: 0.77rem !important; font-weight: 600 !important; color: #64748B !important; margin-bottom: 2px !important; }
    [data-testid="stMetricValue"] div { font-size: 1.35rem !important; font-weight: 700 !important; color: #0F172A !important; line-height: 1.2 !important; }
    [data-testid="stMetricDelta"] div { font-size: 0.72rem !important; font-weight: 500 !important; margin-top: 2px !important; }

    .content-box {
        background: #FFFFFF; border-radius: 10px; padding: 18px 20px; margin-bottom: 14px;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        color: #1E293B; line-height: 1.75; font-size: 0.90rem;
    }
    .news-badge {
        display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.72rem;
        font-weight: 600; background-color: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; margin-bottom: 8px;
    }
    .news-title { color: #0F172A; font-size: 1.15rem; font-weight: 700; line-height: 1.4; margin-bottom: 10px; }
    .model-tag { font-size: 0.68rem; color: #64748B; background-color: #F1F5F9; padding: 2px 6px; border-radius: 4px; margin-top: 10px; display: inline-block; font-weight: 500; }
    .source-container { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; margin-top: 10px; font-size: 0.84rem; }

    .stButton>button {
        width: 100%; background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); color: #FFFFFF !important;
        border: none; border-radius: 6px; height: 35px !important; min-height: 35px !important; font-weight: 600; font-size: 0.83rem !important;
        padding: 4px 8px !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.18); transition: all 0.15s ease;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%); box-shadow: 0 4px 10px rgba(37, 99, 235, 0.28); transform: translateY(-1px); }

    /* --- Premier League Custom Responsive Table --- */
    .pl-table-container {
        width: 100%; overflow-x: auto; border-radius: 10px; border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); margin-bottom: 12px;
    }
    .pl-table {
        width: 100%; border-collapse: collapse; text-align: center; font-size: 0.84rem;
        background: #FFFFFF; font-family: 'Plus Jakarta Sans', 'Prompt', sans-serif;
    }
    .pl-table th {
        background: #F8FAFC; border-bottom: 2px solid #E2E8F0; color: #475569; font-weight: 700;
        padding: 8px 4px;
    }
    .pl-table td {
        padding: 7px 4px; border-bottom: 1px solid #F1F5F9;
    }
    .pl-table tr:hover {
        background-color: #F8FAFC !important;
    }
    .pl-pts-col {
        font-weight: 800 !important; color: #1D4ED8 !important; background: #EFF6FF !important;
    }
    .pl-fixture-mw {
        font-weight: 700;
        color: #3B82F6;
        font-size: 0.88rem;
    }
    .pl-fixture-date {
        font-size: 0.84rem;
        color: #475569;
        font-weight: 500;
        margin-top: 3px;
    }
    .pl-fixture-team {
        color: #1E293B;
        font-weight: 600;
    }
    .pl-badge-live {
        background: #DC2626;
        color: #FFFFFF;
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.84rem;
        display: inline-block;
        white-space: nowrap;
        box-shadow: 0 0 8px rgba(220, 38, 38, 0.45);
        animation: plLivePulse 1.8s infinite ease-in-out;
    }
    @keyframes plLivePulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.85; transform: scale(1.02); }
        100% { opacity: 1; transform: scale(1); }
    }
    .pl-badge-finished {
        background: #16A34A;
        color: #FFFFFF;
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.84rem;
        display: inline-block;
        white-space: nowrap;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }
    .pl-badge-upcoming {
        background: #F8FAFC;
        color: #1E293B;
        border: 1px solid #CBD5E1;
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
        white-space: nowrap;
    }

    /* --- Dark Mode Auto Support (Mobile & Desktop) --- */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #0B0F19 !important; color: #F1F5F9 !important; }
        [data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #1F2937 !important; }
        .content-box { background: #111827 !important; color: #F1F5F9 !important; border-color: #1F2937 !important; }
        [data-testid="stMetric"] { background: #111827 !important; border-color: #1F2937 !important; }
        [data-testid="stMetricLabel"] p { color: #94A3B8 !important; }
        [data-testid="stMetricValue"] div { color: #F8FAFC !important; }
        .source-container { background-color: #0B0F19 !important; border-color: #1F2937 !important; }
        [data-testid="stSidebar"] div[data-testid="stRadio"] > div > label { background-color: #0B0F19 !important; border-color: #1F2937 !important; color: #E2E8F0 !important; }
        .main div[data-testid="stRadio"] > div > label { background-color: #111827 !important; border-color: #1F2937 !important; color: #E2E8F0 !important; }
        div[data-baseweb="select"] > div { background-color: #111827 !important; border-color: #374151 !important; color: #F1F5F9 !important; }
        div[data-baseweb="input"] input { background-color: #111827 !important; border-color: #374151 !important; color: #F1F5F9 !important; }
        h1, [data-testid="stMarkdownContainer"] h1 { color: #60A5FA !important; }
        h2, [data-testid="stMarkdownContainer"] h2 { color: #38BDF8 !important; }
        h3, [data-testid="stMarkdownContainer"] h3 { color: #60A5FA !important; }
        h4, [data-testid="stMarkdownContainer"] h4 { color: #93C5FD !important; }
        h5, [data-testid="stMarkdownContainer"] h5 { color: #BAE6FD !important; }
        .pl-table-container { border-color: #1F2937 !important; background: #111827 !important; }
        .pl-table { background: #111827 !important; color: #F1F5F9 !important; }
        .pl-table th { background: #0B0F19 !important; border-bottom: 2px solid #1F2937 !important; color: #94A3B8 !important; }
        .pl-table td { border-bottom: 1px solid #1F2937 !important; color: #E2E8F0 !important; }
        .pl-table tr:hover { background-color: #1F2937 !important; }
        .pl-pts-col { color: #60A5FA !important; background: rgba(37, 99, 235, 0.18) !important; }
        .pl-status-badge { background: rgba(37, 99, 235, 0.20) !important; color: #60A5FA !important; border-color: rgba(37, 99, 235, 0.40) !important; }
        .pl-fixture-mw { color: #60A5FA !important; }
        .pl-fixture-date { color: #94A3B8 !important; }
        .pl-fixture-team { color: #F1F5F9 !important; }
        .pl-badge-live { background: #EF4444 !important; color: #FFFFFF !important; }
        .pl-badge-upcoming { background: #1E293B !important; color: #F1F5F9 !important; border-color: #374151 !important; }
    }
</style>
"""