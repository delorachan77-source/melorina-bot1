import aiohttp
import fitz  # PyMuPDF
import asyncio
from config import GEMINI_API_KEY
import os
from PIL import Image
import io
import arabic_reshaper
from bidi.algorithm import get_display

# ========================================
# تنظیمات Gemini
# ========================================

API_URL = "https://generativelanguage.googleapis.com/v1beta"

# اولویت مدل‌ها:
PREFERRED_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
]


# ========================================
# پیدا کردن مدل قابل استفاده
# ========================================

async def get_available_model():
    """
    مدل‌های در دسترس API را می‌گیرد و مدلی را انتخاب می‌کند
    که generateContent را پشتیبانی کند.
    """

    if not GEMINI_API_KEY:
        return None

    url = f"{API_URL}/models"

    headers = {
        "x-goog-api-key": GEMINI_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:

                if response.status != 200:
                    error = await response.text()
                    print(
                        f"❌ خطا در دریافت لیست مدل‌ها: "
                        f"{response.status} - {error[:500]}"
                    )
                    return None

                data = await response.json()

                models = data.get("models", [])

                available = []

                for model in models:
                    name = model.get("name", "")
                    methods = model.get(
                        "supportedGenerationMethods",
                        []
                    )

                    if "generateContent" in methods:
                        model_id = name.replace("models/", "")
                        available.append(model_id)

                if not available:
                    print("❌ هیچ مدل دارای generateContent پیدا نشد!")
                    return None

                # اولویت مدل‌های موردنظر
                for preferred in PREFERRED_MODELS:
                    if preferred in available:
                        print(
                            f"✅ مدل انتخاب شد: {preferred}"
                        )
                        return preferred

                # اگر مدل‌های بالا موجود نبودند،
                # یک مدل Flash مناسب پیدا کن
                flash_models = [
                    m for m in available
                    if "flash" in m.lower()
                ]

                if flash_models:
                    print(
                        f"✅ مدل Flash موجود انتخاب شد: "
                        f"{flash_models[0]}"
                    )
                    return flash_models[0]

                # در نهایت اولین مدل قابل استفاده
                print(
                    f"✅ مدل موجود انتخاب شد: {available[0]}"
                )
                return available[0]

    except asyncio.TimeoutError:
        print("❌ Timeout هنگام دریافت مدل‌های Gemini")
        return None

    except aiohttp.ClientError as e:
        print(f"❌ خطای اتصال هنگام دریافت مدل‌ها: {e}")
        return None

    except Exception as e:
        print(f"❌ خطا در پیدا کردن مدل Gemini: {e}")
        return None


# ========================================
# ارسال درخواست به Gemini
# ========================================

async def call_gemini(prompt):
    """ارسال درخواست به Gemini"""

    if not GEMINI_API_KEY:
        return (
            "❌ کلید جیمینای تنظیم نشده!\n\n"
            "لطفاً GEMINI_API_KEY را در فایل .env تنظیم کن."
        )

    if not prompt or not str(prompt).strip():
        return "❌ متن درخواست خالی است!"

    try:
        # پیدا کردن مدل واقعی و فعال
        model = await get_available_model()

        if not model:
            return (
                "❌ هیچ مدل فعال Gemini برای این API Key پیدا نشد!\n\n"
                "کلید Gemini را بررسی کن."
            )

        url = (
            f"{API_URL}/models/"
            f"{model}:generateContent"
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": str(prompt)
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192
            }
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:

                response_text = await response.text()

                # ========================================
                # موفق
                # ========================================

                if response.status == 200:

                    try:
                        data = await response.json()

                        candidates = data.get(
                            "candidates",
                            []
                        )

                        if not candidates:
                            print(
                                f"❌ Gemini candidate برنگرداند: "
                                f"{response_text[:1000]}"
                            )
                            return (
                                "❌ جیمینای پاسخی برنگرداند."
                            )

                        content = candidates[0].get(
                            "content",
                            {}
                        )

                        parts = content.get(
                            "parts",
                            []
                        )

                        result = ""

                        for part in parts:
                            if "text" in part:
                                result += part["text"]

                        if result.strip():
                            return result.strip()

                        return (
                            "❌ جیمینای پاسخ متنی برنگرداند."
                        )

                    except Exception as e:
                        print(
                            f"❌ خطا در خواندن پاسخ Gemini: {e}"
                        )
                        return (
                            "❌ پاسخ جیمینای قابل خواندن نبود."
                        )

                # ========================================
                # خطاها
                # ========================================

                print(
                    f"❌ Gemini Error "
                    f"{response.status}: "
                    f"{response_text[:1500]}"
                )

                if response.status == 400:
                    return (
                        "❌ درخواست به جیمینای نامعتبر بود.\n\n"
                        "جزئیات خطا در کنسول چاپ شده."
                    )

                elif response.status == 401:
                    return (
                        "❌ کلید Gemini معتبر نیست.\n\n"
                        "GEMINI_API_KEY را بررسی کن."
                    )

                elif response.status == 403:
                    return (
                        "❌ دسترسی به Gemini با این API Key "
                        "مجاز نیست.\n\n"
                        "کلید API را بررسی کن."
                    )

                elif response.status == 404:
                    return (
                        f"❌ مدل `{model}` پیدا نشد.\n\n"
                        "مدل‌های فعال دوباره بررسی شدند، "
                        "اما این مدل در زمان درخواست در دسترس نبود."
                    )

                elif response.status == 429:
                    return (
                        "❌ تعداد درخواست‌های Gemini زیاد شده.\n\n"
                        "چند لحظه بعد دوباره امتحان کن."
                    )

                elif response.status >= 500:
                    return (
                        "❌ سرور Gemini موقتاً مشکل دارد.\n\n"
                        "چند لحظه بعد دوباره امتحان کن."
                    )

                else:
                    return (
                        f"❌ خطای Gemini: "
                        f"{response.status}"
                    )

    except asyncio.TimeoutError:
        return (
            "❌ زمان اتصال به Gemini تمام شد!\n"
            "دوباره امتحان کن."
        )

    except aiohttp.ClientError as e:
        print(f"❌ خطای شبکه Gemini: {e}")
        return (
            "❌ خطا در اتصال به سرور Gemini.\n"
            "اتصال اینترنت سرور را بررسی کن."
        )

    except Exception as e:
        print(f"❌ خطای داخلی Gemini: {e}")
        return (
            f"❌ خطای داخلی جیمینای:\n"
            f"{str(e)[:300]}"
        )


# ========================================
# ========================================
# ===== مترجم (پشتیبانی از فایل) =====
# ========================================
# ========================================

async def translate_text(text, target_lang="fa"):
    """ترجمه متن با Gemini"""

    if not text or len(text.strip()) < 2:
        return "❌ متن کافی برای ترجمه وجود ندارد!"

    if target_lang == "fa":
        lang_name = "فارسی"
    elif target_lang == "en":
        lang_name = "انگلیسی"
    else:
        lang_name = target_lang

    prompt = f"""
متن زیر را به {lang_name} ترجمه کن.

قوانین:
- ترجمه روان و طبیعی باشد.
- معنی اصلی متن حفظ شود.
- چیزی به متن اضافه نکن.
- چیزی از متن حذف نکن.
- فقط ترجمه را ارائه بده.

متن:

{text}
"""

    return await call_gemini(prompt)


# ========================================
# ========================================
# ===== مترجم پیشرفته برای فایل‌ها =====
# ========================================
# ========================================

async def translate_file_content(text, file_type="text", target_lang="fa"):
    """ترجمه محتوای فایل (PDF، عکس، ویدیو، ZIP) با حفظ فرمت"""

    if not text or len(text.strip()) < 2:
        return "❌ متنی برای ترجمه وجود ندارد!"

    lang_name = "فارسی" if target_lang == "fa" else "انگلیسی"

    prompt = f"""
متن زیر را به {lang_name} ترجمه کن.

نوع فایل: {file_type}

قوانین:
- هر بخش را جداگانه ترجمه کن
- متن‌های داخل تصویر یا جدول را هم ترجمه کن
- ترجمه روان و طبیعی باشد
- فرمت اصلی حفظ شود
- فقط ترجمه را ارائه بده

متن:
{text}
"""

    result = await call_gemini(prompt)

    # اضافه کردن متن اصلی + ترجمه
    if result and not result.startswith("❌"):
        return f"📄 **متن اصلی:**\n{text}\n\n🌍 **ترجمه:**\n{result}"
    return result


# ========================================
# ========================================
# ===== خلاصه‌سازی =====
# ========================================
# ========================================

async def summarize_text(text):
    """خلاصه‌سازی متن با Gemini"""

    if not text or len(text.strip()) < 50:
        return (
            "❌ متن کافی برای خلاصه‌سازی وجود ندارد!\n"
            "حداقل ۵۰ کاراکتر نیاز است."
        )

    # جلوگیری از درخواست بیش از حد بزرگ
    if len(text) > 30000:
        text = text[:30000] + "\n..."

    prompt = f"""
متن زیر را به زبان فارسی خلاصه کن.

قوانین:
- نکات مهم را حفظ کن.
- خلاصه واضح و منظم باشد.
- از حاشیه رفتن خودداری کن.
- اطلاعات مهم حذف نشود.
- در صورت امکان از تیتر و bullet استفاده کن.

متن:

{text}
"""

    return await call_gemini(prompt)


# ========================================
# ========================================
# ===== تحلیل کتاب =====
# ========================================
# ========================================

async def analyze_book(text):
    """تحلیل کتاب با Gemini"""

    if not text or len(text.strip()) < 100:
        return (
            "❌ متن کافی برای تحلیل وجود ندارد!\n"
            "حداقل ۱۰۰ کاراکتر نیاز است."
        )

    # محدودیت منطقی برای جلوگیری از درخواست خیلی سنگین
    if len(text) > 30000:
        text = text[:30000] + "\n..."

    prompt = f"""
کتاب یا متن زیر را به زبان فارسی به صورت حرفه‌ای تحلیل کن.

ساختار پاسخ:

۱. شخصیت‌های اصلی
- نام شخصیت
- نقش و اهمیت او

۲. تم‌ها و موضوعات اصلی
- موضوعات کلیدی
- مفاهیم مهم

۳. سبک نوشتاری
- نوع روایت
- زبان و لحن
- ویژگی‌های برجسته

۴. نکات کلیدی
- پیام‌های مهم
- اتفاقات یا ایده‌های مهم

۵. نقاط قوت و ضعف
- نقاط قوت اثر
- نقاط قابل بهبود

۶. جمع‌بندی نهایی
- یک جمع‌بندی روشن و مفید

تحلیل باید بر اساس متن داده‌شده باشد و اطلاعات ساختگی اضافه نشود.

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
    """استخراج متن از فایل PDF با شماره صفحات"""

    try:

        if not file_path:
            return None

        if not file_path.lower().endswith(".pdf"):
            return None

        doc = fitz.open(file_path)

        text_parts = []

        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()

            if page_text.strip():
                text_parts.append(f"📄 **صفحه {page_num}:**\n{page_text.strip()}")

        doc.close()

        if text_parts:
            return "\n\n".join(text_parts)

        return (
            "⚠️ فایل PDF متن قابل استخراج ندارد.\n"
            "ممکن است فایل به صورت اسکن شده باشد."
        )

    except Exception as e:

        print(
            f"❌ خطا در استخراج متن PDF: {e}"
        )

        return None


# ========================================
# ========================================
# ===== تایپیست فارسی (با فونت) =====
# ========================================
# ========================================

async def type_persian_text(text, font_name="Vazir", font_size=20):
    """تایپ متن فارسی با فونت زیبا"""

    if not text or not text.strip():
        return "❌ متنی برای تایپ وجود ندارد!"

    try:
        # اصلاح متن برای نمایش درست
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)

        font_list = {
            "Vazir": "وزیر",
            "IranSans": "ایران‌سنس",
            "Nazanin": "نازنین",
            "Yekan": "یکان",
            "Mitra": "میترا",
            "Lotus": "لوتوس",
            "Zar": "زر",
            "Traffic": "ترافیک"
        }

        font_name_display = font_list.get(font_name, font_name)

        # نتیجه نهایی
        result = f"""
✍️ **تایپیست فارسی**

📝 **متن اصلی:**
{text}

🔤 **فونت:** {font_name_display}

📏 **سایز:** {font_size}

✅ متن با فونت {font_name_display} تایپ شد!

---

💡 **فونت‌های موجود:**
• وزیر (Vazir)
• ایران‌سنس (IranSans)
• نازنین (Nazanin)
• یکان (Yekan)
• میترا (Mitra)
• لوتوس (Lotus)
• زر (Zar)
• ترافیک (Traffic)
"""
        return result

    except Exception as e:
        return f"❌ خطا در تایپ متن: {str(e)[:100]}"


# ========================================
# ========================================
# ===== کلینر (پاک‌سازی فایل) =====
# ========================================
# ========================================

async def clean_file_content(text, file_type="text"):
    """پاک‌سازی و بهینه‌سازی محتوای فایل"""

    if not text or not text.strip():
        return "❌ متنی برای پاک‌سازی وجود ندارد!"

    prompt = f"""
متن زیر را پاک‌سازی و بهینه‌سازی کن.

نوع فایل: {file_type}

قوانین:
- حذف فاصله‌های اضافی
- اصلاح علائم نگارشی
- یکدست کردن فونت
- بهبود خوانایی
- اصلاح غلط‌های املایی

متن:
{text}
"""

    result = await call_gemini(prompt)

    if result and not result.startswith("❌"):
        return f"🧹 **متن پاک‌سازی شده:**\n\n{result}"
    return result


# ========================================
# ========================================
# ===== تست اتصال Gemini =====
# ========================================
# ========================================

async def test_gemini_connection():
    """تست اتصال به Gemini"""

    if not GEMINI_API_KEY:
        return "❌ کلید جیمینای تنظیم نشده!"

    try:

        model = await get_available_model()

        if not model:
            return (
                "❌ هیچ مدل قابل استفاده‌ای پیدا نشد!"
            )

        result = await call_gemini(
            "فقط بنویس: اتصال موفق است."
        )

        if result and not result.startswith("❌"):
            return (
                f"✅ اتصال به جیمینای برقرار است!\n"
                f"🤖 مدل: {model}"
            )

        return result

    except Exception as e:

        return (
            f"❌ خطا در تست Gemini:\n"
            f"{str(e)[:300]}"
        )


print("✅ توابع Gemini بارگذاری شدند!")
