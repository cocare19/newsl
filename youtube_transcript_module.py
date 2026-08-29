import streamlit as st
import re
import json
import urllib.parse
import urllib.request
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def extract_video_id(url: str) -> str:
    """สกัด YouTube Video ID จาก URL รูปแบบต่างๆ (watch, share, shorts, live)"""
    if not url:
        return None
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/shorts\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/live\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1)
    return None


def format_timestamp(seconds: float, srt_format: bool = False) -> str:
    """แปลงวินาทีเป็นรูปแบบเวลา HH:MM:SS หรือ HH:MM:SS,mmm สำหรับ SRT"""
    if seconds is None or seconds < 0:
        seconds = 0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    
    if srt_format:
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def get_video_metadata(video_id: str, url: str) -> dict:
    """ดึงข้อมูล Metadata วิดีโอ (Title, Channel, Thumbnail) อย่างรวดเร็วด้วย oEmbed API"""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            d = json.loads(resp.read().decode('utf-8'))
            return {
                "id": video_id,
                "title": d.get("title", f"YouTube Video ({video_id})"),
                "channel": d.get("author_name", "YouTube Creator"),
                "thumbnail": d.get("thumbnail_url", f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"),
                "url": url,
                "duration": 0
            }
    except Exception:
        pass
        
    return {
        "id": video_id,
        "title": f"YouTube Video ({video_id})",
        "channel": "YouTube Channel",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "url": url,
        "duration": 0
    }


def is_text_thai(text: str) -> bool:
    """ตรวจสอบว่าข้อความเป็นภาษาไทยหรือไม่"""
    if not text:
        return False
    thai_chars = sum(1 for c in text if '\u0E00' <= c <= '\u0E7F')
    return thai_chars > 5 or (thai_chars / max(1, len(text))) > 0.05


def translate_to_thai(text: str) -> str:
    """แปลข้อความเป็นภาษาไทยอย่างเป็นธรรมชาติและแม่นยำ (Zero-API-Key Mode)"""
    if not text or not text.strip():
        return ""
    try:
        url = f"https://translate.google.com/m?sl=auto&tl=th&q={urllib.parse.quote(text.strip())}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            res = soup.find('div', class_='result-container')
            if res and res.text:
                return res.text.strip()
    except Exception:
        pass
    return text


def translate_paragraphs_to_thai(paragraphs, max_workers: int = 12):
    """แปลชุดย่อหน้าทั้งหมดเป็นภาษาไทยผ่าน ThreadPool ขนานความเร็วสูง"""
    if not paragraphs:
        return []

    def _tr(p):
        p_copy = dict(p)
        p_copy['original_text'] = p.get('text', '')
        p_copy['text'] = translate_to_thai(p.get('text', ''))
        return p_copy

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(_tr, paragraphs))


@st.cache_data(ttl=600, show_spinner=False)
def fetch_youtube_data_and_transcript(url: str, preferred_languages=('th', 'en')):
    """
    ดึงข้อมูล Metadata และสคริปต์คำบรรยาย (Transcript) โดยตรง (Zero-API-Key Mode)
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise Exception("ไม่พบ YouTube Video ID ใน URL ที่ระบุ")

    # 1. ดึง Metadata วิดีโอ
    video_info = get_video_metadata(video_id, url)

    # 2. ดึงสคริปต์ Transcript ผ่าน YouTubeTranscriptApi (Fast & Reliable)
    segments = []
    selected_lang = None

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()

        t_list = api.list(video_id)

        # ลองหาภาษาไทยก่อน (Manual หรือ Auto)
        for t in t_list:
            if 'th' in t.language_code.lower():
                f = t.fetch()
                segments = [{'start': s.start, 'duration': s.duration, 'text': s.text.replace('\n', ' ').strip()} for s in f if s.text.strip()]
                selected_lang = f"{t.language} ({t.language_code})"
                break

        # ถ้าไม่มีภาษาไทย ให้หาตามภาษาที่ต้องการ (เช่น English)
        if not segments:
            for lang_code in preferred_languages:
                for t in t_list:
                    if t.language_code.lower().startswith(lang_code.lower()):
                        f = t.fetch()
                        segments = [{'start': s.start, 'duration': s.duration, 'text': s.text.replace('\n', ' ').strip()} for s in f if s.text.strip()]
                        selected_lang = f"{t.language} ({t.language_code})"
                        break
                if segments:
                    break

        # เอาภาษาแรกที่พบ
        if not segments:
            for t in t_list:
                f = t.fetch()
                segments = [{'start': s.start, 'duration': s.duration, 'text': s.text.replace('\n', ' ').strip()} for s in f if s.text.strip()]
                selected_lang = f"{t.language} ({t.language_code})"
                break

    except Exception as e:
        print("YouTubeTranscriptApi list error:", e)

    # Fallback ดึงตรงๆ ถ้า list ล้มเหลว
    if not segments:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()
            fetched = api.fetch(video_id, languages=list(preferred_languages))
            for s in fetched:
                txt = s.text.replace('\n', ' ').strip()
                if txt:
                    segments.append({
                        'start': s.start,
                        'duration': s.duration,
                        'text': txt
                    })
            if segments:
                selected_lang = "Detected Transcript"
        except Exception as e2:
            print("YouTubeTranscriptApi fetch fallback error:", e2)

    # 3. คำนวณความยาวคลิปโดยประมาณจาก segment สุดท้าย
    if segments:
        last_seg = segments[-1]
        video_info['duration'] = int(last_seg['start'] + last_seg.get('duration', 0))
        return video_info, segments, selected_lang or "คำบรรยาย YouTube"

    raise Exception("วิดีโอนี้ไม่มีคำบรรยาย (Transcript/Captions) หรือเจ้าของคลิปปิดการใช้งานคำบรรยาย")


def smart_merge_paragraphs(segments, pause_threshold: float = 2.2):
    """
    Smart Paragraph Merging:
    รวมท่อนเสียงสั้นๆ (1-2 วินาที) ให้เป็นย่อหน้าที่ต่อเนื่องและอ่านง่ายตามจังหวะหยุดพูด (Speech Pause)
    """
    if not segments:
        return []
        
    paragraphs = []
    current_para = {
        'start': segments[0]['start'],
        'duration': segments[0].get('duration', 0),
        'texts': [segments[0]['text'].strip()]
    }
    
    for i in range(len(segments) - 1):
        curr_seg = segments[i]
        next_seg = segments[i + 1]
        
        time_gap = next_seg['start'] - (curr_seg['start'] + curr_seg.get('duration', 0))
        if time_gap < 0:
            time_gap = next_seg['start'] - curr_seg['start']
            
        if time_gap > pause_threshold:
            paragraphs.append({
                'start': current_para['start'],
                'text': ' '.join(current_para['texts'])
            })
            current_para = {
                'start': next_seg['start'],
                'duration': next_seg.get('duration', 0),
                'texts': [next_seg['text'].strip()]
            }
        else:
            current_para['texts'].append(next_seg['text'].strip())
            current_para['duration'] = (next_seg['start'] + next_seg.get('duration', 0)) - current_para['start']
            
    if current_para['texts']:
        paragraphs.append({
            'start': current_para['start'],
            'text': ' '.join(current_para['texts'])
        })
        
    return paragraphs


def build_export_clean_text(paragraphs) -> str:
    """รูปแบบที่ 1: Clean continuous text (ข้อความล้วนต่อเนื่อง ไม่รวมเวลา)"""
    return "\n\n".join([p['text'] for p in paragraphs])


def build_export_timestamped_md(paragraphs, video_info: dict, is_thai: bool = True) -> str:
    """รูปแบบที่ 2: Markdown พร้อม Timestamp และหัวข้อข้อมูลคลิป"""
    duration_str = format_timestamp(video_info.get('duration', 0))
    lang_tag = "ฉบับแปลภาษาไทย (Thai Translation)" if is_thai else "ฉบับภาษาต้นฉบับ (Original Transcript)"
    header = f"""# {video_info.get('title', 'YouTube Transcript')}
- **ช่อง (Channel):** {video_info.get('channel', 'Unknown')}
- **ความยาว (Duration):** {duration_str}
- **ภาษา:** {lang_tag}
- **ลิงก์วิดีโอ (URL):** {video_info.get('url', '')}

---
### 📝 เนื้อหาสคริปต์ (Transcript with Timestamps)

"""
    body = "\n\n".join([f"**`[{format_timestamp(p['start'])}]`** {p['text']}" for p in paragraphs])
    return header + body


def build_export_srt(paragraphs) -> str:
    """รูปแบบที่ 3: มาตรฐานไฟล์คำบรรยาย (.srt)"""
    srt_lines = []
    for idx, p in enumerate(paragraphs, start=1):
        start_time = format_timestamp(p['start'], srt_format=True)
        end_time = format_timestamp(p['start'] + p.get('duration', 2.5), srt_format=True)
        text = p['text'].strip()
        srt_lines.append(f"{idx}\n{start_time} --> {end_time}\n{text}\n")
    return "\n".join(srt_lines)


def build_export_llm_prompt(paragraphs, video_info: dict) -> str:
    """รูปแบบที่ 4: โครงร่างคำสั่ง AI Prompt พร้อมบริบทและข้อกำหนดสำหรับการสรุปเนื้อหา"""
    clean_text = build_export_clean_text(paragraphs)
    prompt = f"""คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์และสรุปเนื้อหา กรุณาสรุปและวิเคราะห์เนื้อหาจากวิดีโอ YouTube ต่อไปนี้เป็นภาษาไทยอย่างละเอียด ครบถ้วน และมีโครงสร้างที่อ่านง่าย

### ข้อมูลวิดีโอ:
- **ชื่อคลิป:** {video_info.get('title', 'N/A')}
- **ช่อง:** {video_info.get('channel', 'N/A')}
- **ลิงก์:** {video_info.get('url', 'N/A')}

### ข้อกำหนดในการสรุป:
1. **Executive Summary:** สรุปใจความสำคัญและประเด็นหลักของคลิปใน 3-5 บรรทัด
2. **Key Takeaways & Details:** สรุปประเด็นเนื้อหาหลักแยกเป็นหัวข้อย่อยและลำดับขั้นตอนให้ชัดเจน
3. **Actionable Insights:** สิ่งที่สามารถนำไปปรับใช้หรือข้อคิดสำคัญที่ได้จากคลิปนี้

---
### เนื้อหาสคริปต์ (Transcript):
{clean_text}
"""
    return prompt


def wrap_utf8_bom(content: str) -> bytes:
    """ใส่ UTF-8 BOM (\uFEFF) นำหน้า เพื่อการันตีเปิดภาษาไทยได้ถูกต้องบน Windows, Excel และ Text Editors ทุกตัว"""
    return ("\ufeff" + content).encode("utf-8")


def render_youtube_transcript_page():
    """หน้าจอหลักสำหรับหัวข้อที่ 7: YouTube Transcript Pro (No API) พร้อมระบบแปลภาษาไทยอัตโนมัติ"""
    
    # CSS สไตล์เฉพาะของโมดูล Transcript
    st.markdown("""
        <style>
        .yt-extract-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #431407 100%);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 18px;
            color: #ffffff;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        }
        .yt-extract-badge {
            background: #F97316;
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
            margin-left: 8px;
        }
        .yt-para-box {
            background: #F8FAFC;
            border-left: 4px solid #2563EB;
            padding: 10px 14px;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
            font-size: 0.90rem;
            line-height: 1.5;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header Banner
    st.markdown("""
        <div class="yt-extract-banner">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                <span style="font-size: 1.6rem;">🎬</span>
                <span style="font-size: 1.45rem; font-weight: 800; color: #FFFFFF;">YouTube Transcript Pro</span>
                <span class="yt-extract-badge">🇹🇭 Auto-Translate to Thai • No API Key</span>
            </div>
            <p style="color: #CBD5E1; font-size: 0.88rem; margin: 0;">
                ดึงสคริปต์คำบรรยายจากคลิป YouTube อัตโนมัติ • แปลงเป็นภาษาไทยให้อัตโนมัติ • รวมประโยคตามความเงียบ • Export ได้ 4 รูปแบบ
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Initial Session States
    if 'transcript_url_input' not in st.session_state:
        st.session_state['transcript_url_input'] = ""
    if 'transcript_ready' not in st.session_state:
        st.session_state['transcript_ready'] = False
    if 'transcript_data' not in st.session_state:
        st.session_state['transcript_data'] = None

    # แผงตั้งค่าการถอดความ (Expander Settings)
    with st.expander("⚙️ การตั้งค่าขั้นสูง (Speech Gap & Language Priority)", expanded=False):
        c_set1, c_set2 = st.columns(2)
        with c_set1:
            pause_threshold = st.slider(
                "⏱️ Speech Pause Gap (วินาที)", 
                min_value=1.0, 
                max_value=5.0, 
                value=2.2, 
                step=0.1,
                help="ระยะเวลาความเงียบระหว่างท่อนเสียงที่ใช้ตัดขึ้นย่อหน้าใหม่ (ค่าเริ่มต้น 2.2 วินาที)"
            )
        with c_set2:
            lang_pref = st.multiselect(
                "🌐 ลำดับค้นหาภาษาคำบรรยาย",
                options=["th", "en", "ja", "zh-Hans", "zh-Hant", "ko", "de", "fr"],
                default=["th", "en"],
                help="ระบบจะค้นหาคำบรรยายตามลำดับภาษาที่ระบุ"
            )

    # Input Form สำหรับกรอก URL
    with st.form("yt_extract_form", clear_on_submit=False):
        url_col, btn_col = st.columns([4.2, 1.2])
        with url_col:
            input_url = st.text_input(
                "🔗 วางลิงก์ YouTube ที่ต้องการดึงสคริปต์ (รองรับคลิปภาษาไทย อังกฤษ และต่างประเทศ):",
                value=st.session_state.get('transcript_url_input', ''),
                placeholder="วางลิงก์ เช่น https://www.youtube.com/watch?v=... หรือ https://youtu.be/...",
                key="yt_transcript_url_box"
            )
        with btn_col:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button("🚀 ดึงสคริปต์ & แปลไทย", use_container_width=True, type="primary")

    # ดำเนินการดึงข้อมูล
    if submit_btn and input_url.strip():
        st.session_state['transcript_url_input'] = input_url.strip()
        vid_id = extract_video_id(input_url.strip())
        
        if not vid_id:
            st.error("❌ ไม่พบ Video ID ใน URL กรุณาตรวจสอบลิงก์ YouTube อีกครั้ง (รองรับทั้ง watch?v=, youtu.be, shorts/)")
        else:
            with st.spinner("⏳ กำลังเชื่อมต่อ YouTube และสกัดสคริปต์คำบรรยาย..."):
                try:
                    v_info, raw_segs, lang_name = fetch_youtube_data_and_transcript(
                        input_url.strip(),
                        preferred_languages=tuple(lang_pref)
                    )

                    # รวมย่อหน้าต้นฉบับ
                    orig_paragraphs = smart_merge_paragraphs(raw_segs, pause_threshold=pause_threshold)

                    # ตรวจสอบว่าข้อความต้นฉบับเป็นภาษาไทยอยู่แล้วหรือไม่
                    sample_check = " ".join(p['text'] for p in orig_paragraphs[:10])
                    has_thai = is_text_thai(sample_check)

                    thai_paragraphs = orig_paragraphs
                    is_translated = False
                    
                    if not has_thai:
                        with st.spinner("🇹🇭 กำลังแปลสคริปต์เป็นภาษาไทย (Auto-Translating to Thai)..."):
                            thai_paragraphs = translate_paragraphs_to_thai(orig_paragraphs)
                            is_translated = True

                    st.session_state['transcript_ready'] = True
                    st.session_state['transcript_data'] = {
                        'video_info': v_info,
                        'raw_segments': raw_segs,
                        'orig_paragraphs': orig_paragraphs,
                        'thai_paragraphs': thai_paragraphs,
                        'lang_name': lang_name,
                        'is_translated': is_translated,
                        'has_native_thai': has_thai
                    }
                    
                    trans_note = " ➡️ แปลงเป็นภาษาไทยเรียบร้อยแล้ว!" if is_translated else ""
                    st.success(f"✅ ดึงสคริปต์สำเร็จ! (ภาษาต้นฉบับ: **{lang_name}** | **{len(orig_paragraphs):,}** ย่อหน้า){trans_note}")
                except Exception as err:
                    st.session_state['transcript_ready'] = False
                    st.error(f"❌ {str(err)}")

    # แสดงผลสคริปต์ที่สกัดได้
    if st.session_state.get('transcript_ready', False) and st.session_state.get('transcript_data'):
        data_bundle = st.session_state['transcript_data']
        v_info = data_bundle['video_info']
        orig_paras = data_bundle['orig_paragraphs']
        thai_paras = data_bundle['thai_paragraphs']
        lang_name = data_bundle['lang_name']
        is_trans = data_bundle.get('is_translated', False)
        has_native_thai = data_bundle.get('has_native_thai', False)
        
        # ตรวจสอบเพิ่มเติมกรณีข้อความต้นฉบับไม่ใช่ภาษาไทย แต่ยังไม่ได้แปล
        sample_check = " ".join(p['text'] for p in orig_paras[:10])
        is_foreign = not is_text_thai(sample_check)

        st.markdown("---")
        
        # กล่องข้อมูลคลิป (Metadata Card)
        c_thumb, c_meta = st.columns([1.2, 3.0])
        with c_thumb:
            if v_info.get('thumbnail'):
                st.image(v_info['thumbnail'], use_container_width=True)
        with c_meta:
            st.markdown(f"""
                <h3 style="margin: 0 0 6px 0; font-size: 1.20rem; font-weight: 700; color: #0F172A;">
                    {v_info.get('title', 'YouTube Video')}
                </h3>
                <div style="font-size: 0.86rem; color: #475569; margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 12px;">
                    <span>👤 ช่อง: <b>{v_info.get('channel', 'N/A')}</b></span>
                    <span>⏱️ ความยาว: <b>{format_timestamp(v_info.get('duration', 0))}</b></span>
                    <span>🌐 ภาษาต้นฉบับ: <b style="color: #2563EB;">{lang_name}</b></span>
                    <span>📝 จำนวนย่อหน้า: <b>{len(orig_paras):,} ย่อหน้า</b></span>
                </div>
            """, unsafe_allow_html=True)
            
            c_link1, c_link2 = st.columns([1.5, 1.5])
            with c_link1:
                st.link_button("▶️ เปิดรับชมบน YouTube", v_info.get('url', ''), use_container_width=True)
            with c_link2:
                with st.popover("📺 เล่นวิดีโอในหน้านี้", use_container_width=True):
                    st.video(v_info.get('url', ''))

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # แถบสลับภาษาแสดงผล & ดาวน์โหลด (แสดงเสมอเมื่อเป็นคลิปต่างประเทศ)
        if is_foreign:
            selected_view_mode = st.radio(
                "🌐 เลือกภาษาที่ต้องการแสดงผลและดาวน์โหลด:",
                options=[
                    "🇹🇭 สคริปต์ฉบับแปลภาษาไทย (Thai Translation)", 
                    "🌐 สคริปต์ฉบับภาษาต้นฉบับ (Original Transcript)"
                ],
                index=0,
                horizontal=True,
                key="radio_view_lang_selector"
            )
            is_current_thai = "ภาษาไทย" in selected_view_mode
            
            # หากเลือกภาษาไทย แต่ thai_paras ยังไม่ได้ถูกแปล ให้แปลทันที
            if is_current_thai:
                if not thai_paras or thai_paras == orig_paras or not is_text_thai(" ".join(p['text'] for p in thai_paras[:5])):
                    with st.spinner("🇹🇭 กำลังแปลสคริปต์เป็นภาษาไทย (Auto-Translating to Thai)..."):
                        thai_paras = translate_paragraphs_to_thai(orig_paras)
                        st.session_state['transcript_data']['thai_paragraphs'] = thai_paras
                        st.session_state['transcript_data']['is_translated'] = True
                active_paragraphs = thai_paras
            else:
                active_paragraphs = orig_paras
        else:
            st.markdown("<p style='font-size: 0.88rem; font-weight: 700; color: #1E293B; margin-top: 6px;'>🇹🇭 สคริปต์คำบรรยายภาษาไทย (Native Thai Transcript):</p>", unsafe_allow_html=True)
            active_paragraphs = orig_paras
            is_current_thai = True

        # สร้างข้อความสำหรับ Export
        clean_txt = build_export_clean_text(active_paragraphs)
        md_txt = build_export_timestamped_md(active_paragraphs, v_info, is_thai=is_current_thai)
        srt_txt = build_export_srt(active_paragraphs)
        llm_prompt = build_export_llm_prompt(active_paragraphs, v_info)

        # ส่วนดาวน์โหลดผลลัพธ์ (4 Formats with UTF-8 BOM)
        st.markdown("#### 📥 ดาวน์โหลดสคริปต์ (Export Formats)")
        safe_title = re.sub(r'[^\w\-_\. ]', '_', v_info.get('title', 'transcript'))[:35]
        lang_suffix = "_th" if is_current_thai else "_orig"
        
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button(
                label="📄 Clean Text (.txt)",
                data=wrap_utf8_bom(clean_txt),
                file_name=f"{safe_title}{lang_suffix}_clean.txt",
                mime="text/plain",
                use_container_width=True
            )
        with d2:
            st.download_button(
                label="⏱️ Timestamps (.md)",
                data=wrap_utf8_bom(md_txt),
                file_name=f"{safe_title}{lang_suffix}_timestamps.md",
                mime="text/markdown",
                use_container_width=True
            )
        with d3:
            st.download_button(
                label="🎬 Subtitles (.srt)",
                data=wrap_utf8_bom(srt_txt),
                file_name=f"{safe_title}{lang_suffix}.srt",
                mime="text/plain",
                use_container_width=True
            )
        with d4:
            st.download_button(
                label="🤖 AI/LLM Prompt (.txt)",
                data=wrap_utf8_bom(llm_prompt),
                file_name=f"{safe_title}{lang_suffix}_ai_prompt.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # ช่องค้นหาคำในสคริปต์แบบ Real-time Text Search
        st.markdown("#### 👁️ ตัวอย่างเนื้อหาสคริปต์ (Interactive Preview)")
        search_kw = st.text_input("🔍 ค้นหาคำหรือประโยคในสคริปต์:", placeholder="พิมพ์คำที่ต้องการค้นหา เช่น AI, ข่าว, สรุป...")

        # แท็บแสดงผล 4 มุมมอง
        tab_time, tab_clean, tab_prompt, tab_srt = st.tabs([
            "⏱️ สคริปต์พร้อม Timestamp", 
            "📄 ข้อความต่อเนื่อง (Clean Text)", 
            "🤖 พร้อมส่งให้ AI สรุป (AI Prompt Ready)", 
            "🎬 โครงสร้าง Subtitle (.srt)"
        ])

        with tab_time:
            filtered_paras = [p for p in active_paragraphs if search_kw.lower() in p['text'].lower()] if search_kw else active_paragraphs
            if not filtered_paras:
                st.info(f"💡 ไม่พบข้อความที่ตรงกับ '{search_kw}'")
            else:
                if search_kw:
                    st.caption(f"พบคำค้นหาทั้งหมด {len(filtered_paras)} ย่อหน้า")
                for p in filtered_paras:
                    time_lbl = format_timestamp(p['start'])
                    txt = p['text']
                    if search_kw:
                        txt = re.sub(f"({re.escape(search_kw)})", r":orange[**\1**]", txt, flags=re.IGNORECASE)
                    st.markdown(f"""
                        <div class="yt-para-box">
                            <span style="background: #2563EB; color: white; padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 0.78rem; margin-right: 8px;">
                                {time_lbl}
                            </span>
                            {txt}
                        </div>
                    """, unsafe_allow_html=True)

        with tab_clean:
            st.text_area("Clean Continuous Text", clean_txt, height=380)

        with tab_prompt:
            st.text_area("พร้อม Copy ไปวางใน ChatGPT, Claude, Gemini ได้ทันที:", llm_prompt, height=380)

        with tab_srt:
            st.text_area("SRT Preview", srt_txt[:5000] + ("\n... (แสดงตัวอย่างบางส่วน ดาวน์โหลดไฟล์เต็มได้ที่ปุ่มด้านบน)" if len(srt_txt) > 5000 else ""), height=380)
