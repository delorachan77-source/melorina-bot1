# main.py

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import router as handlers_router
from admin import router as admin_router


# ========================================
# تنظیمات لاگ
# ========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ========================================
# بررسی تنظیمات
# ========================================

if not BOT_TOKEN:
    raise ValueError(
        "❌ BOT_TOKEN در متغیرهای محیطی تنظیم نشده است!"
    )


# ========================================
# ساخت Bot
# ========================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)


# ========================================
# ساخت Dispatcher
# ========================================

dp = Dispatcher()


# ========================================
# ثبت Router ها
# ========================================

# هندلرهای کاربران
dp.include_router(handlers_router)

# پنل ادمین
dp.include_router(admin_router)


# ========================================
# Startup
# ========================================

async def on_startup():
    logger.info("========================================")
    logger.info("🚀 ربات در حال راه‌اندازی است...")
    logger.info("========================================")

    try:
        me = await bot.get_me()

        logger.info(
            f"✅ ربات با موفقیت متصل شد!"
        )

        logger.info(
            f"🤖 نام: {me.full_name}"
        )

        logger.info(
            f"🔗 Username: @{me.username}"
        )

        logger.info(
            f"🆔 ID: {me.id}"
        )

    except Exception as e:
        logger.error(
            f"❌ خطا در اتصال به تلگرام: {e}"
        )
        raise


# ========================================
# Shutdown
# ========================================

async def on_shutdown():
    logger.info("========================================")
    logger.info("🛑 در حال خاموش کردن ربات...")
    logger.info("========================================")

    try:
        await bot.session.close()
        logger.info("✅ اتصال Bot بسته شد.")

    except Exception as e:
        logger.error(
            f"❌ خطا هنگام بستن Bot: {e}"
        )


# ========================================
# اجرای اصلی
# ========================================

async def main():

    # Startup
    await on_startup()

    logger.info("📡 Polling شروع شد...")
    logger.info("📚 سیستم مدیریت کتاب فعال است.")
    logger.info("🔐 سیستم فایل رمزدار فعال است.")
    logger.info("📢 سیستم عضویت اجباری فعال است.")
    logger.info("🎨 سیستم بنر فعال است.")
    logger.info("👥 سیستم کاربران فعال است.")
    logger.info("🤖 سیستم Gemini در صورت تنظیم API فعال است.")
    logger.info("⚙️ پنل ادمین فعال است.")

    try:

        # حذف آپدیت‌های قدیمی تلگرام
        await bot.delete_webhook(
            drop_pending_updates=True
        )

        # شروع Polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )

    except asyncio.CancelledError:

        logger.info(
            "🛑 Polling متوقف شد."
        )

    except Exception as e:

        logger.exception(
            f"❌ خطای اصلی ربات: {e}"
        )

    finally:

        await on_shutdown()


# ========================================
# اجرای فایل
# ========================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:

        logger.info(
            "🛑 ربات توسط کاربر متوقف شد."
        )

    except Exception as e:

        logger.exception(
            f"❌ خطای غیرمنتظره: {e}"
)
