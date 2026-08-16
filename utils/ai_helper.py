import aiohttp
import json
import fitz  # PyMuPDF
import asyncio
from config import GEMINI_API_KEY

# ========================================
# ========================================
# ===== ارسال به جیمینای =====
# ========================================
# ========================================

async def call_gemini(prompt):
    """ارسال درخواست به جیمینای"""
    if not GEMINI_API_KEY:
        return "❌ کلید جیمینای تنظیم نشده! لطفاً GEMINI_API_KEY رو توی .env تنظیم کن."
    
    try:
        # ===== استفاده از مدل gemini-pro (پایدارترین) =====
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {"Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if result:
                        return result
                    else:
                        return "❌ جیمینای پاسخی برنگرداند!"
                else:
                    error_text = await response.text()
                    print(f"❌ خطای جیمینای: {response.status} - {error_text}")
                    
                    if response.status == 403:
                        return "❌ کلید جیمینای نامعتبر است! لطفاً کلید جدید از https://aistudio.google.com/ بگیر."
                    elif response.status == 404:
                        return "❌ مدل جیمینای پیدا نشد! لطفاً کلید خود را بررسی کن."
                    elif response.status == 429:
                        return "❌ تعداد درخواست‌ها زیاد شده! چند دقیقه دیگه امتحان کن."
                    else:
                        return f"❌ خطای جیمینای: {response.status}"
    except asyncio.TimeoutError:
        return "❌ زمان درخواست به جیمینای تمام شد! دوباره تلاش کن."
    except aiohttp.ClientError as e:
        return f"❌ خطای اتصال به جیمینای: {str(e)[:100]}"
    except Exception as e:
        print(f"❌ خطا: {e}")
        return f"❌ خطای داخلی: {str(e)[:100]}"

# ========================================
# ========================================
# ===== مترجم =====
# ========================================
# ========================================

async def translate_text(text, target_lang="fa"):
    """ترجمه متن با جیمینای"""
    if not text or len(text.strip()) < 2:
        return "❌ متن کافی برای ترجمه وجود ندارد!"
    
    lang_name = "فارسی" if target_lang == "fa" else "انگلیسی"
    prompt = f"متن زیر را به {lang_name} ترجمه کن. ترجمه روان و طبیعی باشد:\n\n{text}"
    return await call_gemini(prompt)

# ========================================
# ========================================
# ===== خلاصه‌سازی =====
# ========================================
# ========================================

async def summarize_text(text):
    """خلاصه‌سازی متن با جیمینای"""
    if not text or len(text.strip()) < 50:
        return "❌ متن کافی برای خلاصه‌سازی وجود ندارد! حداقل ۵۰ کاراکتر نیاز است."
    
    if len(text) > 5000:
        text = text[:5000] + "..."
    
    prompt = f"خلاصه زیر رو به فارسی بنویس (حداکثر ۱۰ خط، نکات کلیدی رو پوشش بده):\n\n{text}"
    return await call_gemini(prompt)

# ========================================
# ========================================
# ===== تحلیل کتاب =====
# ========================================
# ========================================

async def analyze_book(text):
    """تحلیل کتاب با جیمینای"""
    if not text or len(text.strip()) < 100:
        return "❌ متن کافی برای تحلیل وجود ندارد! حداقل ۱۰۰ کاراکتر نیاز است."
    
    if len(text) > 5000:
        text = text[:5000] + "..."
    
    prompt = f"""
    کتاب زیر را به زبان فارسی تحلیل کن:
    
    ۱. شخصیت‌های اصلی (نام و نقش)
    ۲. تم‌های اصلی (موضوعات کلیدی)
    ۳. سبک نوشتاری (روایت، زبان)
    ۴. نکات کلیدی (پیام‌های مهم)
    ۵. جمع‌بندی نهایی
    
    متن کتاب:
    {text}
    """
    return await call_gemini(prompt)

# ========================================
# ========================================
# ===== استخراج متن از فایل =====
# ========================================
# ========================================

async def extract_text_from_file(file_path):
    """استخراج متن از فایل PDF"""
    try:
        if not file_path:
            return None
        
        if file_path.endswith(".pdf"):
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            
            if text.strip():
                return text
            else:
                return "⚠️ فایل PDF متنی ندارد (ممکن است اسکن شده باشد)."
        else:
            return None
    except Exception as e:
        print(f"❌ خطا در استخراج متن: {e}")
        return None

# ========================================
# ========================================
# ===== تست اتصال جیمینای =====
# ========================================
# ========================================

async def test_gemini_connection():
    """تست اتصال به جیمینای"""
    if not GEMINI_API_KEY:
        return "❌ کلید جیمینای تنظیم نشده!"
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": "سلام"}]
            }]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    return "✅ اتصال به جیمینای برقرار است!"
                else:
                    return f"❌ خطا در اتصال: {response.status}"
    except Exception as e:
        return f"❌ خطا: {str(e)[:100]}"

print("✅ توابع جیمینای بارگذاری شدند!")
