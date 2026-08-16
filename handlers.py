from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
import json

router = Router()

# ===== منوی کاربر =====
def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 کتاب‌ها")],
            [KeyboardButton(text="💬 نظر و پیشنهاد")],
            [KeyboardButton(text="⭐ امتیاز به ربات")]
        ],
        resize_keyboard=True
    )

@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        f"👋 سلام {message.from_user.first_name}!\nبه ربات خوش اومدی!",
        reply_markup=user_menu()
    )

@router.message(lambda m: m.text == "📚 کتاب‌ها")
async def list_books(message: types.Message):
    await message.answer("📚 لیست کتاب‌ها:\nهنوز کتابی اضافه نشده!")

@router.message(lambda m: m.text == "💬 نظر و پیشنهاد")
async def feedback(message: types.Message):
    await message.answer("💬 نظر یا پیشنهادت رو بفرست:")

@router.message(lambda m: m.text == "⭐ امتیاز به ربات")
async def rating(message: types.Message):
    await message.answer("⭐ امتیازت رو بفرست (۱ تا ۱۰):")
