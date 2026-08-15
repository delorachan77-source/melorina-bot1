import os
from dotenv import load_dotenv

# ========================================
# ===== بارگذاری متغیرهای محیطی =====
# ========================================

load_dotenv()

# ========================================
# ===== تنظیمات اصلی ربات =====
# ========================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# آیدی ادمین اصلی
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8255361263"))
except ValueError:
    ADMIN_ID = 8255361263

# ========================================
# ===== هوش مصنوعی Gemini =====
# ========================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# مدل Gemini
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()

# ========================================
# ===== دیتابیس =====
# ========================================

DB_PATH = os.getenv(
    "DB_PATH",
    "bot.db"
).strip()

# ========================================
# ===== تنظیمات بکاپ =====
# ========================================

BACKUP_PATH = os.getenv(
    "BACKUP_PATH",
    f"{DB_PATH}.backup"
).strip()

# ========================================
# ===== تنظیمات ارسال همگانی =====
# ========================================

# فاصله بین ارسال پیام‌ها برای جلوگیری از Flood
BROADCAST_DELAY = float(
    os.getenv("BROADCAST_DELAY", "0.05")
)

# تعداد کاربران در هر بخش ارسال
BROADCAST_BATCH_SIZE = int(
    os.getenv("BROADCAST_BATCH_SIZE", "25")
)

# ========================================
# ===== تنظیمات عمومی =====
# ========================================

BOT_NAME = os.getenv(
    "BOT_NAME",
    "ربات مدیریت کتاب"
).strip()

# ========================================
# ===== بررسی تنظیمات ضروری =====
# ========================================

if not BOT_TOKEN:
    print("⚠️ هشدار: BOT_TOKEN تنظیم نشده!")

if ADMIN_ID <= 0:
    print("⚠️ هشدار: ADMIN_ID نامعتبر است!")

if not GEMINI_API_KEY:
    print("ℹ️ GEMINI_API_KEY تنظیم نشده؛ قابلیت‌های Gemini غیرفعال خواهند بود.")

# ========================================
# ===== نمایش وضعیت =====
# ========================================

print("✅ Config بارگذاری شد")
print(f"👤 ADMIN_ID: {ADMIN_ID}")
print(f"📁 DB_PATH: {DB_PATH}")
print(f"🤖 GEMINI: {'فعال' if GEMINI_API_KEY else 'غیرفعال'}")
print(f"🔧 GEMINI_MODEL: {GEMINI_MODEL}")
