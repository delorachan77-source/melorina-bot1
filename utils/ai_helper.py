import aiohttp
import json
import fitz  # PyMuPDF
from PIL import Image
import io
from config import GEMINI_API_KEY

# ========================================
# ===== ارسال به جیمینای =====
# ========================================
async def call_gemini(prompt):
    """ارسال درخواست به جیمینای"""
    if not GEMINI_API_KEY:
        return "❌ کلید جیمینای تنظیم نشده!"
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                else:
                    error = await response.text()
                    print(f"❌ خطا: {response.status} - {error}")
                    return None
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# ========================================
# ===== مترجم =====
# ========================================
async def translate_text(text, target_lang="fa"):
    """ترجمه متن با جیمینای"""
    prompt = f"متن زیر را به {target_lang} ترجمه کن:\n\n{text}"
    return await call_gemini(prompt)

# ========================================
# ===== خلاصه‌سازی =====
# ========================================
async def summarize_text(text):
    """خلاصه‌سازی متن با جیمینای"""
    prompt = f"خلاصه زیر رو به فارسی بنویس (حداکثر ۱۰ خط):\n\n{text[:5000]}"
    return await call_gemini(prompt)

# ========================================
# ===== تحلیل کتاب =====
# ========================================
async def analyze_book(text):
    """تحلیل کتاب با جیمینای"""
    prompt = f"""
    کتاب زیر را تحلیل کن:
    ۱. شخصیت‌های اصلی
    ۲. تم‌های اصلی
    ۳. سبک نوشتاری
    ۴. نکات کلیدی
    
    متن:
    {text[:5000]}
    """
    return await call_gemini(prompt)

# ========================================
# ===== استخراج متن از فایل =====
# ========================================
async def extract_text_from_file(file_path):
    """استخراج متن از PDF"""
    try:
        if file_path.endswith(".pdf"):
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        return None
    except Exception as e:
        print(f"❌ خطا در استخراج متن: {e}")
        return None
