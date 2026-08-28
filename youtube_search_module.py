import streamlit as st
import requests
import json
import re
import urllib.parse
from datetime import datetime

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7'
}

SORT_OPTIONS = {
    "ความเกี่ยวข้อง (Relevance)": "relevance",
    "อัปโหลดล่าสุด (Upload Date)": "upload_date",
    "ยอดวิวสูงสุด (View Count)": "view_count",
    "คะแนนความนิยม (Rating)": "rating"
}

SP_PARAMS = {
    'relevance': '',
    'upload_date': '&sp=CAI%253D',
    'view_count': '&sp=CAM%253D',
    'rating': '&sp=CAE%253D',
}

QUICK_TOPICS = [
    ("⚡ ข่าวไอทีล่าสุด", "ข่าวไอที เทคโนโลยี ล่าสุด"),
    ("⚽ ไฮไลท์ฟุตบอล", "ไฮไลท์ พรีเมียร์ลีก ล่าสุด"),
    ("🤖 AI & Python", "สอน AI ChatGPT Python ภาษาไทย"),
    ("🍿 สปอยล์หนัง", "สปอยล์หนัง เต็มเรื่อง"),
    ("🎶 รวมเพลงเพราะ", "รวมเพลงเพราะ ฟังเพลงสบายๆ"),
    ("🙏 หลวงตาสุริยา", "หลวงตาสุริยา มหาปัญโญ วัดป่าโสมพนัส"),
    ("📈 วิเคราะห์ตลาด & หุ้น", "วิเคราะห์ตลาด หุ้น การเงิน ล่าสุด")
]


def search_youtube_videos(query: str, sort_by: str = "relevance", limit: int = 20):
    """
    ค้นหาวิดีโอบน YouTube โดยดึงข้อมูล: Video ID, ชื่อคลิป, ชื่อช่อง, รูปหน้าปก (Thumbnail),
    ความยาว (Duration), ยอดวิว (Views), วันเวลาที่ลง (Published Time) และคำอธิบายย่อ
    """
    if not query or not query.strip():
        return []

    sp = SP_PARAMS.get(sort_by, '')
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.youtube.com/results?search_query={encoded_query}{sp}"

    results = []
    seen_ids = set()

    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=12)
        idx = r.text.find('ytInitialData')
        if idx == -1:
            return []

        sub = r.text[idx:]
        m = re.search(r'ytInitialData\s*=\s*(\{.*?\});\s*</script>', sub, re.DOTALL)
        if not m:
            return []

        data = json.loads(m.group(1))

        def extract_node(node):
            if isinstance(node, dict):
                if 'videoRenderer' in node:
                    vr = node['videoRenderer']
                    vid = vr.get('videoId')
                    if vid and vid not in seen_ids:
                        seen_ids.add(vid)
                        
                        # Title
                        title = ""
                        if 'title' in vr:
                            runs = vr['title'].get('runs', [])
                            if runs:
                                title = "".join(r.get('text', '') for r in runs)
                            else:
                                title = vr['title'].get('simpleText', '')
                        
                        # Channel name
                        channel = ""
                        if 'ownerText' in vr and 'runs' in vr['ownerText']:
                            channel = "".join(r.get('text', '') for r in vr['ownerText']['runs'])
                        elif 'shortBylineText' in vr and 'runs' in vr['shortBylineText']:
                            channel = "".join(r.get('text', '') for r in vr['shortBylineText']['runs'])

                        # Views
                        views = ""
                        if 'viewCountText' in vr:
                            views = vr['viewCountText'].get('simpleText', '')
                            if not views and 'runs' in vr['viewCountText']:
                                views = "".join(r.get('text', '') for r in vr['viewCountText']['runs'])

                        # Published Time
                        pub_time = ""
                        if 'publishedTimeText' in vr:
                            pub_time = vr['publishedTimeText'].get('simpleText', '')
                            if not pub_time and 'runs' in vr['publishedTimeText']:
                                pub_time = "".join(r.get('text', '') for r in vr['publishedTimeText']['runs'])

                        # Duration
                        length = ""
                        if 'lengthText' in vr:
                            length = vr['lengthText'].get('simpleText', '')
                            if not length and 'runs' in vr['lengthText']:
                                length = "".join(r.get('text', '') for r in vr['lengthText']['runs'])

                        # Thumbnail URL (High Quality)
                        thumbs = vr.get('thumbnail', {}).get('thumbnails', [])
                        thumb_url = ""
                        if thumbs:
                            thumb_url = thumbs[-1].get('url', '')
                            # Clean up webp or query parameters if needed
                            if thumb_url.startswith("//"):
                                thumb_url = "https:" + thumb_url
                        if not thumb_url:
                            thumb_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

                        # Snippet description
                        desc = ""
                        if 'detailedMetadataSnippets' in vr:
                            for s in vr['detailedMetadataSnippets']:
                                for run in s.get('snippetText', {}).get('runs', []):
                                    desc += run.get('text', '')
                        elif 'descriptionSnippet' in vr:
                            for run in vr['descriptionSnippet'].get('runs', []):
                                desc += run.get('text', '')

                        if title:
                            results.append({
                                'id': vid,
                                'title': title.strip(),
                                'channel': channel.strip(),
                                'views': views.strip() if views else "ยอดวิว N/A",
                                'published': pub_time.strip() if pub_time else "ไม่ระบุเวลา",
                                'duration': length.strip() if length else "--:--",
                                'thumbnail': thumb_url,
                                'description': desc.strip(),
                                'link': f"https://www.youtube.com/watch?v={vid}"
                            })

                for v in node.values():
                    extract_node(v)
            elif isinstance(node, list):
                for item in node:
                    extract_node(item)

        extract_node(data)
    except Exception as e:
        print(f"Error searching YouTube: {e}")

    return results[:limit]


def render_youtube_search_page():
    """หน้าจอค้นหาวิดีโอ YouTube พร้อมรูปหน้าปก ข้อมูลคลิป และเครื่องเล่นวิดีโอ"""
    st.markdown("""
        <div style="background: linear-gradient(135deg, #FF0000 0%, #CC0000 50%, #990000 100%); padding: 18px 22px; border-radius: 12px; margin-bottom: 20px; color: white; box-shadow: 0 4px 14px rgba(255, 0, 0, 0.25);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 2.2rem;">🎬</div>
                <div>
                    <h3 style="margin: 0; font-size: 1.35rem; font-weight: 800; color: white;">YouTube Search & Video Explorer</h3>
                    <p style="margin: 2px 0 0 0; font-size: 0.88rem; opacity: 0.92; color: #FFF;">
                        ค้นหาคลิปวิดีโอจาก YouTube ได้โดยตรง สกัดรูปหน้าปก รายละเอียด และกดเลือกชมวิดีโอได้ทันที
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Initial session states
    if 'yt_search_query' not in st.session_state:
        st.session_state['yt_search_query'] = ""
    if 'yt_search_results' not in st.session_state:
        st.session_state['yt_search_results'] = []
    if 'yt_selected_video' not in st.session_state:
        st.session_state['yt_selected_video'] = None
    if 'yt_favorites' not in st.session_state:
        st.session_state['yt_favorites'] = []
    if 'yt_search_history' not in st.session_state:
        st.session_state['yt_search_history'] = []

    tab_search, tab_fav = st.tabs(["🔍 ค้นหาวิดีโอ (Search Videos)", "⭐ รายการโปรด & ประวัติ (Favorites & History)"])

    # --- TAB 1: SEARCH VIDEOS ---
    with tab_search:
        # หัวข้อค้นหาด่วน (Quick Topics)
        st.markdown("<p style='font-size: 0.82rem; font-weight: 700; color: #475569; margin-bottom: 6px;'>⚡ คำค้นหายอดนิยม (QUICK TOPICS):</p>", unsafe_allow_html=True)
        topic_cols = st.columns(len(QUICK_TOPICS))
        for i, (label, q_val) in enumerate(QUICK_TOPICS):
            with topic_cols[i]:
                if st.button(label, use_container_width=True, key=f"quick_top_{i}"):
                    st.session_state['yt_search_query'] = q_val
                    st.session_state['yt_trigger_search'] = True
                    st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Form ค้นหา
        with st.form("yt_search_form", clear_on_submit=False):
            col_inp, col_sort, col_cnt = st.columns([3.5, 1.5, 1.0])
            with col_inp:
                search_kw = st.text_input(
                    "🔍 คำค้นหาวิดีโอ (Search Query):",
                    value=st.session_state.get('yt_search_query', ''),
                    placeholder="พิมพ์เรื่องที่ต้องการค้นหา เช่น รีวิว iPhone 16, ไฮไลท์ฟุตบอล, สอน AI...",
                    key="yt_kw_input"
                )
            with col_sort:
                sort_choice = st.selectbox(
                    "⚙️ จัดเรียงผลลัพธ์:",
                    list(SORT_OPTIONS.keys()),
                    index=0,
                    key="yt_sort_sel"
                )
            with col_cnt:
                limit_choice = st.selectbox(
                    "📊 จำนวนคลิป:",
                    [10, 20, 30, 50],
                    index=1,
                    key="yt_limit_sel"
                )

            btn_submit = st.form_submit_button("🚀 ค้นหาวิดีโอ YouTube", use_container_width=True)

        # ดำเนินการค้นหา
        should_search = btn_submit or st.session_state.pop('yt_trigger_search', False)
        if should_search and search_kw.strip():
            st.session_state['yt_search_query'] = search_kw.strip()
            chosen_sort_key = SORT_OPTIONS[sort_choice]
            
            # บันทึกลงประวัติค้นหา
            if search_kw.strip() not in st.session_state['yt_search_history']:
                st.session_state['yt_search_history'].insert(0, search_kw.strip())
                st.session_state['yt_search_history'] = st.session_state['yt_search_history'][:20]

            with st.spinner(f"🔍 กำลังค้นหาวิดีโอบน YouTube สำหรับ '{search_kw.strip()}'..."):
                results = search_youtube_videos(search_kw.strip(), sort_by=chosen_sort_key, limit=limit_choice)
                st.session_state['yt_search_results'] = results
                if results and not st.session_state.get('yt_selected_video'):
                    st.session_state['yt_selected_video'] = results[0]

        # --- ส่วนที่ 1: โรงภาพยนตร์ / เครื่องเล่นวิดีโอ (Theater View Player) ---
        selected_vid = st.session_state.get('yt_selected_video')
        if selected_vid:
            st.markdown("---")
            st.markdown(f"""
                <div style="background: #0F172A; border-radius: 12px; padding: 16px; margin-bottom: 20px; color: white; border: 1px solid #1E293B; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
                        <div>
                            <span style="background: #EF4444; color: white; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">
                                🔴 NOW PLAYING
                            </span>
                            <h3 style="color: #F8FAFC; margin: 8px 0 4px 0; font-size: 1.25rem; font-weight: 700;">
                                {selected_vid['title']}
                            </h3>
                            <div style="font-size: 0.85rem; color: #94A3B8; display: flex; gap: 14px; flex-wrap: wrap; align-items: center; margin-top: 4px;">
                                <span>📺 <b>{selected_vid['channel']}</b></span>
                                <span>⏱️ <b>{selected_vid['duration']}</b></span>
                                <span>👁️ <b>{selected_vid['views']}</b></span>
                                <span>🕒 <b>{selected_vid['published']}</b></span>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # เครื่องเล่น Streamlit Video Player
            st.video(selected_vid['link'])

            # แถบเครื่องมือใต้เครื่องเล่น
            ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2.5, 2.5, 1.2])
            with ctrl_col1:
                st.link_button("▶️ เปิดรับชมบน YouTube โดยตรง", selected_vid['link'], use_container_width=True)
            with ctrl_col2:
                # ปุ่มบันทึกรายการโปรด
                is_fav = any(f['id'] == selected_vid['id'] for f in st.session_state['yt_favorites'])
                if is_fav:
                    if st.button("💔 ลบออกจากรายการโปรด", use_container_width=True, key="btn_remove_fav_player"):
                        st.session_state['yt_favorites'] = [f for f in st.session_state['yt_favorites'] if f['id'] != selected_vid['id']]
                        st.success("ลบออกจากรายการโปรดแล้ว")
                        st.rerun()
                else:
                    if st.button("⭐ บันทึกเป็นคลิปโปรด", use_container_width=True, key="btn_add_fav_player"):
                        st.session_state['yt_favorites'].insert(0, selected_vid)
                        st.success("บันทึกลงในรายการโปรดเรียบร้อยแล้ว!")
                        st.rerun()
            with ctrl_col3:
                if st.button("❌ ปิดเครื่องเล่น", use_container_width=True, key="btn_close_player"):
                    st.session_state['yt_selected_video'] = None
                    st.rerun()

        # --- ส่วนที่ 2: รายการผลการค้นหา (YouTube Video Feed & Cards) ---
        search_results = st.session_state.get('yt_search_results', [])
        current_query = st.session_state.get('yt_search_query', '')

        if search_results:
            st.markdown("---")
            res_header_col1, res_header_col2 = st.columns([3.5, 1.5])
            with res_header_col1:
                st.markdown(f"#### 📺 ผลการค้นหาสำหรับ: <span style='color: #EF4444;'>\"{current_query}\"</span> (พบ {len(search_results)} คลิป)", unsafe_allow_html=True)
            with res_header_col2:
                st.caption(f"ดึงข้อมูลล่าสุดเมื่อ: {datetime.now().strftime('%H:%M:%S')}")

            # Dropdown ด่วนสำหรับเลือกเล่นคลิป
            video_options = {}
            for idx, item in enumerate(search_results):
                label = f"#{idx+1} [{item['duration']}] {item['title']} - {item['channel']} ({item['views']})"
                video_options[label] = item

            quick_sel = st.selectbox(
                "🎯 เลือกคลิปจากรายการด่วนเพื่อรับชมทันที:",
                options=list(video_options.keys()),
                key="yt_quick_select_box"
            )
            
            # ปุ่มเล่นจาก Dropdown
            if st.button("▶️ รับชมคลิปที่เลือกจากรายการ", use_container_width=True, key="btn_play_dropdown"):
                st.session_state['yt_selected_video'] = video_options[quick_sel]
                st.rerun()

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            # แสดงผลเป็นการ์ดวิดีโอสไตล์ YouTube พร้อมรูปหน้าปก
            for idx, item in enumerate(search_results):
                card_col_thumb, card_col_info = st.columns([1.6, 3.4])
                
                with card_col_thumb:
                    # แสดงภาพปกวิดีโอ (Thumbnail)
                    st.markdown(f"""
                        <div style="position: relative; border-radius: 10px; overflow: hidden; background: #000; box-shadow: 0 3px 10px rgba(0,0,0,0.15); margin-bottom: 8px;">
                            <img src="{item['thumbnail']}" style="width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block;" onerror="this.src='https://i.ytimg.com/vi/{item['id']}/hqdefault.jpg'"/>
                            <span style="position: absolute; bottom: 8px; right: 8px; background: rgba(0, 0, 0, 0.85); color: #fff; font-size: 0.76rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; letter-spacing: 0.5px;">
                                {item['duration']}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                
                with card_col_info:
                    st.markdown(f"""
                        <div style="margin-bottom: 4px;">
                            <h4 style="margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 700; line-height: 1.35; color: #0F172A;">
                                <span style="color: #EF4444; font-size: 0.9rem;">#{idx+1}</span> {item['title']}
                            </h4>
                            <div style="font-size: 0.83rem; color: #475569; margin-bottom: 6px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                                <span>📺 <b>{item['channel']}</b></span>
                                <span>👁️ {item['views']}</span>
                                <span>🕒 {item['published']}</span>
                            </div>
                            <p style="font-size: 0.82rem; color: #64748B; margin: 0 0 8px 0; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                                {item['description'] if item['description'] else 'คลิกเพื่อรับชมวิดีโอต้นฉบับบน YouTube หรือเล่นผ่านเครื่องเล่นในระบบ'}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                    btn_c1, btn_c2 = st.columns([1.5, 1.5])
                    with btn_c1:
                        if st.button("▶️ เล่นคลิปนี้", key=f"btn_play_card_{item['id']}_{idx}", use_container_width=True):
                            st.session_state['yt_selected_video'] = item
                            st.rerun()
                    with btn_c2:
                        st.link_button("🔗 เปิดบน YouTube", item['link'], use_container_width=True)

                st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

        elif current_query:
            st.info(f"💡 ไม่พบผลการค้นหาสำหรับ '{current_query}' หรือ YouTube มีการจำกัดการเชื่อมต่อชั่วคราว กรุณาลองใช้คำค้นหาอื่น")
        else:
            st.markdown("""
                <div style="text-align: center; padding: 45px 20px; background: #F8FAFC; border-radius: 12px; border: 1px dashed #CBD5E1; margin-top: 15px;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">🔍🎬</div>
                    <h4 style="color: #334155; margin-bottom: 6px;">พิมพ์คำค้นหา หรือกดเลือกหัวข้อยอดนิยมด้านบน</h4>
                    <p style="color: #64748B; font-size: 0.88rem; max-width: 500px; margin: 0 auto;">
                        ระบบจะทำการสกัดวิดีโอจาก YouTube พร้อมรูปหน้าปก รายละเอียด ความยาว และยอดวิว เพื่อให้คุณสามารถเลือกรับชมได้ทันที
                    </p>
                </div>
            """, unsafe_allow_html=True)

    # --- TAB 2: FAVORITES & HISTORY ---
    with tab_fav:
        fav_col, hist_col = st.columns([2.5, 1.5])
        
        with fav_col:
            st.markdown("#### ⭐ รายการโปรดที่บันทึกไว้ (Favorites)")
            favorites = st.session_state.get('yt_favorites', [])
            if favorites:
                st.caption(f"มีรายการโปรดทั้งหมด {len(favorites)} คลิป")
                for f_idx, fav_item in enumerate(favorites):
                    f_col1, f_col2 = st.columns([1.5, 3.5])
                    with f_col1:
                        st.image(fav_item['thumbnail'], use_container_width=True)
                    with f_col2:
                        st.markdown(f"**{fav_item['title']}**")
                        st.caption(f"📺 {fav_item['channel']} • ⏱️ {fav_item['duration']} • 👁️ {fav_item['views']}")
                        
                        f_act1, f_act2 = st.columns([1.5, 1.5])
                        with f_act1:
                            if st.button("▶️ เล่นคลิปนี้", key=f"fav_play_{fav_item['id']}_{f_idx}", use_container_width=True):
                                st.session_state['yt_selected_video'] = fav_item
                                st.rerun()
                        with f_act2:
                            if st.button("🗑️ ลบ", key=f"fav_del_{fav_item['id']}_{f_idx}", use_container_width=True):
                                st.session_state['yt_favorites'] = [f for f in st.session_state['yt_favorites'] if f['id'] != fav_item['id']]
                                st.rerun()
                    st.markdown("<hr style='margin: 8px 0; border-top: 1px dashed #CBD5E1;'/>", unsafe_allow_html=True)
            else:
                st.info("ยังไม่มีวิดีโอในรายการโปรด (คุณสามารถกดปุ่ม '⭐ บันทึกเป็นคลิปโปรด' ขณะเล่นคลิปได้)")

        with hist_col:
            st.markdown("#### 🕒 ประวัติการค้นหาล่าสุด")
            history = st.session_state.get('yt_search_history', [])
            if history:
                for h_idx, h_query in enumerate(history):
                    if st.button(f"🔍 {h_query}", key=f"hist_btn_{h_idx}", use_container_width=True):
                        st.session_state['yt_search_query'] = h_query
                        st.session_state['yt_trigger_search'] = True
                        st.rerun()
                
                if st.button("🧹 ล้างประวัติการค้นหา", use_container_width=True, key="btn_clear_hist"):
                    st.session_state['yt_search_history'] = []
                    st.rerun()
            else:
                st.caption("ยังไม่มีประวัติการค้นหา")
