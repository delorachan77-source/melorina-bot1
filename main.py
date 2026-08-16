import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✅ ربات کار میکنه!")

@dp.message(Command("panel"))
async def panel(message: types.Message):
    await message.answer("⚙️ پنل ادمین (تست)")

async def main():
    print("🤖 ربات روشن شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
