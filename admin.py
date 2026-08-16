from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID

router = Router()

# ===== کیبورد پنل ادمین =====
def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 مدیریت کتاب‌ها")],
            [KeyboardButton(text="📢 مدیریت کانال‌ها")],
            [KeyboardButton(text="🎨 مدیریت بنر")],
            [KeyboardButton(text="👥 مدیریت کاربران")],
            [KeyboardButton(text="📊 آمار")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )

@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما ادمین نیستید!")
        return
    await message.answer("⚙️ پنل مدیریت:", reply_markup=admin_menu())

@router.message(lambda m: m.text == "📚 مدیریت کتاب‌ها" and m.from_user.id == ADMIN_ID)
async def manage_books(message: types.Message):
    await message.answer("📚 مدیریت کتاب‌ها (در حال توسعه)")

@router.message(lambda m: m.text == "📢 مدیریت کانال‌ها" and m.from_user.id == ADMIN_ID)
async def manage_channels(message: types.Message):
    await message.answer("📢 مدیریت کانال‌ها (در حال توسعه)")

@router.message(lambda m: m.text == "🎨 مدیریت بنر" and m.from_user.id == ADMIN_ID)
async def manage_banner(message: types.Message):
    await message.answer("🎨 مدیریت بنر (در حال توسعه)")

@router.message(lambda m: m.text == "👥 مدیریت کاربران" and m.from_user.id == ADMIN_ID)
async def manage_users(message: types.Message):
    await message.answer("👥 مدیریت کاربران (در حال توسعه)")

@router.message(lambda m: m.text == "📊 آمار" and m.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    await message.answer("📊 آمار ربات (در حال توسعه)")

@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())
