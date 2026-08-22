from google import genai
from google.genai import types
from config import load_api_keys

API_KEYS_POOL = load_api_keys()

def smart_gemini_generate(prompt_text, task_level="lite", enable_search=False):
    """
    ประมวลผล Gemini AI อัจฉริยะ:
    - สลับคีย์อัตโนมัติเมื่อคีย์ใดคีย์หนึ่งติด Rate Limit
    - จัดระดับ Model ตามความลึกของงาน (lite vs deep)
    """
    if not API_KEYS_POOL:
        return "⚠️ ไม่พบ API Key ใน secrets.toml", "No Key"

    total_keys = len(API_KEYS_POOL)
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    ) if enable_search else None

    for idx, current_key in enumerate(API_KEYS_POOL):
        key_num = idx + 1
        masked_key = f"...{current_key[-4:]}"

        if idx == 0 and task_level == "deep":
            models_to_test = ["gemini-3.7-flash", "gemini-3.5-flash-lite"]
        elif task_level == "lite":
            models_to_test = ["gemini-3.5-flash-lite", "gemini-3.7-flash"]
        else:
            models_to_test = ["gemini-3.7-flash", "gemini-3.5-flash-lite"]

        for m_name in models_to_test:
            try:
                client = genai.Client(api_key=current_key)
                res = client.models.generate_content(
                    model=m_name,
                    contents=prompt_text,
                    config=config
                )
                if res and res.text:
                    prefix = "👑 Pro" if idx == 0 else "⚡ Pool"
                    return res.text, f"{prefix} {m_name} (Key #{key_num}: {masked_key})"
            except Exception:
                continue

    return f"⚠️ ติด Limit/Error หมดทุกคีย์ (ทดสอบครบทั้ง {total_keys}/{total_keys} Keys แล้ว)", "All Keys Exhausted"