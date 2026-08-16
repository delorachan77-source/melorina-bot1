import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router as user_router
from admin import router as admin_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== ثبت هر دو روت =====
dp.include_router(admin_router)   # ← پنل ادمین
dp.include_router(user_router)    # ← منوی کاربر

async def main():
    print("🤖 ربات روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
