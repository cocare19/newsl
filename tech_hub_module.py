import streamlit as st
import requests
from bs4 import BeautifulSoup
import feedparser
import json
import re
from datetime import datetime
from dateutil import parser as date_parser

WEB_SOURCES = [
    ("🇹🇭 TNN Tech Reports", "https://www.tnnthailand.com/tech/"),
    ("🇹🇭 Blognone (ไอที & ธุรกิจเทคโนโลยี)", "https://www.blognone.com/"),
    ("🇹🇭 DroidSans (สมาร์ทโฟน, AI & Gadget)", "https://droidsans.com/"),
    ("🌐 TechCrunch (Global Tech & Startups)", "https://techcrunch.com/"),
    ("🌐 The Verge (Tech, AI & Gadgets)", "https://www.theverge.com/"),
]

PLAYLIST_SOURCES = [
    ("📱 TNN Tech Reports (Playlist ข่าว & นวัตกรรมเทคโนโลยี)", "https://www.youtube.com/playlist?list=PLr8CA-SlIPTQlN_u93VGyCeL5YDk5igf7"),
    ("🧠 Genwit อัจฉริยะพันธุ์ใหม่ (FULL EP - วิทยาศาสตร์ & ปัญญาประลอง)", "https://www.youtube.com/playlist?list=PLE3LvI8oc_pgz8DLiEL2cwOfJhtLBoBHg"),
    ("🎤 The Wall Song ร้องข้ามกำแพง (2026 | FULL EP)", "https://www.youtube.com/playlist?list=PLcwQy6DvJjsye5XTXOd8PUWO_xYxX3v6d"),
    ("🔥 The Wall Song ร้องข้ามกำแพง (2026 | Highlight)", "https://www.youtube.com/playlist?list=PLcwQy6DvJjsxQMBvw2y9o4zV_xU0K9qgO"),
    ("🎤 The Wall Song ร้องข้ามกำแพง (2025 | FULL EP)", "https://www.youtube.com/playlist?list=PLcwQy6DvJjsy5MM5BrMwH1sHB3c1bCOhb"),
    ("🔥 The Wall Song ร้องข้ามกำแพง (2025 | Highlight)", "https://www.youtube.com/playlist?list=PLcwQy6DvJjsxlM4BQIZOzp7NVQzj5BPOL"),
    ("🎶 The Wall Song ร้องข้ามกำแพง (รวมเพลงเพราะ)", "https://www.youtube.com/playlist?list=PLcwQy6DvJjsykyKjN9QuM6Zxz512zJVG8"),
    ("♠️ 4 โพดำ (FULL EP - วาไรตี้ดนตรี)", "https://www.youtube.com/playlist?list=PLTKzzsUPAwUiF9xWMvEbhD3Dr47MEtcM8"),
    ("🎭 4 โพดำการละคร (ละครซิตคอม & เพลง)", "https://www.youtube.com/playlist?list=PLX5ZfW-WYDaIVNpcg3RjMbT3G2CPXlgzs"),
    ("🎹 Piano & I Full Episode (โต๋ ศักดิ์สิทธิ์)", "https://www.youtube.com/playlist?list=PLtUbzX7Ih0cdimx9-47gWUdLPlclOCj14"),
]

# รายการช่อง YouTube ครบทุกหมวดหมู่ (IT, อนิเมะ/การ์ตูน/สปอยล์หนัง, ฟุตบอล)
CHANNEL_SOURCES = [
    # --- หมวด 1: IT, เทคโนโลยี & Coding ---
    ("🇹🇭 TNN Online (ข่าวสารทันโลก, ธุรกิจ & สาระความรู้)", "https://www.youtube.com/@TNN.Online/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCqUBA96OsqMgSFvTwLXY9yw", "IT & Tech"),
    ("⚡ Extreme IT (รีวิวไอที, จัดสเปกคอม, Gadget)", "https://www.youtube.com/@ExtremeIT/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UC1l9NQ__kCp9JoBnuZsaUjA", "IT & Tech"),
    ("👑 9arm (นายอาร์ม - เทคโนโลยี, AI & วงการไอที)", "https://www.youtube.com/@9arm./videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCoiEtD4v1qMAqHV5MDI5Qpg", "IT & Tech"),
    ("💻 TechOffside “ล้ำหน้าโชว์” (ข่าวไอที & เทคโนโลยี)", "https://www.youtube.com/@techoffside/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCaQSlfXVJAOE7wJYSIfOM9g", "IT & Tech"),
    ("🧑‍💻 mikelopster (โปรแกรมมิ่ง, AI & ซอฟต์แวร์)", "https://www.youtube.com/@mikelopster/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UC3YgTINPYQmUcRt5ZcNFIZQ", "IT & Tech"),
    ("🚀 MilerDev (Developer & AI Coding)", "https://www.youtube.com/@MilerDev/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCeKE6wQHTt5JpS9_RsH4hrg", "IT & Tech"),
    ("💼 noobitguy (บริหารงานแบบคนไอที & การทำงาน Tech)", "https://www.youtube.com/@noobitguy/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UChxmhkD8uSSzUOkfMO_p5oQ", "IT & Tech"),
    ("🔬 Jedi Trinupab (เจษฎา & เทคโนโลยี/การศึกษา)", "https://www.youtube.com/@jeditrinupab/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCgAZTX23heuJ8xoltU4VECA", "IT & Tech"),
    ("💻 Little Moments (IT, เทคโนโลยี & สาระความรู้)", "https://www.youtube.com/@LittleMomentsTH/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UC-Kk9Kr6K_J-dr7jK0RcOCg", "IT & Tech"),
    
    # --- หมวด 2: การ์ตูน, อนิเมะ & สปอยล์หนัง ---
    ("⚔️ KOMNA CHANNEL (สปอยล์อนิเมะ & วันพีช)", "https://www.youtube.com/@komnachannel6612/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCMJINLXtEr0G8F44Lmn5PgA", "Anime & Movies"),
    ("🍿 OverReview (สปอยล์หนัง / วันพีช & ภาพยนตร์)", "https://www.youtube.com/@OverReview.official/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCRQlHTeZ8HXLK8yxDWFXTug", "Anime & Movies"),
    ("🦸 ULTRA CHANNEL (อุลตร้าแมน & โทคุซัทสึ)", "https://www.youtube.com/@ULTRA_CHANNEL/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCwF1JCe4cgf9tEfDHplGqhA", "Anime & Movies"),
    ("🎌 Jovem Otaku (อนิเมะ & การ์ตูนญี่ปุ่น)", "https://www.youtube.com/@JovemOtaku/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCkZkNN_-iB8KZ0iEYO6yflg", "Anime & Movies"),

    # --- หมวด 3: ฟุตบอล & กีฬา ---
    ("⚽ Liverpool News Update (ชายผู้บ้าคลั่งลิเวอร์พูล)", "https://www.youtube.com/@Liverpoolnewsupdate./videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCo8fmZPIulzRYYqsdRTObEg", "Sports & Football"),
    ("⚽ SO Report by Sir-Oh (ลิเวอร์พูล)", "https://www.youtube.com/@SOReport/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UC1vMqYUL9ToAD_8H4kK7vsQ", "Sports & Football"),
    ("⚽ บอ บู๋ (วิเคราะห์ฟุตบอล & ข่าวฟุตบอล)", "https://www.youtube.com/@borbou23/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCsS1nKrY6qUx-6XW8e-Tuww", "Sports & Football"),
    ("⚽ LFC Zone (ลิเวอร์พูล)", "https://www.youtube.com/@LFCZone_th/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCL82HFRm67wKhp1emhExXeg", "Sports & Football"),
    ("⚽ L.F.C News (ข่าวสารลิเวอร์พูล & พรีเมียร์ลีก)", "https://www.youtube.com/@mobilelegends-ix4lo/videos", "https://www.youtube.com/feeds/videos.xml?channel_id=UCZPGPsGivKWuTBwpS9yKR3w", "Sports & Football"),
]

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7'
}

def normalize_youtube_url(url, entry=None):
    """แปลงลิงก์ YouTube (รวมถึง /shorts/, youtu.be, playlist url) ให้เป็นรูปแบบมาตรฐานสำหรับ Streamlit Player"""
    if entry is not None:
        if isinstance(entry, dict) and entry.get('id'):
            return f"https://www.youtube.com/watch?v={entry['id']}"
        if hasattr(entry, 'yt_videoid') and entry.yt_videoid:
            return f"https://www.youtube.com/watch?v={entry.yt_videoid}"
        if isinstance(entry, dict) and entry.get('yt_videoid'):
            return f"https://www.youtube.com/watch?v={entry['yt_videoid']}"
    
    m = re.search(r'(?:v=|\/shorts\/|youtu\.be\/|\/embed\/)([a-zA-Z0-9_-]{11})', str(url))
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    return str(url)

def parse_entry_date(entry):
    """ฟังก์ชันสกัดและแปลงวันเวลาของคลิป/บทความ"""
    date_str = getattr(entry, 'published', '') or getattr(entry, 'updated', '')
    if not date_str:
        return datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo)
    try:
        return date_parser.parse(date_str)
    except Exception:
        return datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo)

def get_recency_score(video_item):
    """
    คำนวณคะแนนความใหม่ (ยิ่งน้อย = ยิ่งใหม่ เช่น 0 = เพิ่งลง, ตัวเลขมาก = นานแล้ว)
    โดยตรวจจาก meta ('...ที่ผ่านมา', '...ที่แล้ว') และวันที่ในชื่อคลิป
    """
    meta = str(video_item.get('meta', ''))
    title = str(video_item.get('title', ''))
    
    # 1. ตรวจ relative time ใน meta เช่น "16 นาทีที่ผ่านมา", "14 ชั่วโมงที่ผ่านมา", "7 วันที่ผ่านมา", "2 ปีที่แล้ว"
    m_min = re.search(r'(\d+)\s*(?:นาที|minute)', meta)
    if m_min:
        return int(m_min.group(1)) * 1
    
    m_hr = re.search(r'(\d+)\s*(?:ชั่วโมง|hour)', meta)
    if m_hr:
        return int(m_hr.group(1)) * 60
    
    m_day = re.search(r'(\d+)\s*(?:วัน|day)', meta)
    if m_day:
        return int(m_day.group(1)) * 1440
    
    m_wk = re.search(r'(\d+)\s*(?:สัปดาห์|week)', meta)
    if m_wk:
        return int(m_wk.group(1)) * 10080
    
    m_mo = re.search(r'(\d+)\s*(?:เดือน|month)', meta)
    if m_mo:
        return int(m_mo.group(1)) * 43200
    
    m_yr = re.search(r'(\d+)\s*(?:ปี|year)', meta)
    if m_yr:
        return int(m_yr.group(1)) * 525600

    # 2. ตรวจวันที่ภาษาไทยในชื่อคลิป เช่น "19 ส.ค. 69", "3 เม.ย. 67"
    months = {
        'ม.ค.': 1, 'ก.พ.': 2, 'มี.ค.': 3, 'เม.ย.': 4, 'พ.ค.': 5, 'มิ.ย.': 6,
        'ก.ค.': 7, 'ส.ค.': 8, 'ก.ย.': 9, 'ต.ค.': 10, 'พ.ย.': 11, 'ธ.ค.': 12
    }
    date_m = re.search(r'(\d{1,2})\s*([ก-๙\.]+)\s*(\d{2,4})', title)
    if date_m:
        d = int(date_m.group(1))
        m_str = date_m.group(2)
        y = int(date_m.group(3))
        if y < 100:
            y += 2500
        for k, v in months.items():
            if k in m_str:
                days_since = (2570 - y) * 365 + (12 - v) * 30 + (31 - d)
                return days_since * 1440

    return 999999999

def extract_clean_time_label(meta_info, title=""):
    """
    ดึงเฉพาะข้อมูลเวลา/ความสดใหม่ที่กระชับ เพื่อแสดงใน Dropdown
    ตัดชื่อช่อง, ยอดวิว และคำฟุ่มเฟือยออก เหลือเฉพาะ เช่น '15 ชม. ก่อน', '7 วันก่อน', '1 เดือนก่อน' หรือ 'ล่าสุด'
    """
    if not meta_info:
        return "ล่าสุด"
    
    parts = [p.strip() for p in str(meta_info).split("•")]
    time_candidate = ""
    
    for p in parts:
        if "การดู" in p or "วิว" in p or "views" in p.lower():
            continue
        if any(w in p for w in ["ชั่วโมง", "นาที", "วัน", "สัปดาห์", "เดือน", "ปี", "ago", "ชม.", "min", "hour", "day", "week", "month", "year", "streamed"]):
            time_candidate = p
            break
        if re.search(r'\d{4}-\d{2}-\d{2}', p) or re.search(r'\d{1,2}\s+[ก-ฮ\.]+\s+\d{2,4}', p):
            time_candidate = p
            break

    if not time_candidate and title:
        m = re.search(r'(\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s*\d{2,4})', title)
        if m:
            time_candidate = m.group(1)

    if not time_candidate:
        non_views = [p for p in parts if "การดู" not in p and "views" not in p.lower()]
        time_candidate = non_views[-1] if non_views else parts[-1]

    time_clean = time_candidate.replace("ที่ผ่านมา", "ก่อน").replace("streamed", "").strip()
    return time_clean if time_clean else "ล่าสุด"

def extract_continuation_token(node):
    """ค้นหา Innertube Continuation Token เพื่อดึงข้อมูลคลิปหน้าถัดไปแบบไม่จำกัด"""
    found = []
    def _find(n):
        if isinstance(n, dict):
            if 'continuationCommand' in n:
                tok = n['continuationCommand'].get('token')
                if tok:
                    found.append(tok)
            for v in n.values():
                _find(v)
        elif isinstance(n, list):
            for it in n:
                _find(it)
    _find(node)
    return found[0] if found else None

def fetch_youtube_playlist_videos(playlist_info, max_items=30, sort_by="newest"):
    """
    ดึงคลิปวิดีโอจาก YouTube Playlist แบบยืดหยุ่น (สูงสุด 300 คลิป)
    รองรับการจัดเรียงคลิปตามเวลาจริง (Newest First), ลำดับเดิม (Original), หรือเก่าสุด (Oldest)
    """
    raw_url = playlist_info[1] if isinstance(playlist_info, (list, tuple)) else str(playlist_info)
    
    # สกัด playlist_id
    pl_id = raw_url
    if "playlist_id=" in raw_url:
        m = re.search(r'playlist_id=([a-zA-Z0-9_-]+)', raw_url)
        if m:
            pl_id = m.group(1)
    elif "list=" in raw_url:
        m = re.search(r'list=([a-zA-Z0-9_-]+)', raw_url)
        if m:
            pl_id = m.group(1)
    elif "/" in raw_url:
        pl_id = raw_url.rstrip("/").split("/")[-1]

    videos = []
    seen_ids = set()

    # 1. ดึงข้อมูลจากหน้าเว็บ YouTube Playlist โดยตรง
    try:
        url = f"https://www.youtube.com/playlist?list={pl_id}"
        r = requests.get(url, headers=HTTP_HEADERS, timeout=10)
        idx = r.text.find('ytInitialData')
        if idx != -1:
            sub = r.text[idx:]
            m = re.search(r'ytInitialData\s*=\s*(\{.*?\});\s*</script>', sub, re.DOTALL)
            if m:
                data = json.loads(m.group(1))

                def parse_item(node):
                    if isinstance(node, dict):
                        # Modern lockupViewModel
                        if 'lockupViewModel' in node:
                            lockup = node['lockupViewModel']
                            cid = lockup.get('contentId', '')
                            if not cid:
                                cid = lockup.get('rendererContext', {}).get('commandContext', {}).get('onTap', {}).get('innertubeCommand', {}).get('watchEndpoint', {}).get('videoId', '')
                            if cid and cid not in seen_ids:
                                metadata = lockup.get('metadata', {}).get('lockupMetadataViewModel', {})
                                title = metadata.get('title', {}).get('content', '')
                                if not title:
                                    title = lockup.get('rendererContext', {}).get('accessibilityContext', {}).get('label', '')
                                meta_rows = metadata.get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', [])
                                snippets = []
                                for row in meta_rows:
                                    for p in row.get('metadataParts', []):
                                        t = p.get('text', {}).get('content', '')
                                        if t:
                                            snippets.append(t)
                                seen_ids.add(cid)
                                videos.append({
                                    'id': cid,
                                    'title': title,
                                    'link': f"https://www.youtube.com/watch?v={cid}&list={pl_id}",
                                    'meta': " • ".join(snippets) if snippets else "ล่าสุด",
                                    'description': ''
                                })
                        # Classic playlistVideoRenderer
                        elif 'playlistVideoRenderer' in node:
                            pvr = node['playlistVideoRenderer']
                            cid = pvr.get('videoId', '')
                            if cid and cid not in seen_ids:
                                title = ""
                                if 'title' in pvr:
                                    if 'runs' in pvr['title']:
                                        title = "".join([x.get('text', '') for x in pvr['title']['runs']])
                                    elif 'simpleText' in pvr['title']:
                                        title = pvr['title']['simpleText']
                                snippets = []
                                if 'shortBylineText' in pvr and 'runs' in pvr['shortBylineText']:
                                    snippets.append(pvr['shortBylineText']['runs'][0].get('text', ''))
                                if 'lengthText' in pvr and 'simpleText' in pvr['lengthText']:
                                    snippets.append(pvr['lengthText']['simpleText'])
                                seen_ids.add(cid)
                                videos.append({
                                    'id': cid,
                                    'title': title,
                                    'link': f"https://www.youtube.com/watch?v={cid}&list={pl_id}",
                                    'meta': " • ".join(snippets) if snippets else "ล่าสุด",
                                    'description': ''
                                })
                        # Classic videoRenderer
                        elif 'videoRenderer' in node:
                            vr = node['videoRenderer']
                            cid = vr.get('videoId', '')
                            if cid and cid not in seen_ids:
                                title = ""
                                if 'title' in vr and 'runs' in vr['title']:
                                    title = "".join([x.get('text', '') for x in vr['title']['runs']])
                                elif 'simpleText' in vr['title']:
                                    title = vr['title']['simpleText']
                                seen_ids.add(cid)
                                videos.append({
                                    'id': cid,
                                    'title': title,
                                    'link': f"https://www.youtube.com/watch?v={cid}&list={pl_id}",
                                    'meta': "ล่าสุด",
                                    'description': ''
                                })
                        for v in node.values():
                            parse_item(v)
                    elif isinstance(node, list):
                        for item in node:
                            parse_item(item)

                parse_item(data)

                # ดึงหน้าถัดไปด้วย Continuation Token หากต้องการมากกว่าที่มีในหน้าแรก (สูงสุด 300 คลิป)
                fetch_pool_target = max(max_items, 300)
                if len(videos) < fetch_pool_target:
                    api_key_match = re.search(r'"INNERTUBE_API_KEY":"([a-zA-Z0-9_-]+)"', r.text)
                    if api_key_match:
                        api_key = api_key_match.group(1)
                        curr_token = extract_continuation_token(data)
                        attempts = 0
                        while curr_token and len(videos) < fetch_pool_target and attempts < 15:
                            attempts += 1
                            api_url = f"https://www.youtube.com/youtubei/v1/browse?key={api_key}"
                            payload = {
                                "context": {"client": {"clientName": "WEB", "clientVersion": "2.20240815.01.00", "hl": "th", "gl": "TH"}},
                                "continuation": curr_token
                            }
                            try:
                                r_cont = requests.post(api_url, json=payload, headers=HTTP_HEADERS, timeout=8)
                                if r_cont.status_code == 200:
                                    d_cont = r_cont.json()
                                    parse_item(d_cont)
                                    curr_token = extract_continuation_token(d_cont)
                                else:
                                    break
                            except Exception:
                                break
    except Exception:
        pass

    # 2. สำรองด้วย RSS Feed หากไม่ได้ผล
    if not videos and pl_id:
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={pl_id}"
            feed = feedparser.parse(feed_url)
            for e in feed.entries:
                vid = getattr(e, 'yt_videoid', '')
                title = getattr(e, 'title', '')
                link = getattr(e, 'link', f"https://www.youtube.com/watch?v={vid}&list={pl_id}")
                pub = getattr(e, 'published', '')[:10]
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    videos.append({
                        'id': vid,
                        'title': title,
                        'link': link,
                        'meta': pub or "ล่าสุด",
                        'description': getattr(e, 'description', '')
                    })
        except Exception:
            pass

    # 3. จัดเรียงตามเงื่อนไขที่ผู้ใช้เลือกก่อนตัดตามจำนวน max_items
    if sort_by == "newest":
        videos = sorted(videos, key=get_recency_score)
    elif sort_by == "oldest":
        videos = sorted(videos, key=get_recency_score, reverse=True)
    # else original: keep as is

    return videos[:max_items]

def fetch_youtube_channel_videos(channel_info, max_items=20, sort_by="newest"):
    """
    ดึงคลิปวิดีโอจาก YouTube Channel แบบยืดหยุ่น (1-100 คลิป)
    รองรับการจัดเรียงคลิปตามเวลาจริง (Newest First), ลำดับเดิม (Original), หรือเก่าสุด (Oldest)
    """
    web_url = channel_info[1] if isinstance(channel_info, (list, tuple)) else channel_info
    feed_url = channel_info[2] if isinstance(channel_info, (list, tuple)) and len(channel_info) > 2 else ""
    
    videos = []
    seen_ids = set()
    
    # 1. ดึงข้อมูลจากหน้าเว็บ YouTube /videos เพื่อให้ได้คลิปจำนวนมาก (สูงสุด 100 คลิป)
    try:
        url = web_url
        if "@" in url and not url.endswith("/videos"):
            url = url.rstrip("/") + "/videos"
        elif "channel/" in url and not url.endswith("/videos"):
            url = url.rstrip("/") + "/videos"
            
        r = requests.get(url, headers=HTTP_HEADERS, timeout=8)
        idx = r.text.find('ytInitialData')
        if idx != -1:
            sub = r.text[idx:]
            m = re.search(r'ytInitialData\s*=\s*(\{.*?\});\s*</script>', sub, re.DOTALL)
            if m:
                data = json.loads(m.group(1))
                
                def parse_item(node):
                    if isinstance(node, dict):
                        # Modern lockupViewModel
                        if 'lockupViewModel' in node:
                            lockup = node['lockupViewModel']
                            cid = lockup.get('contentId', '')
                            if not cid:
                                cid = lockup.get('rendererContext', {}).get('commandContext', {}).get('onTap', {}).get('innertubeCommand', {}).get('watchEndpoint', {}).get('videoId', '')
                            if cid and cid not in seen_ids:
                                metadata = lockup.get('metadata', {}).get('lockupMetadataViewModel', {})
                                title = metadata.get('title', {}).get('content', '')
                                meta_rows = metadata.get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', [])
                                snippets = []
                                for row in meta_rows:
                                    for p in row.get('metadataParts', []):
                                        t = p.get('text', {}).get('content', '')
                                        if t:
                                            snippets.append(t)
                                seen_ids.add(cid)
                                videos.append({
                                    'id': cid,
                                    'title': title,
                                    'link': f"https://www.youtube.com/watch?v={cid}",
                                    'meta': " • ".join(snippets) if snippets else "ล่าสุด",
                                    'description': ''
                                })
                        # Classic videoRenderer
                        if 'videoRenderer' in node:
                            vr = node['videoRenderer']
                            vid = vr.get('videoId')
                            if vid and vid not in seen_ids:
                                title = ""
                                if 'title' in vr and 'runs' in vr['title']:
                                    title = "".join([x.get('text', '') for x in vr['title']['runs']])
                                elif 'title' in vr and 'simpleText' in vr['title']:
                                    title = vr['title']['simpleText']
                                pub = ""
                                if 'publishedTimeText' in vr and 'simpleText' in vr['publishedTimeText']:
                                    pub = vr['publishedTimeText']['simpleText']
                                seen_ids.add(vid)
                                videos.append({
                                    'id': vid,
                                    'title': title,
                                    'link': f"https://www.youtube.com/watch?v={vid}",
                                    'meta': pub or "ล่าสุด",
                                    'description': ''
                                })
                        for v in node.values():
                            parse_item(v)
                    elif isinstance(node, list):
                        for item in node:
                            parse_item(item)
                            
                parse_item(data)
                
                # หากต้องการคลิปมากกว่าหน้าแรก ให้ดึงหน้าถัดไปผ่าน Innertube Continuation Token (สูงสุด 300 คลิป)
                fetch_pool_target = max(max_items, 300)
                if len(videos) < fetch_pool_target:
                    api_key_match = re.search(r'"INNERTUBE_API_KEY":"([a-zA-Z0-9_-]+)"', r.text)
                    if api_key_match:
                        api_key = api_key_match.group(1)
                        curr_token = extract_continuation_token(data)
                        attempts = 0
                        while curr_token and len(videos) < fetch_pool_target and attempts < 15:
                            attempts += 1
                            api_url = f"https://www.youtube.com/youtubei/v1/browse?key={api_key}"
                            payload = {
                                "context": {"client": {"clientName": "WEB", "clientVersion": "2.20240815.01.00", "hl": "th", "gl": "TH"}},
                                "continuation": curr_token
                            }
                            try:
                                r_cont = requests.post(api_url, json=payload, headers=HTTP_HEADERS, timeout=8)
                                if r_cont.status_code == 200:
                                    d_cont = r_cont.json()
                                    parse_item(d_cont)
                                    curr_token = extract_continuation_token(d_cont)
                                else:
                                    break
                            except Exception:
                                break
    except Exception:
        pass

    # 2. สำรองด้วย RSS Feed หากไม่ได้ผล
    if not videos and feed_url:
        try:
            feed = feedparser.parse(feed_url)
            for e in feed.entries:
                vid = getattr(e, 'yt_videoid', '')
                title = getattr(e, 'title', '')
                link = getattr(e, 'link', f"https://www.youtube.com/watch?v={vid}")
                pub = getattr(e, 'published', '')[:10]
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    videos.append({
                        'id': vid,
                        'title': title,
                        'link': link,
                        'meta': pub or "ล่าสุด",
                        'description': getattr(e, 'description', '')
                    })
        except Exception:
            pass

    # 3. จัดเรียงตามเงื่อนไขที่ผู้ใช้เลือกก่อนตัดตามจำนวน max_items
    if sort_by == "newest":
        videos = sorted(videos, key=get_recency_score)
    elif sort_by == "oldest":
        videos = sorted(videos, key=get_recency_score, reverse=True)
    # else original: keep as is
            
    return videos[:max_items]

def render_tech_hub_page():
    st.markdown("#### 📺 Tech & Media Intelligence Hub")
    tab1, tab2, tab3 = st.tabs(["🌐 เว็บไซต์ข่าว", "📋 YouTube Playlists", "🎥 YouTube Channels"])

    # --- TAB 1: เว็บไซต์ข่าว ---
    with tab1:
        selected_web = st.selectbox("เลือกเว็บข่าว:", WEB_SOURCES, format_func=lambda x: x[0], key="web_sel")
        if st.button("🚀 สแกนและดึงหัวข้อข่าวล่าสุด", key="web_btn"):
            with st.spinner(f"กำลังเชื่อมต่อและดึงหัวข้อข่าวสดจาก {selected_web[0]}..."):
                try:
                    r = requests.get(selected_web[1], headers=HTTP_HEADERS, timeout=10)
                    r.encoding = 'utf-8' if 'utf-8' in (r.encoding or '').lower() else (r.apparent_encoding or 'utf-8')
                    soup = BeautifulSoup(r.text, 'html.parser')
                    
                    articles = []
                    seen_txt = set()
                    
                    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                        txt = tag.get_text(separator=" ", strip=True)
                        if txt and len(txt) > 20 and len(txt) < 200 and txt not in seen_txt:
                            if not any(skip in txt.lower() for skip in ['cookie', 'privacy', 'policy', 'terms', 'ติดต่อเรา', 'เข้าสู่ระบบ', 'สมัครสมาชิก']):
                                seen_txt.add(txt)
                                articles.append(txt)
                    
                    if articles:
                        st.markdown(f"##### 📰 หัวข้อข่าวเด่นจาก {selected_web[0]}:")
                        for idx, art in enumerate(articles[:15]):
                            st.markdown(f"""
                                <div class="content-box" style="padding: 12px 16px; margin-bottom: 8px;">
                                    <b>#{idx+1}</b> <span style="font-size: 0.95rem; font-weight: 600; color: #0F172A;">{art}</span>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("ไม่พบรายการข่าวที่แยกแยะได้ชัดเจน หรือเว็บไซต์มีการป้องกันการเข้าถึง")
                    st.write("")
                    st.link_button("🌐 ไปที่เว็บต้นฉบับฉบับเต็ม", selected_web[1])
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

    # --- TAB 2: YouTube Playlists ---
    with tab2:
        selected_pl = st.selectbox("📋 เลือก Playlist:", PLAYLIST_SOURCES, format_func=lambda x: x[0], key="pl_sel")
        custom_pl_input = st.text_input("🔗 หรือใส่ URL Playlist เพิ่มเติม:", placeholder="https://www.youtube.com/playlist?list=...", key="custom_pl_input")

        # เลือก Playlist เป้าหมาย
        active_pl_target = custom_pl_input.strip() if custom_pl_input.strip() else selected_pl
        pl_display_name = active_pl_target[0] if isinstance(active_pl_target, (list, tuple)) else active_pl_target

        st.markdown("##### ⚙️ ตัวเลือกการจัดเรียงและจำนวนคลิปที่ต้องการดึง:")
        
        pl_fetch_criteria = st.radio(
            "🎯 เกณฑ์การเลือกคลิปจาก Playlist:",
            options=[
                "🆕 คลิปล่าสุดตามเวลาจริง (Newest First)",
                "📋 ตามลำดับต้นฉบับ Playlist (Original Order)",
                "⏳ คลิปเก่าสุด/แรกเริ่ม (Oldest First)"
            ],
            index=0,
            horizontal=True,
            key="pl_fetch_criteria_radio"
        )

        if "ล่าสุด" in pl_fetch_criteria:
            chosen_pl_sort = "newest"
        elif "เก่าสุด" in pl_fetch_criteria:
            chosen_pl_sort = "oldest"
        else:
            chosen_pl_sort = "original"
        
        # แถวปุ่มลัด 5 ปุ่ม (10, 30, 50, 100, 300 คลิป)
        pl_b_cols = st.columns(5)
        pl_quick_count = None
        
        with pl_b_cols[0]:
            if st.button("⚡ 10 คลิป", use_container_width=True, key="btn_pl_10"):
                pl_quick_count = 10
        with pl_b_cols[1]:
            if st.button("⚡ 30 คลิป", use_container_width=True, key="btn_pl_30"):
                pl_quick_count = 30
        with pl_b_cols[2]:
            if st.button("⚡ 50 คลิป", use_container_width=True, key="btn_pl_50"):
                pl_quick_count = 50
        with pl_b_cols[3]:
            if st.button("⚡ 100 คลิป", use_container_width=True, key="btn_pl_100"):
                pl_quick_count = 100
        with pl_b_cols[4]:
            if st.button("⚡ 300 คลิป", use_container_width=True, key="btn_pl_300"):
                pl_quick_count = 300

        # สไลเดอร์ระบุจำนวนคลิปเองแบบละเอียด (1 - 300 คลิป)
        pl_slider_col1, pl_slider_col2 = st.columns([2.6, 1.4])
        with pl_slider_col1:
            pl_slider_count = st.slider(
                "🎚️ หรือเลื่อนสไลเดอร์ระบุจำนวนเอง (1 - 300 คลิป):",
                min_value=1,
                max_value=300,
                value=30,
                step=1,
                key="pl_count_slider"
            )
        with pl_slider_col2:
            st.write("")
            pl_btn_custom = st.button("📥 ดึงตามสไลเดอร์", use_container_width=True, key="btn_pl_slider_fetch")

        # ตรวจสอบการเปลี่ยน Playlist หรือกดปุ่ม
        pl_cache_key = f"pl_cache_{pl_display_name}_{chosen_pl_sort}"
        final_pl_count_to_fetch = pl_quick_count if pl_quick_count is not None else (pl_slider_count if pl_btn_custom else None)

        if final_pl_count_to_fetch is not None or pl_cache_key not in st.session_state:
            fetch_cnt = final_pl_count_to_fetch or 20
            with st.spinner(f"กำลังเชื่อมต่อและดึง {fetch_cnt} คลิป จาก {pl_display_name}..."):
                st.session_state['pl_videos'] = fetch_youtube_playlist_videos(
                    active_pl_target, 
                    max_items=fetch_cnt, 
                    sort_by=chosen_pl_sort
                )
                st.session_state['pl_last_source'] = pl_display_name
                st.session_state[pl_cache_key] = st.session_state['pl_videos']
        else:
            st.session_state['pl_videos'] = st.session_state.get(pl_cache_key, [])

        if st.session_state.get('pl_videos'):
            st.markdown("---")
            pl_source_tag = st.session_state.get('pl_last_source', pl_display_name)
            st.caption(f"📁 รายการคลิปจาก Playlist: **{pl_source_tag}** (ทั้งหมด {len(st.session_state['pl_videos'])} คลิป)")
            
            pl_clip_dict = {}
            for idx, e in enumerate(st.session_state['pl_videos']):
                clean_title = e['title'].replace(" - YouTube", "").strip()
                time_label = extract_clean_time_label(e.get('meta', ''), clean_title)
                display_label = f"{idx+1}. [{time_label}] {clean_title}"
                pl_clip_dict[display_label] = e

            pl_choice = st.selectbox("🎯 เลือกคลิปที่ต้องการรับชม:", list(pl_clip_dict.keys()), key="pl_choice")
            
            selected_entry = pl_clip_dict[pl_choice]
            clean_title = selected_entry['title']
            video_url = normalize_youtube_url(selected_entry['link'], selected_entry)

            st.markdown(f"### 📺 {clean_title}")
            st.video(video_url)
            if selected_entry.get('meta'):
                st.caption(f"ℹ️ ข้อมูลคลิป: {selected_entry['meta']}")
            st.write("")
            st.link_button("▶️ ดูคลิปต้นฉบับบน YouTube", video_url)
        else:
            st.warning(f"⚠️ ไม่พบข้อมูลคลิปใน Playlist นี้ กรุณาลองใหม่อีกครั้ง")

    # --- TAB 3: YouTube Channels ---
    with tab3:
        # ตัวเลือกฟิลเตอร์หมวดหมู่ช่อง
        category_options = ["IT & Tech", "Anime & Movies", "Sports & Football", "🌟 ทั้งหมด (All Categories)"]
        ch_category = st.radio(
            "📂 เลือกหมวดหมู่คอนเทนต์:",
            options=category_options,
            index=0,
            horizontal=True,
            key="ch_category_radio"
        )
        
        # กรองรายชื่อช่องตามหมวดหมู่ที่เลือก
        if ch_category == "🌟 ทั้งหมด (All Categories)":
            filtered_channels = CHANNEL_SOURCES
        else:
            filtered_channels = [c for c in CHANNEL_SOURCES if len(c) > 3 and c[3] == ch_category]
            
        selected_ch = st.selectbox("📺 เลือกช่อง YouTube:", filtered_channels, format_func=lambda x: x[0], key="ch_sel")
        custom_ch_input = st.text_input("🔗 หรือใส่ URL ช่อง/วิดีโอ YouTube เพิ่มเติม:", placeholder="https://www.youtube.com/@ChannelName/videos", key="custom_ch_input")
        
        # ช่องเป้าหมาย
        active_ch_target = custom_ch_input.strip() if custom_ch_input.strip() else selected_ch
        ch_display_name = active_ch_target[0] if isinstance(active_ch_target, (list, tuple)) else active_ch_target

        st.markdown("##### ⚙️ ตัวเลือกการจัดเรียงและจำนวนคลิปที่ต้องการดึง:")
        
        ch_fetch_criteria = st.radio(
            "🎯 เกณฑ์การเลือกคลิปจากช่อง:",
            options=[
                "🆕 คลิปล่าสุดตามเวลาจริง (Newest First)",
                "📋 ตามลำดับฟีดช่อง (Default Feed)",
                "⏳ คลิปแรกเริ่ม/ย้อนหลัง (Oldest First)"
            ],
            index=0,
            horizontal=True,
            key="ch_fetch_criteria_radio"
        )

        if "ล่าสุด" in ch_fetch_criteria:
            chosen_ch_sort = "newest"
        elif "ย้อนหลัง" in ch_fetch_criteria:
            chosen_ch_sort = "oldest"
        else:
            chosen_ch_sort = "original"

        # แถวปุ่มลัด 5 ปุ่ม (10, 30, 50, 100, 300 คลิป)
        ch_b_cols = st.columns(5)
        ch_quick_count = None
        
        with ch_b_cols[0]:
            if st.button("⚡ 10 คลิป", use_container_width=True, key="btn_ch_10"):
                ch_quick_count = 10
        with ch_b_cols[1]:
            if st.button("⚡ 30 คลิป", use_container_width=True, key="btn_ch_30"):
                ch_quick_count = 30
        with ch_b_cols[2]:
            if st.button("⚡ 50 คลิป", use_container_width=True, key="btn_ch_50"):
                ch_quick_count = 50
        with ch_b_cols[3]:
            if st.button("⚡ 100 คลิป", use_container_width=True, key="btn_ch_100"):
                ch_quick_count = 100
        with ch_b_cols[4]:
            if st.button("⚡ 300 คลิป", use_container_width=True, key="btn_ch_300"):
                ch_quick_count = 300

        # สไลเดอร์ระบุจำนวนคลิปเองแบบละเอียด (1 - 300 คลิป)
        ch_slider_col1, ch_slider_col2 = st.columns([2.6, 1.4])
        with ch_slider_col1:
            ch_slider_count = st.slider(
                "🎚️ หรือเลื่อนสไลเดอร์ระบุจำนวนเอง (1 - 300 คลิป):",
                min_value=1,
                max_value=300,
                value=30,
                step=1,
                key="ch_count_slider"
            )
        with ch_slider_col2:
            st.write("")
            ch_btn_custom = st.button("📥 ดึงตามสไลเดอร์", use_container_width=True, key="btn_ch_slider_fetch")

        # ตรวจสอบการเปลี่ยนช่อง หรือกดปุ่ม
        ch_cache_key = f"ch_cache_{ch_display_name}_{chosen_ch_sort}"
        final_ch_count_to_fetch = ch_quick_count if ch_quick_count is not None else (ch_slider_count if ch_btn_custom else None)

        if final_ch_count_to_fetch is not None or ch_cache_key not in st.session_state:
            fetch_ch_cnt = final_ch_count_to_fetch or 20
            with st.spinner(f"กำลังเชื่อมต่อและดึง {fetch_ch_cnt} คลิป จาก {ch_display_name}..."):
                st.session_state['ch_videos'] = fetch_youtube_channel_videos(
                    active_ch_target, 
                    max_items=fetch_ch_cnt,
                    sort_by=chosen_ch_sort
                )
                st.session_state['ch_last_source'] = ch_display_name
                st.session_state[ch_cache_key] = st.session_state['ch_videos']
        else:
            st.session_state['ch_videos'] = st.session_state.get(ch_cache_key, [])

        if st.session_state.get('ch_videos'):
            st.markdown("---")
            ch_source_tag = st.session_state.get('ch_last_source', ch_display_name)
            st.caption(f"📁 รายการคลิปจากช่อง: **{ch_source_tag}** (ทั้งหมด {len(st.session_state['ch_videos'])} คลิป)")
            
            ch_clip_dict = {}
            for idx, e in enumerate(st.session_state['ch_videos']):
                clean_title = e['title'].replace(" - YouTube", "").strip()
                time_label = extract_clean_time_label(e.get('meta', ''), clean_title)
                display_label = f"{idx+1}. [{time_label}] {clean_title}"
                ch_clip_dict[display_label] = e

            ch_choice = st.selectbox("🎯 เลือกคลิปที่ต้องการรับชม:", list(ch_clip_dict.keys()), key="ch_choice")
            
            selected_entry = ch_clip_dict[ch_choice]
            clean_title = selected_entry['title']
            video_ch_url = normalize_youtube_url(selected_entry['link'], selected_entry)

            st.markdown(f"### 📺 {clean_title}")
            st.video(video_ch_url)
            if selected_entry.get('meta'):
                st.caption(f"ℹ️ ข้อมูลคลิป: {selected_entry['meta']}")
            st.write("")
            st.link_button("▶️ ดูคลิปต้นฉบับบน YouTube", video_ch_url)
        else:
            st.warning(f"⚠️ ไม่พบข้อมูลคลิปในช่องนี้ กรุณาลองใหม่อีกครั้ง")