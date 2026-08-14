from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import json
import os

router = Router()
user_states = {}

# ========================================
# ========================================
# ===== کیبورد عضویت اجباری =====
# ========================================
# ========================================

def join_keyboard():
    """ساخت دکمه‌های عضویت برای کانال‌های اجباری"""
    channels = get_channels()
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت در @{ch}", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========================================
# ========================================
# ===== ارسال بنر =====
# ========================================
# ========================================

async def send_banner(message):
    """ارسال بنر به کاربر (متن، عکس یا ویدیو)"""
    banner = get_banner()
    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(banner["file_id"], caption=banner["text"])
    else:
        await message.answer(banner["text"])

# ========================================
# ========================================
# ===== ارسال کتاب با جلد و اطلاعات کامل =====
# ========================================
# ========================================

async def send_book(message, book_id):
    """ارسال کتاب با جلد، اطلاعات و دکمه دانلود"""
    book = get_book(book_id)
    if not book:
        await message.answer("❌ کتاب پیدا نشد!")
        return
    
    # اطلاعات کتاب
    book_id, title, author, description, genre, cover_file_id, file_id, file_name, downloads = book
    
    # ساخت متن کتاب
    text = f"📖 **{title}**\n\n"
    if author:
        text += f"✍️ **نویسنده:** {author}\n"
    if genre:
        text += f"📂 **ژانر:** {genre}\n"
    if downloads:
        text += f"📥 **دانلودها:** {downloads} بار\n"
    if description:
        text += f"\n📝 **توضیحات:**\n{description}\n"
    text += f"\n🔗 برای دریافت فایل روی دکمه زیر کلیک کن."
    
    # دکمه دریافت فایل
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 دریافت فایل", callback_data=f"download_{book_id}")]
    ])
    
    # ارسال جلد (اگه وجود داشته باشه)
    if cover_file_id:
        await message.answer_photo(cover_file_id, caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

# ========================================
# ========================================
# ===== دانلود فایل کتاب =====
# ========================================
# ========================================

@router.callback_query(lambda c: c.data.startswith("download_"))
async def download_book(call: types.CallbackQuery):
    """ارسال فایل کتاب به کاربر"""
    book_id = int(call.data.replace("download_", ""))
    book = get_book(book_id)
    
    if not book:
        await call.answer("❌ کتاب پیدا نشد!", show_alert=True)
        return
    
    # اطلاعات کتاب
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = book
    
    # افزایش تعداد دانلود
    increment_download(book_id)
    
    # ارسال فایل
    await call.message.answer_document(
        file_id,
        caption=f"📖 **{title}**\n\n✅ دانلود شد!"
    )
    await call.answer("✅ دانلود شروع شد!")

# ========================================
# ========================================
# ===== استارت =====
# ========================================
# ========================================

@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    
    # ثبت کاربر در دیتابیس
    add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or ""
    )
    
    # ===== استارت معمولی (بدون کد) =====
    if len(args) == 1:
        await send_banner(message)
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            "به ربات مدیریت کتاب خوش اومدی!"
        )
        return
    
    # ===== استارت با کد کتاب =====
    code = args[1]
    if code.startswith("book_"):
        try:
            book_id = int(code.replace("book_", ""))
            
            # ===== بررسی عضویت اجباری =====
            channels = get_channels()
            if channels:
                # ذخیره book_id برای بعد از عضویت
                with open("temp.json", "w") as f:
                    json.dump({"book_id": book_id}, f)
                
                await message.answer(
                    "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
                    reply_markup=join_keyboard()
                )
                return
            
            # اگه کانالی نیست، مستقیم کتاب رو بفرست
            await send_book(message, book_id)
            
        except ValueError:
            await message.answer("❌ لینک نامعتبر!")
    else:
        await message.answer("❌ لینک نامعتبر!")

# ========================================
# ========================================
# ===== بررسی عضویت =====
# ========================================
# ========================================

@router.callback_query(lambda c: c.data == "check_mem")
async def check_mem(call: types.CallbackQuery):
    """بررسی عضویت کاربر در کانال‌های اجباری"""
    try:
        with open("temp.json", "r") as f:
            data = json.load(f)
        book_id = data.get("book_id")
    except:
        await call.message.edit_text("❌ لینک نامعتبر!")
        return
    
    # چک کردن عضویت در همه کانال‌ها
    for ch in get_channels():
        try:
            member = await call.bot.get_chat_member(f"@{ch}", call.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await call.answer(f"❌ در کانال @{ch} عضو نشدی!", show_alert=True)
                return
        except Exception as e:
            await call.answer(f"❌ خطا در بررسی کانال @{ch}!", show_alert=True)
            return
    
    # همه چی اوکی
    await call.message.delete()
    
    # ارسال کتاب
    await send_book(call.message, book_id)
