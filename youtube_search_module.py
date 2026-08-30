import streamlit as st
import requests
import json
import re
import urllib.parse
import unicodedata
from datetime import datetime

# Headers จำลอง Browser สำหรับ YouTube Search Scraper (Zero-API-Key)
YOUTUBE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# Cookie ระบุโซนประเทศไทยและภาษาไทยสำหรับ YouTube
YOUTUBE_COOKIES = {
    'PREF': 'hl=th&gl=TH'
}

# พารามิเตอร์การจัดเรียงของ YouTube (sp parameters)
SORT_SP_MAPPING = {
    "upload_date": "CAISBAgCEAE%3D",   # อัปโหลดล่าสุด (Upload date - Newest first)
    "relevance": "",                   # ความเกี่ยวข้อง (Relevance)
    "view_count": "CAMSAhAB",          # ยอดวิวสูงสุด (View count)
    "rating": "CAESAhAB"               # คะแนนความนิยม / เรตติ้ง (Rating)
}

QUICK_TOPICS = [
    ("⚡ ข่าวไอทีล่าสุด", "ข่าวไอทีล่าสุด"),
    ("⚽ ไฮไลท์ฟุตบอล", "ไฮไลท์ฟุตบอล"),
    ("🤖 AI & Python", "AI & Python"),
    ("🍿 สปอยล์หนัง", "สปอยล์หนัง"),
    ("🎶 รวมเพลงเพราะ", "รวมเพลงเพราะ"),
    ("🙏 หลวงตาสุริยา", "หลวงตาสุริยา วัดป่าธรรมอุทยาน"),
    ("📈 วิเคราะห์ตลาด & หุ้น", "วิเคราะห์หุ้น ตลาดหุ้น")
]


# Regex สำหรับอักษรที่ไม่ใช่ละตินและไม่ใช่ไทย (เช่น จีน ญี่ปุ่น เกาหลี รัสเซีย อาหรับ ฮินดี ลาว พม่า ฯลฯ)
NON_LATIN_THAI_REGEX = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff\u0900-\u097f\u0e80-\u0eff\u1000-\u109f]')

# เครื่องหมายกำกับเสียงเฉพาะภาษาอื่น (เวียดนาม, ฝรั่งเศส, สเปน, เยอรมัน, โปแลนด์ ฯลฯ ที่ภาษาอังกฤษแทบไม่ใช้)
FOREIGN_DIACRITICS_REGEX = re.compile(r'[àáâãäåæçèéêëìíîïðñòóôõöøùúûüýÿđơưăảẽỉỏũạẹọụừứờớàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵßŁłŻżĆćŚśŹźñ¿¡«»]')

# คำเฉพาะ / Stopwords ของภาษาละตินอื่นๆ (ฝรั่งเศส, เวียดนาม, สเปน, โปรตุเกส, อินโดนีเซีย, เยอรมัน, อิตาลี ฯลฯ)
FOREIGN_STOPWORDS = {
    # French
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'en', 'ce', 'cette', 'ces', 'dans', 'pour', 'avec', 'sur', 'par', 
    'qui', 'que', 'quoi', 'dont', 'où', 'est', 'sont', 'fait', 'tout', 'tous', 'toute', 'toutes', 'monde', 'sa', 'son', 'ses', 
    'leur', 'leurs', 'nous', 'vous', 'ils', 'elles', 'seule', 'seul', 'garçon', 'haït', 'soigner', 'jambe', 'regarder', 'mineurs',
    'suivre', 'déclaration', 'histoire', 'film', 'complet', 'bande', 'annonce', 'vf', 'vostfr', 'épisode', 'chanson', 'avec',
    # Vietnamese
    'của', 'và', 'các', 'có', 'được', 'cho', 'trong', 'với', 'không', 'những', 'người', 'này', 'đã', 'để', 'khi', 'từ', 'vào', 
    'một', 'nhiều', 'như', 'là', 'tại', 'tự', 'khác', 'biệt', 'đáng', 'kinh', 'ngạc', 'thành', 'phố', 'việt', 'nam', 'hà', 'nội', 
    'sài', 'gòn', 'tập', 'phim', 'thuyết', 'minh', 'lồng', 'tiếng', 'full', 'trọn', 'bộ', 'hài', 'hước', 'địa', 'lý',
    # Spanish
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'del', 'al', 'con', 'por', 'para', 'como', 'pero', 'sus', 'este', 'esta',
    'estos', 'estas', 'partido', 'resumen', 'goles', 'capítulo', 'completo', 'película', 'serie', 'enlace', 'noticias', 'canción',
    # Portuguese
    'o', 'a', 'os', 'as', 'um', 'uma', 'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'pelo', 'pela', 'pelos', 'pelas',
    'para', 'com', 'não', 'mais', 'como', 'mas', 'foi', 'resumo', 'jogo', 'capítulo', 'completo', 'filme', 'música',
    # Indonesian / Malay
    'yang', 'di', 'dan', 'itu', 'dengan', 'untuk', 'tidak', 'ini', 'dari', 'dalam', 'akan', 'pada', 'juga', 'saya', 'ke', 'karena',
    'tersebut', 'bisa', 'ada', 'mereka', 'lebih', 'sudah', 'atau', 'saat', 'oleh', 'telah', 'kita', 'menjadi', 'orang', 'sangat',
    'cara', 'membuat', 'lagu', 'alur', 'cerita', 'film', 'terbaru', 'lengkap', 'bahasa', 'indonesia',
    # German & Italian
    'der', 'die', 'das', 'und', 'den', 'von', 'dem', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'nicht', 'ein', 'eine',
    'della', 'delle', 'degli', 'nella', 'nelle', 'sono', 'questo', 'questa', 'perché', 'anche'
}


def is_thai_text(text: str) -> bool:
    """ตรวจสอบว่าข้อความมีตัวอักษรภาษาไทยหรือไม่"""
    if not text:
        return False
    return bool(re.search(r'[\u0e00-\u0e7f]', str(text)))


def is_thai_content(item: dict) -> bool:
    """
    ตรวจสอบว่าวิดีโอเป็นคอนเทนต์ภาษาไทยแท้ 100% หรือไม่
    - ตรวจจากชื่อคลิป (Title) โดยตรงว่ามีตัวอักษรภาษาไทยหรือไม่
    - ไม่อ้างอิงชื่อช่อง (Channel) เนื่องจาก YouTube UI ภาษาไทยจะมีการแทรกข้อความไทยอัตโนมัติ
      (เช่น '...และอีก 2 ช่อง', '...และ Better Creating') ซึ่งทำให้คลิปภาษาอื่นหลุดเข้ามา
    """
    if not item:
        return False
    title = item.get("title", "")
    return is_thai_text(title)


def is_pure_english_text(text: str) -> bool:
    """
    ตรวจสอบข้อความว่าเป็นภาษาอังกฤษแท้ 100% หรือไม่
    (ใช้ระบบ Character Whitelist อนุญาตเฉพาะตัวอักษรละตินมาตรฐาน A-Z, ตัวเลข, สัญลักษณ์, อีโมจิ
     และตัดภาษาต่างประเทศทุกภาษา เช่น อินเดีย (Telugu/Hindi/Tamil), เวียดนาม, ฝรั่งเศส, จีน, ญี่ปุ่น, เกาหลี, อาหรับ, รัสเซีย ฯลฯ ออกทั้งหมด)
    """
    if not text or not str(text).strip():
        return False
    # หากมีตัวอักษรไทย ถือว่าเป็นภาษาไทย
    if is_thai_text(text):
        return False

    # ตรวจสอบทุกตัวอักษร: ไม่อนุญาตตัวอักษรภาษาอื่น (Non-ASCII) นอกเหนือจากเครื่องหมายสากล/อีโมจิ
    for ch in str(text):
        cp = ord(ch)
        if cp <= 127:  # Standard ASCII (A-Z, a-z, 0-9, standard symbols, space)
            continue
        if 0x2000 <= cp <= 0x206F:  # Smart quotes, dashes, bullets, ellipses
            continue
        if 0x20A0 <= cp <= 0x20CF:  # Currency symbols
            continue
        if (0x2190 <= cp <= 0x2BFF) or (0x1F000 <= cp <= 0x1FAFF):  # Emojis & misc UI symbols
            continue
        # พบตัวอักษรของภาษาอื่น เช่น อินเดีย (Telugu/Hindi/Tamil), จีน, เวียดนาม, ฝรั่งเศส ฯลฯ
        return False

    # ตรวจสอบคำศัพท์กับฐานข้อมูลคำภาษาอื่น (เช่น ฝรั่งเศส, สเปน, อินโดนีเซีย ที่เขียนด้วย ASCII ทั่วไป)
    words = [w for w in re.findall(r'[a-zA-Z]+', str(text).lower()) if len(w) > 1]
    if not words:
        return False
    foreign_cnt = sum(1 for w in words if w in FOREIGN_STOPWORDS)
    if foreign_cnt >= 1 and (foreign_cnt / len(words) >= 0.15 or foreign_cnt >= 2):
        return False

    return True


def is_thai_or_english_content(item: dict) -> bool:
    """
    ตรวจสอบว่าวิดีโอเป็นภาษาไทยหรือภาษาอังกฤษเท่านั้น
    (ตัดภาษาอื่นออก 100% เช่น ภาษาอินเดีย, ฝรั่งเศส, เวียดนาม, สเปน, โปรตุเกส, อินโดนีเซีย, จีน, ญี่ปุ่น, เกาหลี, รัสเซีย, อาหรับ ฯลฯ)
    """
    if not item:
        return False
    if is_thai_content(item):
        return True
    
    title = item.get("title", "")
    channel = item.get("channel", "")
    clean_channel = re.sub(r'\s*และ\s*', ' ', channel)
    
    # หากไม่ใช่ภาษาไทย ให้ตรวจสอบว่าทั้งชื่อคลิปและชื่อช่องเป็นภาษาอังกฤษแท้
    return is_pure_english_text(title) and (not channel or is_pure_english_text(clean_channel))


def detect_lang_tag(item: dict) -> str:
    """
    ระบุแท็กภาษาสำหรับแสดงผลบนการ์ดวิดีโอ:
    - 'TH': 🇹🇭 ไทย
    - 'EN': 🇬🇧 English
    - 'INT': 🌐 สากล
    """
    if not item:
        return "INT"
    if is_thai_content(item):
        return "TH"
    title = item.get("title", "")
    channel = item.get("channel", "")
    clean_channel = re.sub(r'\s*และ\s*', ' ', channel)
    if is_pure_english_text(title) and (not channel or is_pure_english_text(clean_channel)):
        return "EN"
    return "INT"


def parse_relative_time_to_minutes(text: str) -> float:
    """
    แปลงข้อความเวลาที่เผยแพร่ (เช่น 15 นาทีที่ผ่านมา, 2 ชม. ที่แล้ว, 3 days ago)
    เป็นค่านาทีเพื่อใช้จัดเรียงลำดับจากใหม่สุดไปเก่าสุดอย่างแม่นยำ
    """
    if not text:
        return 999999999.0
    text_clean = str(text).lower().replace(',', '').strip()

    # หากเป็น Live สด ให้ความสำคัญสูงสุด (0 นาที)
    if any(k in text_clean for k in ['สด', 'live', 'กำลังสตรีม', 'premiering']):
        return 0.0

    num_match = re.search(r'(\d+(?:\.\d+)?)', text_clean)
    num = float(num_match.group(1)) if num_match else 1.0

    if any(u in text_clean for u in ['วินาที', 'sec', 'second']):
        return num / 60.0
    elif any(u in text_clean for u in ['นาที', 'min', 'minute']):
        return num
    elif any(u in text_clean for u in ['ชั่วโมง', 'ชม', 'hour', 'hr']):
        return num * 60.0
    elif any(u in text_clean for u in ['วัน', 'day']):
        return num * 1440.0
    elif any(u in text_clean for u in ['สัปดาห์', 'week']):
        return num * 10080.0
    elif any(u in text_clean for u in ['เดือน', 'month']):
        return num * 43200.0
    elif any(u in text_clean for u in ['ปี', 'year', 'yr']):
        return num * 525600.0

    return 999999999.0


def _extract_video_renderer_data(vr: dict) -> dict:
    """สกัดข้อมูลจาก videoRenderer object ของ YouTube อย่างปลอดภัย"""
    try:
        video_id = vr.get('videoId')
        if not video_id:
            return None

        # Title
        title_obj = vr.get('title', {})
        if 'runs' in title_obj and title_obj['runs']:
            title = "".join([r.get('text', '') for r in title_obj['runs']])
        else:
            title = title_obj.get('simpleText', f"YouTube Video ({video_id})")

        # Channel
        channel_obj = vr.get('ownerText', {}) or vr.get('shortBylineText', {})
        if 'runs' in channel_obj and channel_obj['runs']:
            channel = "".join([r.get('text', '') for r in channel_obj['runs']])
        else:
            channel = channel_obj.get('simpleText', 'YouTube Creator')

        # Views
        views_obj = vr.get('viewCountText', {}) or vr.get('shortViewCountText', {})
        if 'simpleText' in views_obj:
            views = views_obj['simpleText']
        elif 'runs' in views_obj and views_obj['runs']:
            views = "".join([r.get('text', '') for r in views_obj['runs']])
        else:
            views = "ยอดวิวไม่ระบุ"

        # Published Time
        pub_obj = vr.get('publishedTimeText', {})
        published = pub_obj.get('simpleText', 'ไม่ระบุเวลา')

        # Duration
        dur_obj = vr.get('lengthText', {})
        if 'simpleText' in dur_obj:
            duration = dur_obj['simpleText']
        elif 'runs' in dur_obj and dur_obj['runs']:
            duration = "".join([r.get('text', '') for r in dur_obj['runs']])
        else:
            badges = vr.get('badges', [])
            is_live = False
            for b in badges:
                badge_text = b.get('metadataBadgeRenderer', {}).get('label', '')
                if 'LIVE' in badge_text.upper() or 'สด' in badge_text:
                    is_live = True
                    break
            duration = "🔴 LIVE" if is_live else "N/A"

        # Thumbnail (HD Priority)
        thumbnails = vr.get('thumbnail', {}).get('thumbnails', [])
        if thumbnails:
            thumbnail = thumbnails[-1].get('url', f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg")
            if thumbnail.startswith("//"):
                thumbnail = "https:" + thumbnail
        else:
            thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        # Description snippet
        desc_obj = vr.get('descriptionSnippet', {}) or vr.get('detailedMetadataSnippets', [{}])[0].get('snippetText', {})
        if 'runs' in desc_obj and desc_obj['runs']:
            description = "".join([r.get('text', '') for r in desc_obj['runs']])
        elif 'simpleText' in desc_obj:
            description = desc_obj['simpleText']
        else:
            description = ""

        norm_title = unicodedata.normalize("NFC", str(title).strip())
        norm_channel = unicodedata.normalize("NFC", str(channel).strip())
        norm_desc = unicodedata.normalize("NFC", str(description).strip())

        item_dict = {
            "id": str(video_id).strip(),
            "title": norm_title,
            "channel": norm_channel,
            "views": str(views).strip(),
            "published": str(published).strip(),
            "duration": str(duration).strip(),
            "thumbnail": str(thumbnail).strip(),
            "description": norm_desc,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "time_minutes": parse_relative_time_to_minutes(published)
        }
        item_dict["is_thai"] = is_thai_content(item_dict)
        item_dict["is_thai_or_eng"] = is_thai_or_english_content(item_dict)
        item_dict["lang_tag"] = detect_lang_tag(item_dict)
        return item_dict
    except Exception:
        return None


@st.cache_data(ttl=180, show_spinner=False)
def fetch_youtube_search_results(
    query: str, 
    sort_by: str = "upload_date", 
    max_results: int = 30,
    lang_filter: str = "thai_first"
) -> list:
    """
    ค้นหาคลิปวิดีโอจาก YouTube Search โดยตรง (Zero-API-Key Mode)
    รองรับการดึงผลลัพธ์จำนวนมาก (10-300 คลิป) ผ่าน Multi-page Pagination
    พร้อมระบบคัดกรองและให้ความสำคัญกับเนื้อหาภาษาไทยและภาษาอังกฤษ
    และจัดเรียงตามลำดับเวลาล่าสุด (Newest First) พร้อมแคชข้อมูล 3 นาที
    """
    if not query or not query.strip():
        return []

    encoded_query = urllib.parse.quote_plus(query.strip())
    sp = SORT_SP_MAPPING.get(sort_by, "CAISBAgCEAE%3D")
    url = f"https://www.youtube.com/results?search_query={encoded_query}&gl=TH&hl=th"
    if sp:
        url += f"&sp={sp}"

    results = []
    seen_ids = set()
    continuation_token = None

    try:
        resp = requests.get(url, headers=YOUTUBE_HEADERS, cookies=YOUTUBE_COOKIES, timeout=(5, 12))
        if resp.status_code == 200:
            match = re.search(r'var ytInitialData\s*=\s*({.+?});</script>', resp.text)
            if not match:
                match = re.search(r'ytInitialData\s*=\s*({.+?});', resp.text)

            if match:
                data = json.loads(match.group(1))

                sections = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])

                for sec in sections:
                    item_sec = sec.get('itemSectionRenderer', {})
                    items = item_sec.get('contents', [])
                    for it in items:
                        if 'videoRenderer' in it:
                            parsed = _extract_video_renderer_data(it['videoRenderer'])
                            if parsed and parsed['id'] not in seen_ids:
                                seen_ids.add(parsed['id'])
                                results.append(parsed)

                    if 'continuationItemRenderer' in sec:
                        endpoint = sec['continuationItemRenderer'].get('continuationEndpoint', {})
                        continuation_token = endpoint.get('continuationCommand', {}).get('token')

                if not continuation_token and len(sections) > 0 and 'continuationItemRenderer' in sections[-1]:
                    endpoint = sections[-1]['continuationItemRenderer'].get('continuationEndpoint', {})
                    continuation_token = endpoint.get('continuationCommand', {}).get('token')

                # Pagination: หากต้องการกรองภาษา ให้ดึงเผื่อไว้เพื่อให้ได้คลิปครบตามจำนวน
                target_fetch_count = max_results if lang_filter == "all" else max(max_results + 15, int(max_results * 1.5))
                max_loop_steps = min(30, (target_fetch_count // 10) + 5)
                loop_step = 0

                def should_continue_fetching() -> bool:
                    if not continuation_token or loop_step >= max_loop_steps:
                        return False
                    if lang_filter == "thai_only":
                        thai_count = sum(1 for r in results if r.get("is_thai", False))
                        return thai_count < max_results
                    elif lang_filter == "thai_and_eng":
                        th_en_count = sum(1 for r in results if r.get("is_thai_or_eng", False))
                        return th_en_count < max_results
                    return len(results) < target_fetch_count

                while should_continue_fetching():
                    loop_step += 1
                    payload = {
                        'context': {
                            'client': {
                                'clientName': 'WEB',
                                'clientVersion': '2.20240101.00.00',
                                'hl': 'th',
                                'gl': 'TH'
                            }
                        },
                        'continuation': continuation_token
                    }
                    try:
                        c_resp = requests.post(
                            'https://www.youtube.com/youtubei/v1/search',
                            json=payload,
                            headers={'Content-Type': 'application/json', 'User-Agent': YOUTUBE_HEADERS['User-Agent']},
                            cookies=YOUTUBE_COOKIES,
                            timeout=(4, 10)
                        )
                        continuation_token = None
                        if c_resp.status_code == 200:
                            c_data = c_resp.json()
                            actions = c_data.get('onResponseReceivedCommands', [])
                            added_this_round = 0
                            for act in actions:
                                app_items = act.get('appendContinuationItemsAction', {}).get('continuationItems', [])
                                for ai in app_items:
                                    if 'itemSectionRenderer' in ai:
                                        for it in ai['itemSectionRenderer'].get('contents', []):
                                            if 'videoRenderer' in it:
                                                parsed = _extract_video_renderer_data(it['videoRenderer'])
                                                if parsed and parsed['id'] not in seen_ids:
                                                    seen_ids.add(parsed['id'])
                                                    results.append(parsed)
                                                    added_this_round += 1
                                    if 'continuationItemRenderer' in ai:
                                        endpoint = ai['continuationItemRenderer'].get('continuationEndpoint', {})
                                        continuation_token = endpoint.get('continuationCommand', {}).get('token')
                            if added_this_round == 0:
                                break
                        else:
                            break
                    except Exception:
                        break
    except Exception:
        pass

    # เรียงลำดับตามเวลาล่าสุดก่อน (Upload Date)
    if sort_by == "upload_date" and results:
        results = sorted(results, key=lambda x: x.get("time_minutes", 999999999.0))

    # กรองและจัดลำดับตามภาษา (Language Filtering / Prioritization)
    if lang_filter == "thai_only":
        results = [r for r in results if r.get("is_thai", False)]
    elif lang_filter == "thai_and_eng":
        results = [r for r in results if r.get("is_thai_or_eng", False)]
    elif lang_filter == "thai_first":
        thai_videos = [r for r in results if r.get("is_thai", False)]
        other_videos = [r for r in results if not r.get("is_thai", False)]
        results = thai_videos + other_videos

    return results[:max_results]


def _init_session_states():
    """เตรียมสถานะ Session State สำหรับ YouTube Search Hub"""
    if "yt_search_query" not in st.session_state:
        st.session_state["yt_search_query"] = "ข่าวไอทีล่าสุด"
    if "input_yt_search" not in st.session_state:
        st.session_state["input_yt_search"] = "ข่าวไอทีล่าสุด"
    if "yt_search_lang" not in st.session_state:
        st.session_state["yt_search_lang"] = "thai_first"
    if "yt_search_sort" not in st.session_state:
        st.session_state["yt_search_sort"] = "upload_date"
    if "yt_search_limit" not in st.session_state:
        st.session_state["yt_search_limit"] = 30
    if "yt_theater_video" not in st.session_state:
        st.session_state["yt_theater_video"] = None
    if "yt_search_favorites" not in st.session_state:
        st.session_state["yt_search_favorites"] = []
    if "yt_search_history" not in st.session_state:
        st.session_state["yt_search_history"] = ["ข่าวไอทีล่าสุด", "AI & Python", "ไฮไลท์ฟุตบอล"]


def add_to_favorites(video: dict):
    """เพิ่มคลิปลงในรายการโปรด"""
    if "yt_search_favorites" not in st.session_state:
        st.session_state["yt_search_favorites"] = []
    if not any(f.get("id") == video.get("id") for f in st.session_state["yt_search_favorites"]):
        st.session_state["yt_search_favorites"].append(video)
        st.toast(f"⭐ บันทึก '{video.get('title', '')[:30]}...' ลงในรายการโปรดแล้ว", icon="✅")


def remove_from_favorites(video_id: str):
    """ลบคลิปออกจากรายการโปรด"""
    if "yt_search_favorites" in st.session_state:
        st.session_state["yt_search_favorites"] = [
            f for f in st.session_state["yt_search_favorites"] if f.get("id") != video_id
        ]
        st.toast("🗑️ ลบออกจากรายการโปรดแล้ว", icon="ℹ️")


def is_in_favorites(video_id: str) -> bool:
    """ตรวจสอบว่าคลิปอยู่ในรายการโปรดหรือไม่"""
    return any(f.get("id") == video_id for f in st.session_state.get("yt_search_favorites", []))


def render_youtube_search_page():
    """หน้าหลัก YouTube Search Hub"""
    _init_session_states()

    st.markdown("""
        <style>
        .yt-header-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 18px;
            color: #ffffff;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        }
        .yt-header-title {
            font-size: 1.60rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .yt-header-sub {
            color: #94a3b8;
            font-size: 0.88rem;
            margin: 0;
        }
        .yt-badge-live {
            background: #ef4444;
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        .yt-card-container {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            flex-direction: column;
            height: 100%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            margin-bottom: 14px;
        }
        .yt-card-container:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.08);
            border-color: #cbd5e1;
        }
        .yt-thumb-box {
            position: relative;
            width: 100%;
            padding-top: 56.25%;
            background-color: #0f172a;
            overflow: hidden;
        }
        .yt-thumb-box img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .yt-duration-badge {
            position: absolute;
            bottom: 8px;
            right: 8px;
            background: rgba(15, 23, 42, 0.92);
            color: #ffffff;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            letter-spacing: 0.02em;
        }
        .yt-card-content {
            padding: 12px 14px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .yt-card-title {
            font-size: 0.92rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.35;
            margin-bottom: 8px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            min-height: 2.7em;
        }
        .yt-card-meta {
            font-size: 0.78rem;
            color: #64748b;
            margin-bottom: 4px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
        }
        .yt-card-desc {
            font-size: 0.76rem;
            color: #64748b;
            line-height: 1.35;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            margin-bottom: 10px;
            flex: 1;
        }
        .yt-theater-box {
            background: #0f172a;
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.15);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            color: #ffffff;
        }
        .yt-time-pill {
            background: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #bfdbfe;
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 0.72rem;
            font-weight: 700;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header Banner
    st.markdown("""
        <div class="yt-header-banner">
            <div class="yt-header-title">
                <span>🔍 YouTube Search Hub</span>
                <span class="yt-badge-live">⚡ เรียงลำดับคลิปใหม่ล่าสุด (Live Newest First)</span>
            </div>
            <p class="yt-header-sub">
                ค้นหาวิดีโอบน YouTube แบบเรียลไทม์ • เน้นคอนเทนต์ภาษาไทยเป็นหลัก • เรียงตามวัน-เวลาใหม่ล่าสุด • พร้อมโรงภาพยนตร์ส่วนตัว (Theater View)
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Quick Topics Bar
    st.markdown("<p style='font-size: 0.82rem; font-weight: 700; color: #475569; margin-bottom: 6px;'>⚡ ค้นหาด่วนตามหัวข้อยอดนิยม (ค้นหาตามภาษาที่เลือกไว้ทันที):</p>", unsafe_allow_html=True)
    q_cols = st.columns(len(QUICK_TOPICS))
    for i, (label, search_term) in enumerate(QUICK_TOPICS):
        if q_cols[i].button(label, key=f"quick_topic_{i}", use_container_width=True):
            st.session_state["yt_search_query"] = search_term
            st.session_state["input_yt_search"] = search_term
            st.session_state["yt_search_sort"] = "upload_date"
            if search_term not in st.session_state["yt_search_history"]:
                st.session_state["yt_search_history"].insert(0, search_term)
                st.session_state["yt_search_history"] = st.session_state["yt_search_history"][:10]
            st.rerun()

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # แท็บการใช้งาน
    tab1, tab2 = st.tabs([
        "🔍 ค้นหาวิดีโอ (Search Videos)",
        "⭐ รายการโปรด & ประวัติ (Favorites & History)"
    ])

    # ==========================================
    # TAB 1: ค้นหาวิดีโอ (Search Videos)
    # ==========================================
    with tab1:
        with st.container():
            col_search, col_lang, col_sort, col_limit, col_btn = st.columns([3.0, 1.8, 1.6, 1.2, 1.0])
            
            with col_search:
                current_query = st.text_input(
                    "🔍 คำค้นหา (Search Query):",
                    value=st.session_state.get("yt_search_query", "ข่าวไอทีล่าสุด"),
                    placeholder="พิมพ์คำค้นหา เช่น AI & Python, ไฮไลท์ฟุตบอล...",
                    key="input_yt_search"
                )

            with col_lang:
                lang_options = {
                    "🇹🇭 ภาษาไทยเป็นหลัก (Thai First)": "thai_first",
                    "🇹🇭 ภาษาไทยเท่านั้น (Thai Only)": "thai_only",
                    "🇹🇭🇬🇧 ไทยและอังกฤษเท่านั้น (Thai & English Only)": "thai_and_eng",
                    "🌐 รวมทุกภาษา (All Languages)": "all"
                }
                current_lang_val = st.session_state.get("yt_search_lang", "thai_first")
                lang_idx = 0
                for idx, (k, v) in enumerate(lang_options.items()):
                    if v == current_lang_val:
                        lang_idx = idx
                        break

                selected_lang_label = st.selectbox(
                    "🌐 ตัวกรองภาษา:",
                    options=list(lang_options.keys()),
                    index=lang_idx,
                    key="select_yt_lang"
                )
                selected_lang = lang_options[selected_lang_label]
                st.session_state["yt_search_lang"] = selected_lang

            with col_sort:
                sort_options = {
                    "🕒 อัปโหลดล่าสุด (Upload Date)": "upload_date",
                    "🎯 ความเกี่ยวข้อง (Relevance)": "relevance",
                    "🔥 ยอดวิวสูงสุด (View Count)": "view_count",
                    "⭐ คะแนนความนิยม (Rating)": "rating"
                }
                current_sort_val = st.session_state.get("yt_search_sort", "upload_date")
                sort_idx = 0
                for idx, (k, v) in enumerate(sort_options.items()):
                    if v == current_sort_val:
                        sort_idx = idx
                        break

                selected_sort_label = st.selectbox(
                    "📊 จัดเรียงผลลัพธ์:",
                    options=list(sort_options.keys()),
                    index=sort_idx,
                    key="select_yt_sort"
                )
                selected_sort = sort_options[selected_sort_label]

            with col_limit:
                limit_options = [10, 20, 30, 50, 100, 150, 200, 300]
                current_limit = st.session_state.get("yt_search_limit", 30)
                limit_idx = limit_options.index(current_limit) if current_limit in limit_options else 2
                selected_limit = st.selectbox(
                    "🔢 จำนวนคลิป:",
                    options=limit_options,
                    index=limit_idx,
                    key="select_yt_limit"
                )

            with col_btn:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                do_search = st.button("🚀 ค้นหา", use_container_width=True, type="primary", key="btn_yt_search")

        if do_search:
            st.session_state["yt_search_query"] = current_query
            st.session_state["yt_search_lang"] = selected_lang
            st.session_state["yt_search_sort"] = selected_sort
            st.session_state["yt_search_limit"] = selected_limit
            if current_query and current_query.strip():
                if current_query.strip() not in st.session_state["yt_search_history"]:
                    st.session_state["yt_search_history"].insert(0, current_query.strip())
                    st.session_state["yt_search_history"] = st.session_state["yt_search_history"][:10]
            st.rerun()

        # ==========================================
        # THEATER VIEW PLAYER
        # ==========================================
        theater_video = st.session_state.get("yt_theater_video")
        if theater_video:
            st.markdown("""
                <div class="yt-theater-box">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                            <span>🎬 โรงภาพยนตร์ส่วนตัว (Theater Mode)</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            t_col1, t_col2 = st.columns([2.4, 1.2])
            with t_col1:
                st.video(theater_video["url"])
            with t_col2:
                st.markdown(f"#### {theater_video['title']}")
                st.markdown(f"""
                    <div style='font-size: 0.85rem; color: #64748b; line-height: 1.6; margin-bottom: 14px;'>
                        👤 <b>ช่อง:</b> {theater_video['channel']}<br>
                        👁️ <b>ยอดวิว:</b> {theater_video['views']}<br>
                        🕒 <b>อัปโหลด:</b> <span class="yt-time-pill">{theater_video['published']}</span><br>
                        ⏱️ <b>ความยาว:</b> {theater_video['duration']}
                    </div>
                """, unsafe_allow_html=True)

                if theater_video.get("description"):
                    with st.expander("📝 คำอธิบายคลิปย่อ", expanded=False):
                        st.write(theater_video["description"])

                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                
                fav_col, close_col = st.columns(2)
                with fav_col:
                    is_fav = is_in_favorites(theater_video["id"])
                    if is_fav:
                        if st.button("❌ นำออกจากโปรด", key="theater_unfav_btn", use_container_width=True):
                            remove_from_favorites(theater_video["id"])
                            st.rerun()
                    else:
                        if st.button("⭐ บันทึกรายการโปรด", key="theater_fav_btn", use_container_width=True, type="secondary"):
                            add_to_favorites(theater_video)
                            st.rerun()

                with close_col:
                    if st.button("✖️ ปิดโรงภาพยนตร์", key="theater_close_btn", use_container_width=True):
                        st.session_state["yt_theater_video"] = None
                        st.rerun()

                st.link_button("🔗 เปิดดูบน YouTube โดยตรง", theater_video["url"], use_container_width=True)

            st.markdown("<hr style='margin: 18px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

        # ==========================================
        # แสดงผลการค้นหา
        # ==========================================
        active_query = st.session_state.get("yt_search_query", "ข่าวไอที เทคโนโลยี ล่าสุด")
        active_lang = st.session_state.get("yt_search_lang", "thai_first")
        active_sort = st.session_state.get("yt_search_sort", "upload_date")
        active_limit = st.session_state.get("yt_search_limit", 30)

        with st.spinner(f"⚡ กำลังดึง {active_limit} คลิปบน YouTube สำหรับ '{active_query}'..."):
            try:
                videos = fetch_youtube_search_results(
                    active_query, 
                    sort_by=active_sort, 
                    max_results=active_limit,
                    lang_filter=active_lang
                )
            except Exception as e:
                st.warning(f"⚠️ เกิดข้อผิดพลาดในการค้นหา: {str(e)}")
                videos = []

        if not videos:
            st.warning(f"⚠️ ไม่พบผลลัพธ์วิดีโอสำหรับคำค้นหา '{active_query}' หรือการเชื่อมต่อมีปัญหา กรุณาลองใช้คำค้นหาอื่น")
        else:
            sort_text = "🕒 จัดเรียง: อัปโหลดล่าสุด (ใหม่สุดไล่ลงไป)" if active_sort == "upload_date" else f"จัดเรียง: {active_sort}"
            if active_lang == "thai_first":
                lang_badge = "🇹🇭 เน้นภาษาไทยเป็นหลัก"
            elif active_lang == "thai_only":
                lang_badge = "🇹🇭 ภาษาไทยเท่านั้น"
            elif active_lang == "thai_and_eng":
                lang_badge = "🇹🇭🇬🇧 ไทย & อังกฤษเท่านั้น"
            else:
                lang_badge = "🌐 รวมทุกภาษา"

            st.markdown(f"""
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;'>
                    <span style='font-size: 1.05rem; font-weight: 700; color: #0f172a;'>
                        📺 ผลการค้นหา ({len(videos)} คลิป) สำหรับ: <span style='color: #2563eb;'>"{active_query}"</span>
                    </span>
                    <div style='display: flex; gap: 6px;'>
                        <span class="yt-time-pill" style="font-size: 0.78rem; padding: 3px 8px; background: #f0fdf4; color: #166534; border-color: #bbf7d0;">{lang_badge}</span>
                        <span class="yt-time-pill" style="font-size: 0.78rem; padding: 3px 8px;">{sort_text}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            quick_options = ["-- เลือกคลิปที่ต้องการสั่งเล่นทันที --"] + [
                f"[{v['published']} | {v['duration']}] {v['title'][:55]}... ({v['channel']})" for v in videos
            ]
            selected_quick = st.selectbox(
                "⚡ เล่นคลิปด่วนจากรายการค้นหา (เรียงตามลำดับเวลาล่าสุด):",
                options=quick_options,
                index=0,
                key="select_quick_play"
            )
            if selected_quick != "-- เลือกคลิปที่ต้องการสั่งเล่นทันที --":
                chosen_idx = quick_options.index(selected_quick) - 1
                if 0 <= chosen_idx < len(videos):
                    st.session_state["yt_theater_video"] = videos[chosen_idx]
                    st.rerun()

            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

            grid_cols = st.columns(3)
            for idx, vid in enumerate(videos):
                col = grid_cols[idx % 3]
                with col:
                    tag_type = vid.get('lang_tag', 'INT')
                    if tag_type == 'TH':
                        thai_tag = "<span style='background:#dcfce7; color:#15803d; font-size:0.70rem; font-weight:700; padding:1px 6px; border-radius:4px;'>🇹🇭 ไทย</span>"
                    elif tag_type == 'EN':
                        thai_tag = "<span style='background:#e0e7ff; color:#3730a3; font-size:0.70rem; font-weight:700; padding:1px 6px; border-radius:4px;'>🇬🇧 English</span>"
                    else:
                        thai_tag = "<span style='background:#f1f5f9; color:#64748b; font-size:0.70rem; font-weight:600; padding:1px 6px; border-radius:4px;'>🌐 สากล</span>"

                    st.markdown(f"""
                        <div class="yt-card-container">
                            <div class="yt-thumb-box">
                                <img src="{vid['thumbnail']}" alt="{vid['title']}" loading="lazy" />
                                <div class="yt-duration-badge">{vid['duration']}</div>
                            </div>
                            <div class="yt-card-content">
                                <div class="yt-card-title" title="{vid['title']}">{vid['title']}</div>
                                <div class="yt-card-meta">
                                    <span>👤 <b>{vid['channel']}</b></span>
                                    {thai_tag}
                                </div>
                                <div class="yt-card-meta" style="font-size: 0.76rem; color: #64748b;">
                                    <span class="yt-time-pill">🕒 {vid['published']}</span>
                                    <span>👁️ {vid['views']}</span>
                                </div>
                                <div class="yt-card-desc">{vid['description'] if vid['description'] else 'คลิกเพื่อรับชมวิดีโอนี้'}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    btn_c1, btn_c2 = st.columns([1.2, 1])
                    with btn_c1:
                        if st.button("▶️ เล่นคลิปนี้", key=f"btn_play_{vid['id']}_{idx}", use_container_width=True, type="primary"):
                            st.session_state["yt_theater_video"] = vid
                            st.rerun()
                    with btn_c2:
                        st.link_button("🔗 YouTube", vid["url"], use_container_width=True)

                    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # TAB 2: รายการโปรด & ประวัติการค้นหา
    # ==========================================
    with tab2:
        fav_tab_col1, fav_tab_col2 = st.columns([2, 1])

        with fav_tab_col1:
            favorites = st.session_state.get("yt_search_favorites", [])
            st.markdown(f"### ⭐ รายการคลิปโปรด ({len(favorites)} รายการ)")

            if not favorites:
                st.info("💡 ยังไม่มีคลิปในรายการโปรด — คุณสามารถกด '⭐ บันทึกรายการโปรด' จากหน้าค้นหาหรือขณะเล่นคลิปเพื่อเก็บไว้ดูภายหลังได้")
            else:
                for idx, fav in enumerate(favorites):
                    with st.container():
                        fc1, fc2 = st.columns([1.1, 2.2])
                        with fc1:
                            st.markdown(f"""
                                <div class="yt-thumb-box" style="border-radius: 8px;">
                                    <img src="{fav['thumbnail']}" alt="{fav['title']}" />
                                    <div class="yt-duration-badge">{fav['duration']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        with fc2:
                            st.markdown(f"**{fav['title']}**")
                            st.markdown(f"<p style='font-size: 0.8rem; color: #64748b; margin-bottom: 8px;'>👤 {fav['channel']} • 🕒 {fav.get('published', '-')} • 👁️ {fav['views']}</p>", unsafe_allow_html=True)
                            
                            act1, act2, act3 = st.columns([1.1, 1.1, 0.8])
                            with act1:
                                if st.button("▶️ เล่นคลิปนี้", key=f"fav_play_{fav['id']}_{idx}", use_container_width=True, type="primary"):
                                    st.session_state["yt_theater_video"] = fav
                                    st.rerun()
                            with act2:
                                st.link_button("🔗 YouTube", fav["url"], use_container_width=True)
                            with act3:
                                if st.button("🗑️ ลบ", key=f"fav_del_{fav['id']}_{idx}", use_container_width=True):
                                    remove_from_favorites(fav["id"])
                                    st.rerun()

                        st.markdown("<hr style='margin: 12px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

        with fav_tab_col2:
            st.markdown("### 🕒 คำค้นหาล่าสุด")
            history = st.session_state.get("yt_search_history", [])
            if not history:
                st.write("ยังไม่มีประวัติการค้นหา")
            else:
                for h_idx, h_query in enumerate(history):
                    if st.button(f"🔍 {h_query}", key=f"hist_btn_{h_idx}", use_container_width=True):
                        st.session_state["yt_search_query"] = h_query
                        st.session_state["input_yt_search"] = h_query
                        st.session_state["yt_search_sort"] = "upload_date"
                        st.rerun()

                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ ล้างประวัติการค้นหา", key="btn_clear_history", use_container_width=True):
                    st.session_state["yt_search_history"] = []
                    st.rerun()
