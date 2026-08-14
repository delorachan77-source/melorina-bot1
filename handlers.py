from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import *
import json

router = Router()
user_states = {}

# ========================================
# ===== کیبورد عضویت =====
# ========================================
def join_keyboard():
    channels = get_channels()
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========================================
# ===== ارسال بنر =====
# ========================================
async def send_banner(message):
    banner = get_banner()
    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(banner["file_id"], caption=banner["text"])
    else:
        await message.answer(banner["text"])

# ========================================
# ===== استارت =====
# ========================================
@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    
    if len(args) == 1:
        await send_banner(message)
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            "به ربات مدیریت کتاب خوش اومدی!\n"
            "برای دریافت کتاب از لینک مخصوص استفاده کن.\n"
            "مثال: `https://t.me/ربات?start=book_1`"
        )
        return
    
    # استارت با کد کتاب
    code = args[1]
    if code.startswith("book_"):
        book_id = int(code.replace("book_", ""))
        book = get_book(book_id)
        if book:
            increment_download(book_id)
            await message.answer_document(
                book[4],
                caption=f"📖 **{book[1]}**\n✍️ {book[2] or 'نامشخص'}\n\n{book[3] or ''}"
            )
            await send_banner(message)
        else:
            await message.answer("❌ کتاب پیدا نشد!")
