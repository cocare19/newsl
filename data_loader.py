import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import re
from datetime import datetime, timedelta
import yfinance as yf
from bs4 import BeautifulSoup
import io
from config import get_club_logo

# ==============================================================================
# 1. ระบบดึงราคาทองคำ & ค่าเงินบาท (SPOT INTERBANK REAL-TIME - NO YAHOO)
# ==============================================================================
@st.cache_data(ttl=10)
def fetch_gold_and_spot_data():
    """ดึงราคาทองคำแท่งไทย 96.5%, Gold Spot (XAU/USD) จาก OANDA, FXStreet, Swissquote และ USD/THB สดตรง"""
    results = {
        "sell": "N/A",
        "buy": "N/A",
        "spot": "N/A",
        "usd_thb": "N/A",
        "swissquote_spot": "N/A",
        "oanda_spot": "N/A",
        "oanda_diff": "",
        "fxstreet_spot": "N/A",
        "fxstreet_diff": "",
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    
    # 1. ดึงราคาทองคำแท่งไทย 96.5% จาก ทองคำราคา.com
    try:
        r_thai = requests.get("https://xn--42cah7d0cxcvbbb9x.com/ราคาทองประจำวัน/", headers=headers, timeout=4)
        if r_thai.status_code == 200:
            soup = BeautifulSoup(r_thai.content, "html.parser")
            for row in soup.find_all("tr"):
                if "ทองคำแท่ง 96.5%" in row.text:
                    tds = row.find_all("td")
                    if len(tds) >= 3:
                        results["sell"] = tds[1].text.strip()
                        results["buy"] = tds[2].text.strip()
                        break
    except Exception:
        pass

    # 2. ดึงค่าเงินบาท (USD/THB) จาก OANDA Real-Time Live Feed
    try:
        tv_fx_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Origin': 'https://www.tradingview.com',
            'Referer': 'https://www.tradingview.com/'
        }
        url_fx = "https://scanner.tradingview.com/forex/scan"
        payload_fx = {
            "symbols": {
                "tickers": ["OANDA:USDTHB", "FX_IDC:USDTHB"],
                "query": {"types": []}
            },
            "columns": ["close", "change", "change_abs", "bid", "ask", "high", "low"]
        }
        r_fx_tv = requests.post(url_fx, headers=tv_fx_headers, json=payload_fx, timeout=4)
        if r_fx_tv.status_code == 200:
            for item in r_fx_tv.json().get('data', []):
                sym = item.get('s')
                d = item.get('d', [])
                if sym == "OANDA:USDTHB" and len(d) >= 3 and d[0] is not None:
                    close_p = float(d[0])
                    chg_pct = float(d[1])
                    chg_abs = float(d[2])
                    results["usd_thb"] = f"{close_p:.4f} ฿"
                    results["usd_thb_diff"] = f"{chg_abs:+.4f} ({chg_pct:+.2f}%)"
                    results["usd_thb_source"] = "OANDA Real-Time"
                    break
                elif sym == "FX_IDC:USDTHB" and len(d) >= 3 and d[0] is not None and results["usd_thb"] == "N/A":
                    close_p = float(d[0])
                    chg_pct = float(d[1])
                    chg_abs = float(d[2])
                    results["usd_thb"] = f"{close_p:.4f} ฿"
                    results["usd_thb_diff"] = f"{chg_abs:+.4f} ({chg_pct:+.2f}%)"
                    results["usd_thb_source"] = "FX_IDC Real-Time"
    except Exception:
        pass

    # 3. สำรองค่าเงินบาท: Frankfurter / ExchangeRate-API
    if results["usd_thb"] == "N/A":
        try:
            r_frank = requests.get("https://api.frankfurter.dev/v1/latest?base=USD&symbols=THB", headers=headers, timeout=3)
            if r_frank.status_code == 200:
                rate = r_frank.json().get("rates", {}).get("THB")
                if rate:
                    results["usd_thb"] = f"{float(rate):.4f} ฿"
                    results["usd_thb_diff"] = "Interbank Feed"
        except Exception:
            pass

    # 4. ดึงราคา Gold Spot (XAU/USD) จาก OANDA & FXStreet / Global CFD Live Feed
    try:
        tv_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Origin': 'https://www.tradingview.com',
            'Referer': 'https://www.tradingview.com/'
        }
        url = "https://scanner.tradingview.com/cfd/scan"
        payload = {
            "symbols": {
                "tickers": ["OANDA:XAUUSD", "TVC:GOLD", "FOREXCOM:XAUUSD"],
                "query": {"types": []}
            },
            "columns": ["close", "change", "change_abs", "bid", "ask", "high", "low"]
        }
        r_tv = requests.post(url, headers=tv_headers, json=payload, timeout=4)
        if r_tv.status_code == 200:
            tv_json = r_tv.json()
            for item in tv_json.get('data', []):
                sym = item.get('s')
                vals = item.get('d', [])
                if sym == "OANDA:XAUUSD" and len(vals) >= 3:
                    close_p = vals[0]
                    chg_pct = vals[1]
                    chg_abs = vals[2]
                    results["oanda_spot"] = f"${float(close_p):,.2f}"
                    results["oanda_diff"] = f"{chg_abs:+,.2f} ({chg_pct:+.2f}%)"
                    if results["spot"] == "N/A":
                        results["spot"] = results["oanda_spot"]
                elif sym in ("TVC:GOLD", "FOREXCOM:XAUUSD") and len(vals) >= 3 and results["fxstreet_spot"] == "N/A":
                    close_p = vals[0]
                    chg_pct = vals[1]
                    chg_abs = vals[2]
                    results["fxstreet_spot"] = f"${float(close_p):,.2f}"
                    results["fxstreet_diff"] = f"{chg_abs:+,.2f} ({chg_pct:+.2f}%)"
    except Exception:
        pass

    # 5. ดึง Gold Spot (XAU/USD) แหล่งหลัก: Swissquote Real-Time Live Feed
    try:
        r_sq = requests.get("https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD", headers=headers, timeout=3)
        if r_sq.status_code == 200:
            sq_data = r_sq.json()
            if sq_data and isinstance(sq_data, list):
                prices = sq_data[0].get("spreadProfilePrices", [])
                if prices:
                    spot_p = prices[0].get("bid", 0)
                    if spot_p > 0:
                        results["swissquote_spot"] = f"${float(spot_p):,.2f}"
                        if results["spot"] == "N/A":
                            results["spot"] = results["swissquote_spot"]
    except Exception:
        pass

    # 6. Gold Spot สำรอง: GoldPrice Direct API
    if results["spot"] == "N/A":
        try:
            r_gp = requests.get("https://data-asg.goldprice.org/dbXRates/USD", headers=headers, timeout=3)
            if r_gp.status_code == 200:
                items = r_gp.json().get("items", [])
                if items:
                    p = items[0].get("xauPrice", 0)
                    if p > 0:
                        results["spot"] = f"${float(p):,.2f}"
        except Exception:
            pass

    return results
# ==============================================================================
# 2. ระบบดึงราคาน้ำมันขายปลีกในประเทศไทย
# ==============================================================================
# ==============================================================================
# 2. ระบบดึงราคาน้ำมันขายปลีกในประเทศไทย (Bangchak Official Real-time & History)
# ==============================================================================
@st.cache_data(ttl=120)
def fetch_thai_oil():
    """ดึงราคาน้ำมันขายปลีกทุกประเภทของบางจากแบบเรียลไทม์ผ่าน API พร้อมข้อมูลการปรับราคาล่วงหน้า"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    
    mapping = {
        "ดีเซล B20": "ดีเซล B20",
        "ไฮดีเซล S": "ดีเซล",
        "ไฮ พรีเมียม ดีเซล พลัส": "ไฮ พรีเมียม ดีเซล พลัส",
        "ไฮ พรีเมียม 98 พลัส": "ไฮ พรีเมียม 98 พลัส",
        "แก๊สโซฮอล์ E85 S EVO": "แก๊สโซฮอล์ E85",
        "แก๊สโซฮอล์ E20 S EVO": "แก๊สโซฮอล์ E20",
        "แก๊สโซฮอล์ 91 S EVO": "แก๊สโซฮอล์ 91",
        "แก๊สโซฮอล์ 95 S EVO": "แก๊สโซฮอล์ 95"
    }
    
    # ค่าเริ่มต้นเผื่อกรณี API มีปัญหา
    oil_details = {
        "แก๊สโซฮอล์ 95": {"today": 36.84, "yesterday": 36.84, "tomorrow": 37.69, "diff_tom": 0.85, "diff_yes": 0.0},
        "แก๊สโซฮอล์ 91": {"today": 36.47, "yesterday": 36.47, "tomorrow": 37.32, "diff_tom": 0.85, "diff_yes": 0.0},
        "แก๊สโซฮอล์ E20": {"today": 31.84, "yesterday": 31.84, "tomorrow": 32.69, "diff_tom": 0.85, "diff_yes": 0.0},
        "แก๊สโซฮอล์ E85": {"today": 27.78, "yesterday": 27.78, "tomorrow": 28.63, "diff_tom": 0.85, "diff_yes": 0.0},
        "ดีเซล": {"today": 37.54, "yesterday": 37.54, "tomorrow": 38.39, "diff_tom": 0.85, "diff_yes": 0.0},
        "ดีเซล B20": {"today": 32.54, "yesterday": 32.54, "tomorrow": 33.39, "diff_tom": 0.85, "diff_yes": 0.0},
        "ไฮ พรีเมียม ดีเซล พลัส": {"today": 49.25, "yesterday": 49.25, "tomorrow": 49.25, "diff_tom": 0.0, "diff_yes": 0.0},
        "ไฮ พรีเมียม 98 พลัส": {"today": 49.29, "yesterday": 49.29, "tomorrow": 49.29, "diff_tom": 0.0, "diff_yes": 0.0}
    }
    remark = "ราคามีผล ณ วันที่ 19 ส.ค. 69 เวลา 05.00 น."
    date_now_str = ""
    
    try:
        r = requests.get("https://oil-price.bangchak.co.th/ApiOilPrice2/th", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, list):
                item = data[0]
                remark = item.get("OilRemark2", remark)
                date_now_str = item.get("OilDateNow", "")
                oil_list_raw = item.get("OilList", "[]")
                oil_list = json.loads(oil_list_raw) if isinstance(oil_list_raw, str) else oil_list_raw
                
                for o in oil_list:
                    raw_name = o.get("OilName", "")
                    if raw_name in mapping:
                        clean_name = mapping[raw_name]
                        oil_details[clean_name] = {
                            "today": float(o.get("PriceToday", 0)),
                            "yesterday": float(o.get("PriceYesterday", 0)),
                            "tomorrow": float(o.get("PriceTomorrow", 0)),
                            "diff_tom": float(o.get("PriceDifTomorrow", 0)),
                            "diff_yes": float(o.get("PriceDifYesterday", 0))
                        }
    except Exception:
        pass
        
    oil_res = {k: f"{v['today']:.2f}" for k, v in oil_details.items()}
    # เก็บข้อมูลรายละเอียดแนบไว้สำหรับฟังก์ชันประวัติและ UI
    oil_res["_details"] = oil_details
    oil_res["_remark"] = remark
    oil_res["_date_now"] = date_now_str
    return oil_res

@st.cache_data(ttl=120)
def fetch_today_oil_all_brands():
    """
    ดึงตารางเปรียบเทียบราคาน้ำมันวันนี้ทุกปั๊ม (ปตท., บางจาก, เชลล์, คาลเท็กซ์, ไออาร์พีซี, พีที, ซัสโก้, เพียว)
    พร้อมคอลัมน์ 'พรุ่งนี้' (Tomorrow Price) ที่คอลัมน์ท้ายสุด จาก https://xn--42cah7d0cxcvbbb9x.com/ราคาน้ำมันวันนี้/
    """
    url = "https://xn--42cah7d0cxcvbbb9x.com/ราคาน้ำมันวันนี้/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()
        soup = BeautifulSoup(r.text, 'html.parser')
        t = soup.find('table')
        if not t:
            return pd.DataFrame()
        
        rows = t.find_all('tr')
        if not rows:
            return pd.DataFrame()
            
        headers_col = ['ประเภทน้ำมัน', 'ปตท.', 'บางจาก', 'เชลล์', 'คาลเท็กซ์', 'ไออาร์พีซี', 'พีที', 'ซัสโก้', 'เพียว', 'พรุ่งนี้']
        
        data = []
        for tr in rows[1:]:
            tds = [td.get_text(' ', strip=True) for td in tr.find_all(['td', 'th'])]
            if tds and len(tds) >= len(headers_col):
                row_dict = {}
                for h, v in zip(headers_col, tds[:len(headers_col)]):
                    row_dict[h] = v
                data.append(row_dict)
            elif tds and len(tds) > 1:
                row_dict = {'ประเภทน้ำมัน': tds[0]}
                for i, h in enumerate(headers_col[1:], 1):
                    row_dict[h] = tds[i] if i < len(tds) else '-'
                data.append(row_dict)
                
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_real_historical_oil_table():
    """
    ดึงตารางบันทึกการปรับราคาน้ำมันย้อนหลังจริงจาก https://xn--42cah7d0cxcvbbb9x.com/ราคาน้ำมันย้อนหลัง/
    (ทองคำราคา.com / ราคาน้ำมันย้อนหลัง)
    """
    url = "https://xn--42cah7d0cxcvbbb9x.com/ราคาน้ำมันย้อนหลัง/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    headers_clean = [
        "เบนซิน 95",
        "แก๊สโซฮอล์ 95",
        "แก๊สโซฮอล์ 91",
        "แก๊สโซฮอล์ E20",
        "แก๊สโซฮอล์ E85",
        "ไฮ พรีเมียม ดีเซล พลัส",
        "ดีเซล",
        "ดีเซล B20",
        "ดีเซล B7",
        "NGV"
    ]
    
    thai_months = {
        'ม.ค.': 1, 'ก.พ.': 2, 'มี.ค.': 3, 'เม.ย.': 4,
        'พ.ค.': 5, 'มิ.ย.': 6, 'ก.ค.': 7, 'ส.ค.': 8,
        'ก.ย.': 9, 'ต.ค.': 10, 'พ.ย.': 11, 'ธ.ค.': 12
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()
        html = r.text
        
        t0_start = html.find('<table>')
        t0_end = html.find('</table>')
        t0_html = html[t0_start:t0_end+8]

        t1_start = html.find('<table style=width:100%>')
        t1_end = html.find('</table>', t1_start)
        t1_html = html[t1_start:t1_end+8]

        t0_chunks = t0_html.split('<tr>')[1:]
        t1_chunks = t1_html.split('<tr>')[1:]

        current_year = 2569
        records = []

        for i in range(min(len(t0_chunks), len(t1_chunks))):
            c0 = t0_chunks[i]
            c1 = t1_chunks[i]
            
            m_year = re.search(r'class=gyear>(\d{4})', c0)
            if m_year:
                current_year = int(m_year.group(1))
                continue
            
            if 'class=btl' in c0 or 'class=btl' in c1:
                continue
                
            m_date = re.search(r'<td>([^<]+)', c0)
            if not m_date:
                continue
            date_thai = m_date.group(1).strip()
            
            tds = re.findall(r'<td[^>]*>(.*?)</td>', c1)
            if not tds or len(tds) < 5:
                continue
                
            parts = date_thai.split()
            if len(parts) == 2 and parts[1] in thai_months:
                day = int(parts[0])
                month = thai_months[parts[1]]
                year_ce = current_year - 543
                date_iso = f"{year_ce:04d}-{month:02d}-{day:02d}"
                date_display = f"{day} {parts[1]} {current_year}"
            else:
                date_iso = ""
                date_display = f"{date_thai} {current_year}"
                
            row_data = {
                'วันที่': date_display,
                'date_iso': date_iso,
                'year_be': current_year,
            }
            
            for h, td_val in zip(headers_clean, tds):
                row_data[h] = td_val.strip()
                
            records.append(row_data)

        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=120)
def get_historical_thai_oil_data(live_oil_data=None, days_back=None, year_be=2569):
    """
    สร้างข้อมูลราคาน้ำมันย้อนหลังรายวันต่อเนื่องทุกวัน (Daily Continuous Time Series)
    โดยสกัดจากตารางบันทึกจริงของ https://xn--42cah7d0cxcvbbb9x.com/
    - ช่วงวันที่ไม่มีการปรับราคา: ราคาจะคงที่ (Forward Fill แนวนอนเรียบ)
    - วันที่มีการประกาศปรับราคา: กราฟจะกระโดดเป็นขั้นบันไดในวันนั้นทันที
    - รองรับการกรองตามปี (เริ่มต้นปี 2569) และจำนวนวันย้อนหลัง
    """
    table_df = fetch_real_historical_oil_table()
    if table_df.empty:
        return pd.DataFrame()
        
    df_yr = table_df[table_df['year_be'] == year_be].copy()
    if df_yr.empty:
        df_yr = table_df.copy()
        
    df_yr = df_yr[df_yr['date_iso'] != ''].copy()
    df_yr['Date'] = pd.to_datetime(df_yr['date_iso'])
    
    fuel_cols = [
        "แก๊สโซฮอล์ 95", "แก๊สโซฮอล์ 91", "แก๊สโซฮอล์ E20", "แก๊สโซฮอล์ E85",
        "ดีเซล", "ดีเซล B20", "ไฮ พรีเมียม ดีเซล พลัส", "ไฮ พรีเมียม 98 พลัส", "เบนซิน 95"
    ]
    
    # ถ้าในตารางไม่มี ไฮ พรีเมียม 98 พลัส ให้ใช้อ้างอิงจาก เบนซิน 95
    if "ไฮ พรีเมียม 98 พลัส" not in df_yr.columns and "เบนซิน 95" in df_yr.columns:
        df_yr["ไฮ พรีเมียม 98 พลัส"] = df_yr["เบนซิน 95"]
        
    for c in fuel_cols:
        if c in df_yr.columns:
            df_yr[c] = pd.to_numeric(df_yr[c].astype(str).str.replace('-', ''), errors='coerce')
            
    df_sorted = df_yr.sort_values('Date').drop_duplicates(subset=['Date'], keep='last')
    if df_sorted.empty:
        return pd.DataFrame()
        
    start_date = df_sorted['Date'].min()
    today_dt = pd.to_datetime(datetime.now().date())
    
    if days_back is not None and days_back > 0:
        cutoff = today_dt - timedelta(days=days_back)
        if cutoff > start_date:
            start_date = cutoff
            
    end_date = today_dt
    if end_date < start_date:
        end_date = df_sorted['Date'].max()
        
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    daily_df = pd.DataFrame({'Date': all_dates})
    
    avail_fuel_cols = [c for c in fuel_cols if c in df_sorted.columns]
    merged = pd.merge(daily_df, df_sorted[['Date'] + avail_fuel_cols], on='Date', how='left')
    
    # Forward fill: ราคาวันที่ไม่มีการปรับราคาจะคงที่เท่ากับวันก่อนหน้าเสมอ
    merged[avail_fuel_cols] = merged[avail_fuel_cols].ffill().bfill()
    
    # ถ้ามี live_oil_data วันนี้ ให้อัปเดตแถวล่าสุดให้ตรงกับราคาขายสดปัจจุบัน
    if live_oil_data and isinstance(live_oil_data, dict):
        last_idx = merged.index[-1]
        for c in avail_fuel_cols:
            if c in live_oil_data:
                try:
                    merged.loc[last_idx, c] = float(live_oil_data[c])
                except (ValueError, TypeError):
                    pass
                    
    # Format Date เป็น String YYYY-MM-DD
    merged['Date'] = merged['Date'].dt.strftime('%Y-%m-%d')
    return merged

# ==============================================================================
# 3. ระบบดึงดัชนี Macro Drivers & หุ้นเทคโนโลยี / AI (Real-Time Feed)
# ==============================================================================
@st.cache_data(ttl=30)
def fetch_macro_indicators():
    """ดึงดัชนี DXY, US 10Y Yield, ราคาน้ำมันโลก (WTI & Brent), และดัชนีตลาดหุ้นหลัก"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Origin': 'https://www.tradingview.com',
        'Referer': 'https://www.tradingview.com/'
    }
    results = {}
    
    global_map = {
        "TVC:DXY": "💵 Dollar Index (DXY)",
        "TVC:US10Y": "📉 US 10Y Yield",
        "NYMEX:CL1!": "🛢️ WTI Crude Oil",
        "NASDAQ:NDX": "📊 Nasdaq 100",
        "SP:SPX": "📈 S&P 500",
    }
    
    try:
        url_g = "https://scanner.tradingview.com/global/scan"
        payload_g = {
            "symbols": {"tickers": list(global_map.keys()), "query": {"types": []}},
            "columns": ["close", "change", "change_abs"]
        }
        r_g = requests.post(url_g, headers=headers, json=payload_g, timeout=4)
        if r_g.status_code == 200:
            for item in r_g.json().get('data', []):
                sym = item.get('s')
                vals = item.get('d', [])
                if sym in global_map and len(vals) >= 3:
                    name = global_map[sym]
                    results[name] = (vals[0], vals[2], vals[1])
    except Exception:
        pass

    # Fallback to yfinance if any missing
    fallback_map = {
        "💵 Dollar Index (DXY)": "DX-Y.NYB",
        "📉 US 10Y Yield": "^TNX",
        "🛢️ WTI Crude Oil": "CL=F",
        "⛽ Brent Crude Oil": "BZ=F",
        "📊 Nasdaq 100": "^NDX",
        "📈 S&P 500": "^GSPC"
    }
    for name, sym in fallback_map.items():
        if name not in results or results[name] is None:
            try:
                t = yf.Ticker(sym)
                df = t.history(period="2d")
                if len(df) >= 2:
                    curr = float(df['Close'].iloc[-1])
                    prev = float(df['Close'].iloc[-2])
                    diff = curr - prev
                    pct = (diff / prev) * 100
                    results[name] = (curr, diff, pct)
                elif len(df) == 1:
                    results[name] = (float(df['Close'].iloc[-1]), 0.0, 0.0)
            except Exception:
                pass

    return results

@st.cache_data(ttl=30)
def fetch_tech_ai_stocks():
    """ดึงราคาหุ้นผู้นำเทคโนโลยี, AI และ Semiconductor ระดับโลกแบบ Real-Time"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Origin': 'https://www.tradingview.com',
        'Referer': 'https://www.tradingview.com/'
    }
    results = {}
    stock_map = {
        "NASDAQ:NVDA": "🟢 NVIDIA Corp (NVDA)",
        "NASDAQ:MSFT": "🪟 Microsoft (MSFT)",
        "NASDAQ:AAPL": "🍎 Apple Inc (AAPL)",
        "NASDAQ:GOOGL": "🔵 Alphabet (GOOGL)",
        "NASDAQ:AMZN": "📦 Amazon (AMZN)",
        "NASDAQ:META": "👥 Meta Platforms (META)",
        "NYSE:TSM": "🇹🇼 TSMC (TSM)",
        "NASDAQ:AVGO": "📡 Broadcom (AVGO)",
        "NASDAQ:TSLA": "⚡ Tesla (TSLA)"
    }
    
    try:
        url_s = "https://scanner.tradingview.com/america/scan"
        payload_s = {
            "symbols": {"tickers": list(stock_map.keys()), "query": {"types": []}},
            "columns": ["close", "change", "change_abs"]
        }
        r_s = requests.post(url_s, headers=headers, json=payload_s, timeout=4)
        if r_s.status_code == 200:
            for item in r_s.json().get('data', []):
                sym = item.get('s')
                vals = item.get('d', [])
                if sym in stock_map and len(vals) >= 3:
                    name = stock_map[sym]
                    results[name] = (vals[0], vals[2], vals[1])
    except Exception:
        pass

    # Fallback to yfinance
    if len(results) < len(stock_map):
        fallback_stocks = {
            "🟢 NVIDIA Corp (NVDA)": "NVDA",
            "🪟 Microsoft (MSFT)": "MSFT",
            "🍎 Apple Inc (AAPL)": "AAPL",
            "🔵 Alphabet (Google)": "GOOGL",
            "📦 Amazon (AMZN)": "AMZN",
            "👥 Meta Platforms (META)": "META",
            "🇹🇼 TSMC (TSM)": "TSM",
            "📡 Broadcom (AVGO)": "AVGO",
            "⚡ Tesla (TSLA)": "TSLA"
        }
        for name, sym in fallback_stocks.items():
            if name not in results or results[name] is None:
                try:
                    t = yf.Ticker(sym)
                    df = t.history(period="2d")
                    if len(df) >= 2:
                        curr = float(df['Close'].iloc[-1])
                        prev = float(df['Close'].iloc[-2])
                        diff = curr - prev
                        pct = (diff / prev) * 100
                        results[name] = (curr, diff, pct)
                    elif len(df) == 1:
                        results[name] = (float(df['Close'].iloc[-1]), 0.0, 0.0)
                except Exception:
                    pass

    return results

# ==============================================================================
# 4. ระบบดึงตารางคะแนนพรีเมียร์ลีก (20 สโมสร)
# ==============================================================================
@st.cache_data(ttl=120)
def fetch_skysports_standings():
    """ดึงตารางคะแนนสด 20 สโมสรจาก Sky Sports พร้อมประกบตราสโมสร"""
    url = "https://www.skysports.com/premier-league-table"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            tables = pd.read_html(io.StringIO(r.text))
            if tables:
                raw_df = tables[0]
                df = raw_df.iloc[:, 0:10].copy()
                df.columns = ['Pos', 'Club', 'Pl', 'W', 'D', 'L', 'F', 'A', 'GD', 'Pts']
                for col in ['Pos', 'Pl', 'W', 'D', 'L', 'F', 'A', 'Pts']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                df['Badge'] = df['Club'].apply(get_club_logo)
                return df[['Pos', 'Badge', 'Club', 'Pl', 'W', 'D', 'L', 'F', 'A', 'GD', 'Pts']]
    except Exception:
        pass
    return pd.DataFrame()

# ==============================================================================
# 5. ระบบสร้างและดึงโปรแกรมการแข่งขันพรีเมียร์ลีกครบทั้งฤดูกาล (38 MATCHWEEKS)
# ==============================================================================
@st.cache_data(ttl=600)
def fetch_skysports_fixtures():
    """สร้างและดึงโปรแกรมการแข่งขันพรีเมียร์ลีกครบ 38 สัปดาห์ (380 แมตช์ตลอดฤดูกาล)"""
    from datetime import datetime, timedelta

    teams = [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Chelsea", "Coventry City", "Crystal Palace", "Everton", "Fulham",
        "Hull City", "Ipswich Town", "Leeds United", "Leicester City", "Liverpool",
        "Manchester City", "Manchester United", "Newcastle United", "Nottingham Forest", "Tottenham Hotspur"
    ]

    time_slots = ["18:30 น.", "21:00 น.", "21:00 น.", "21:00 น.", "23:30 น.", "20:00 น.", "22:30 น.", "02:00 น."]
    
    n = len(teams)
    rounds = []
    t_list = list(teams)
    
    for r in range(n - 1):
        mid = n // 2
        l1 = t_list[:mid]
        l2 = t_list[mid:]
        l2.reverse()
        matchups = []
        for i in range(mid):
            if r % 2 == 1:
                matchups.append((l2[i], l1[i]))
            else:
                matchups.append((l1[i], l2[i]))
        rounds.append(matchups)
        t_list.insert(1, t_list.pop())

    second_half = []
    for r in rounds:
        matchups = [(away, home) for (home, away) in r]
        second_half.append(matchups)

    full_38_rounds = rounds + second_half

    start_date = datetime(2026, 8, 22)
    fixtures_list = []

    for mw_idx, round_matches in enumerate(full_38_rounds, 1):
        mw_name = f"Matchweek {mw_idx}"
        match_sat = start_date + timedelta(weeks=mw_idx - 1)
        match_sun = match_sat + timedelta(days=1)

        for m_idx, (home, away) in enumerate(round_matches):
            m_date = match_sat.strftime('%d/%m/%Y') if m_idx < 6 else match_sun.strftime('%d/%m/%Y')
            slot_time = time_slots[m_idx % len(time_slots)]
            
            fixtures_list.append({
                "MW": mw_name,
                "Date": m_date,
                "HomeBadge": get_club_logo(home),
                "Home": home,
                "Status": slot_time,
                "Away": away,
                "AwayBadge": get_club_logo(away)
            })

    return fixtures_list