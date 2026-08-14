from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_ID

router = Router()

@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 سلام! ربات روشن شد!")

@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما ادمین نیستید!")
        return
    await message.answer("⚙️ پنل مدیریت")
