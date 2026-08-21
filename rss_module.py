import streamlit as st
import feedparser
from dateutil import parser as date_parser
from datetime import datetime
from bs4 import BeautifulSoup

# รายชื่อช่องสัญญาณข่าว RSS แยกตามหมวดหมู่
RSS_CATEGORIES = {
    "🤖 AI & Deep Tech": [
        ("🧠 OpenAI News", "https://openai.com/news/rss.xml"),
        ("🔬 Google DeepMind Blog", "https://deepmind.google/blog/rss.xml"),
        ("🤖 Anthropic & Claude News", "https://news.google.com/rss/search?q=Anthropic+Claude+AI&hl=en-US&gl=US&ceid=US:en"),
        ("🦙 Meta AI Blog", "https://ai.meta.com/blog/rss.xml"),
        ("🤗 Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
        ("☁️ Qwen (Alibaba Cloud) AI", "https://alibabacloud.com/blog/rss?category=AI"),
        ("🚀 Kimi (Moonshot AI) Tech", "https://moonshot-ai.github.io/blog/rss.xml"),
        ("🔍 DeepSeek Blog", "https://api.deepseek.com/blog/rss.xml"),
        ("✨ Zhipu AI (GLM) News", "https://www.zhipuai.cn/news/rss")
    ],
    "🚀 Science & Global Tech": [
        ("🚀 NASA Breaking News", "https://www.nasa.gov/rss/dyn/breaking_news.rss"),
        ("💻 TechCrunch AI & Tech", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("🌐 The Verge - Technology", "https://www.theverge.com/rss/index.xml"),
        ("⚡ Ars Technica", "https://feeds.arstechnica.com/arstechnica/index")
    ],
    "📈 Finance & Markets": [
        ("📉 Financial Times - Markets", "https://www.ft.com/markets?format=rss"),
        ("🥇 Investing.com - Gold News", "https://www.investing.com/rss/news_273.rss"),
        ("💰 Investing.com - Commodities", "https://www.investing.com/rss/news_11.rss"),
        ("📊 CNBC Top News", "https://search.cnbc.com/rs/search/combined hazard/rss/top_news.rss")
    ],
    "🌍 World News & Geopolitics": [
        ("⚔️ Al Jazeera - Breaking News", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("🌍 BBC World News", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("📰 Google News - World Top Stories", "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"),
        ("⚔️ Middle East Geopolitics", "https://news.google.com/rss/search?q=Middle+East+Conflict&hl=en-US&gl=US&ceid=US:en")
    ],
    "🇹🇭 ข่าวไทย & กระแสเด่น": [
        ("🇹🇭 ไทยรัฐ ออนไลน์ (ข่าวล่าสุด)", "https://www.thairath.co.th/rss/news"),
        ("🇹🇭 THE STANDARD - ทันโลก", "https://thestandard.co/feed/"),
        ("🇹🇭 PPTV HD 36 - ข่าวเด่น", "https://www.pptvhd36.com/rss/news.xml")
    ],
    "⚽ Sports & Football": [
        ("🔴 Liverpool FC News (This Is Anfield)", "https://thisisanfield.com/feed"),
        ("🏆 Premier League (Official News)", "https://www.premierleague.com/rss/club/9/rss.xml"),
        ("⚽ BBC Sport Football", "https://feeds.bbci.co.uk/sport/football/rss.xml")
    ]
}

def clean_html_text(raw_html):
    """สกัดข้อความสะอาดจาก HTML tags"""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text

def parse_entry_date(entry):
    """แปลงวันเวลาของข่าวสำหรับจัดเรียง"""
    date_str = getattr(entry, 'published', '') or getattr(entry, 'updated', '')
    if not date_str:
        return datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo)
    try:
        return date_parser.parse(date_str)
    except Exception:
        return datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo)

def render_rss_page():
    st.markdown("#### 📡 Curated RSS Live Feeds (ศูนย์รวมข่าวสารสดรอบโลก)")
    st.caption("ดึงข้อมูลข่าวสารสดจากสำนักข่าวชั้นนำทั้งในและต่างประเทศ อ่านสรุปสาระสำคัญได้ทันทีโดยไม่ต้องพึ่งพา API Key")

    col_cat, col_src, col_limit = st.columns([1.2, 1.8, 1])
    
    with col_cat:
        category_choice = st.selectbox("📂 หมวดหมู่ข่าว:", list(RSS_CATEGORIES.keys()), key="rss_cat_choice")
    
    with col_src:
        sources_in_cat = RSS_CATEGORIES[category_choice]
        source_titles = [s[0] for s in sources_in_cat]
        selected_source_title = st.selectbox("📻 เลือกช่องสัญญาณข่าว:", source_titles, key="rss_src_choice")
        chosen_url = next(s[1] for s in sources_in_cat if s[0] == selected_source_title)

    with col_limit:
        max_fetch = st.number_input("จำนวนข่าว:", min_value=5, max_value=100, value=25, step=5, key="rss_limit_input")

    col_btn, col_search = st.columns([1.2, 2.8])
    with col_btn:
        st.write("")
        btn_refresh = st.button("🔄 โหลดข่าวสดล่าสุด", use_container_width=True, key="btn_fetch_rss_clean")
    with col_search:
        keyword_filter = st.text_input("🔍 ค้นหาหัวข้อข่าวในฟีดนี้:", placeholder="พิมพ์คำค้นหา เช่น AI, Gold, Liverpool...", key="rss_keyword_filter")

    # บันทึกสถานะ feed ปัจจุบัน
    cache_key = f"feed_cache_{chosen_url}"
    if btn_refresh or cache_key not in st.session_state:
        with st.spinner(f"กำลังเชื่อมต่อและดึงฟีดสดจาก {selected_source_title}..."):
            try:
                parsed_feed = feedparser.parse(chosen_url)
                if parsed_feed.entries:
                    sorted_entries = sorted(parsed_feed.entries, key=parse_entry_date, reverse=True)
                    st.session_state[cache_key] = sorted_entries
                else:
                    st.session_state[cache_key] = []
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดในการโหลดฟีด: {str(e)}")
                st.session_state[cache_key] = []

    feed_entries = st.session_state.get(cache_key, [])

    if feed_entries:
        # กรองตาม keyword ถ้ามี
        if keyword_filter.strip():
            kw = keyword_filter.strip().lower()
            filtered_entries = [
                e for e in feed_entries 
                if kw in str(getattr(e, 'title', '')).lower() or kw in str(getattr(e, 'description', '')).lower()
            ]
        else:
            filtered_entries = feed_entries

        display_entries = filtered_entries[:int(max_fetch)]
        
        st.markdown(f"""
            <div style='display: flex; justify-content: space-between; align-items: center; margin: 12px 0 16px 0;'>
                <span style='font-size: 0.85rem; font-weight: 700; color: #1E3A8A;'>
                    📰 พบทั้งหมด {len(filtered_entries)} ข่าว (กำลังแสดง {len(display_entries)} ข่าวล่าสุด)
                </span>
                <span class='news-badge'>{selected_source_title}</span>
            </div>
        """, unsafe_allow_html=True)

        if not display_entries:
            st.info("ℹ️ ไม่พบข่าวที่ตรงกับคำค้นหาของคุณ")
            return

        for idx, entry in enumerate(display_entries):
            title = getattr(entry, 'title', 'ไม่มีหัวข้อข่าว')
            link = getattr(entry, 'link', '#')
            pub_date = getattr(entry, 'published', '') or getattr(entry, 'updated', '')
            
            raw_desc = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
            clean_desc = clean_html_text(raw_desc)
            if len(clean_desc) > 350:
                clean_desc = clean_desc[:350] + "..."

            st.markdown(f"""
                <div class="content-box" style="margin-bottom: 12px; padding: 14px 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 6px;">
                        <span class="news-badge">#{idx+1} • {category_choice.split(' ')[0]}</span>
                        <span style="font-size: 0.75rem; color: #64748B; font-weight: 600;">🕒 {pub_date}</span>
                    </div>
                    <div class="news-title" style="font-size: 1.05rem; margin-bottom: 8px; color: #0F172A;">
                        <a href="{link}" target="_blank" style="text-decoration: none; color: inherit; hover: color: #2563EB;">
                            {title}
                        </a>
                    </div>
                    <div style="font-size: 0.84rem; color: #475569; line-height: 1.6; margin-bottom: 12px;">
                        {clean_desc if clean_desc else "คลิกปุ่มด้านล่างเพื่อเปิดอ่านเนื้อหาฉบับเต็มจากเว็บไซต์ต้นทาง"}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            col_lk, _ = st.columns([1.5, 3.5])
            with col_lk:
                st.link_button(f"🌐 อ่านข่าวฉบับเต็ม #{idx+1}", link, use_container_width=True)
            st.write("")
    else:
        st.warning("⚠️ ไม่พบข้อมูลข่าวในช่องสัญญาณนี้ หรือช่องสัญญาณกำลังปิดปรับปรุงชั่วคราว")