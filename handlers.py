from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    elif banner["type"] == "document" and banner["file_id"]:
        await message.answer_document(banner["file_id"], caption=banner["text"])
    else:
        await message.answer(banner["text"])

# ========================================
# ===== ارسال کتاب =====
# ========================================
async def send_book(message, book_id):
    book = get_book(book_id)
    if not book:
        await message.answer("❌ کتاب پیدا نشد!")
        return
    
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = book
    
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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 دریافت فایل", callback_data=f"download_{book_id}")]
    ])
    
    if cover_file_id:
        await message.answer_photo(cover_file_id, caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

# ========================================
# ===== دانلود کتاب =====
# ========================================
@router.callback_query(lambda c: c.data.startswith("download_"))
async def download_book(call: types.CallbackQuery):
    book_id = int(call.data.replace("download_", ""))
    book = get_book(book_id)
    
    if not book:
        await call.answer("❌ کتاب پیدا نشد!", show_alert=True)
        return
    
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = book
    
    increment_download(book_id)
    
    await call.message.answer_document(
        file_id,
        caption=f"📖 **{title}**\n\n✅ دانلود شد!"
    )
    await call.answer("✅ دانلود شروع شد!")

# ========================================
# ===== دریافت فایل با رمز =====
# ========================================
@router.message(lambda m: m.text and not m.text.startswith("/"))
async def handle_password_file(message: types.Message):
    file_info = get_password_file_by_code(message.text.strip())
    if file_info:
        file_id, name, file_type, caption = file_info[2], file_info[1], file_info[3], file_info[4]
        
        if file_type == "photo":
            await message.answer_photo(file_id, caption=f"🔐 {name}\n\n{caption or ''}")
        elif file_type == "video":
            await message.answer_video(file_id, caption=f"🔐 {name}\n\n{caption or ''}")
        else:
            await message.answer_document(file_id, caption=f"🔐 {name}\n\n{caption or ''}")

# ========================================
# ===== استارت =====
# ========================================
@router.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    
    add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or ""
    )
    
    if len(args) == 1:
        await send_banner(message)
        await message.answer(
            f"👋 **سلام {message.from_user.first_name}!**\n\n"
            "به ربات مدیریت کتاب خوش اومدی!"
        )
        return
    
    code = args[1]
    if code.startswith("book_"):
        try:
            book_id = int(code.replace("book_", ""))
            
            channels = get_channels()
            if channels:
                with open("temp.json", "w") as f:
                    json.dump({"book_id": book_id}, f)
                await message.answer(
                    "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
                    reply_markup=join_keyboard()
                )
                return
            
            await send_book(message, book_id)
        except ValueError:
            await message.answer("❌ لینک نامعتبر!")
    else:
        await message.answer("❌ لینک نامعتبر!")

# ========================================
# ===== بررسی عضویت =====
# ========================================
@router.callback_query(lambda c: c.data == "check_mem")
async def check_mem(call: types.CallbackQuery):
    try:
        with open("temp.json", "r") as f:
            data = json.load(f)
        book_id = data.get("book_id")
    except:
        await call.message.edit_text("❌ لینک نامعتبر!")
        return
    
    for ch in get_channels():
        try:
            member = await call.bot.get_chat_member(f"@{ch}", call.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await call.answer(f"❌ در کانال @{ch} عضو نشدی!", show_alert=True)
                return
        except:
            await call.answer(f"❌ خطا!", show_alert=True)
            return
    
    await call.message.delete()
    await send_book(call.message, book_id)
