from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import json

router = Router()

# ========================================
# ========================================
# ===== کیبورد منوی کاربر (ساده) =====
# ========================================
# ========================================

def user_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 نظر و پیشنهاد")],
            [KeyboardButton(text="⭐ امتیاز به ربات")],
            [KeyboardButton(text="📱 فیلترشکن")],
        ],
        resize_keyboard=True
    )

# ========================================
# ========================================
# ===== کیبورد عضویت =====
# ========================================
# ========================================

def join_keyboard():
    channels = get_channels()
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========================================
# ========================================
# ===== ارسال بنر =====
# ========================================
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
# ========================================
# ===== ارسال کتاب =====
# ========================================
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
        [InlineKeyboardButton(text="📥 دریافت فایل", callback_data=f"download_book_{book_id}")]
    ])
    
    if cover_file_id:
        await message.answer_photo(cover_file_id, caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("download_book_"))
async def download_book(call: types.CallbackQuery):
    book_id = int(call.data.replace("download_book_", ""))
    book = get_book(book_id)
    if not book:
        await call.answer("❌ کتاب پیدا نشد!", show_alert=True)
        return
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = book
    increment_download(book_id)
    await call.message.answer_document(file_id, caption=f"📖 **{title}**\n\n✅ دانلود شد!")
    await call.answer("✅ دانلود شروع شد!")

# ========================================
# ========================================
# ===== ارسال مانگا =====
# ========================================
# ========================================

async def send_manga(message, manga_id):
    manga = get_manga(manga_id)
    if not manga:
        await message.answer("❌ مانگا پیدا نشد!")
        return
    
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = manga
    
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
        [InlineKeyboardButton(text="📥 دریافت فایل", callback_data=f"download_manga_{manga_id}")]
    ])
    
    if cover_file_id:
        await message.answer_photo(cover_file_id, caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("download_manga_"))
async def download_manga(call: types.CallbackQuery):
    manga_id = int(call.data.replace("download_manga_", ""))
    manga = get_manga(manga_id)
    if not manga:
        await call.answer("❌ مانگا پیدا نشد!", show_alert=True)
        return
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = manga
    increment_download(manga_id)
    await call.message.answer_document(file_id, caption=f"📖 **{title}**\n\n✅ دانلود شد!")
    await call.answer("✅ دانلود شروع شد!")

# ========================================
# ========================================
# ===== ارسال مانهوا =====
# ========================================
# ========================================

async def send_manhwa(message, manhwa_id):
    manhwa = get_manhwa(manhwa_id)
    if not manhwa:
        await message.answer("❌ مانهوا پیدا نشد!")
        return
    
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = manhwa
    
    text = f"🎨 **{title}**\n\n"
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
        [InlineKeyboardButton(text="📥 دریافت فایل", callback_data=f"download_manhwa_{manhwa_id}")]
    ])
    
    if cover_file_id:
        await message.answer_photo(cover_file_id, caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("download_manhwa_"))
async def download_manhwa(call: types.CallbackQuery):
    manhwa_id = int(call.data.replace("download_manhwa_", ""))
    manhwa = get_manhwa(manhwa_id)
    if not manhwa:
        await call.answer("❌ مانهوا پیدا نشد!", show_alert=True)
        return
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = manhwa
    increment_download(manhwa_id)
    await call.message.answer_document(file_id, caption=f"🎨 **{title}**\n\n✅ دانلود شد!")
    await call.answer("✅ دانلود شروع شد!")

# ========================================
# ========================================
# ===== دریافت فایل با رمز =====
# ========================================
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
# ========================================
# ===== نظر و پیشنهاد =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "💬 نظر و پیشنهاد")
async def feedback_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_feedback"}
    await message.answer("💬 **نظر یا پیشنهادت رو بفرست:**")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_feedback")
async def save_feedback(message: types.Message):
    add_feedback(message.from_user.id, message.text)
    user_states[message.from_user.id] = {}
    await message.bot.send_message(
        ADMIN_ID,
        f"📝 **نظر جدید:**\n\n👤 {message.from_user.full_name}\n🆔 `{message.from_user.id}`\n\n📄 {message.text}"
    )
    await message.answer("✅ **نظرت ثبت شد! ممنون 🙏**")

# ========================================
# ========================================
# ===== امتیاز به ربات =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "⭐ امتیاز به ربات")
async def rating_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rate_robot_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(text=f"{i}⭐", callback_data=f"rate_robot_{i}") for i in range(6, 11)]
    ])
    await message.answer(
        "⭐ **به ربات امتیاز بده!**\n\nاز ۱ تا ۱۰، به ربات چند میدی؟",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data.startswith("rate_robot_"))
async def save_rating(call: types.CallbackQuery):
    rating = int(call.data.replace("rate_robot_", ""))
    add_robot_rating(call.from_user.id, rating)
    await call.message.edit_text(f"✅ **امتیاز شما ثبت شد!**\n\n⭐ {rating} از ۱۰")
    await call.answer("✅ امتیاز ثبت شد!")

# ========================================
# ========================================
# ===== فیلترشکن =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📱 فیلترشکن")
async def list_vpn_user(message: types.Message):
    vpn_list = get_all_vpn()
    if not vpn_list:
        await message.answer("❌ هیچ فیلترشکنی موجود نیست!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔹 {vpn[1]}", callback_data=f"vpn_{vpn[0]}")] for vpn in vpn_list
    ])
    
    await message.answer(
        "📱 **معرفی فیلترشکن‌های قوی**\n\n"
        "یکی از گزینه‌های زیر رو انتخاب کن:",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data.startswith("vpn_"))
async def show_vpn(call: types.CallbackQuery):
    vpn_id = int(call.data.replace("vpn_", ""))
    vpn = get_vpn(vpn_id)
    if not vpn:
        await call.answer("❌ فیلترشکن پیدا نشد!", show_alert=True)
        return
    
    _, name, description, logo_file_id, video_file_id, link = vpn
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 مشاهده ویدیو", url=link)],
        [InlineKeyboardButton(text="🔗 دریافت لینک", url=link)],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_vpn")]
    ])
    
    text = f"📱 **معرفی فیلترشکن {name}**\n\n"
    text += f"📝 {description}\n\n"
    text += f"🔗 لینک: {link}"
    
    if logo_file_id:
        await call.message.answer_photo(logo_file_id, caption=text, reply_markup=keyboard)
    else:
        await call.message.answer(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "back_to_vpn")
async def back_to_vpn(call: types.CallbackQuery):
    await list_vpn_user(call.message)

# ========================================
# ========================================
# ===== استارت =====
# ========================================
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
            "به ربات خوش اومدی!",
            reply_markup=user_menu_keyboard()
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
    elif code.startswith("manga_"):
        try:
            manga_id = int(code.replace("manga_", ""))
            channels = get_channels()
            if channels:
                with open("temp.json", "w") as f:
                    json.dump({"manga_id": manga_id}, f)
                await message.answer(
                    "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
                    reply_markup=join_keyboard()
                )
                return
            await send_manga(message, manga_id)
        except ValueError:
            await message.answer("❌ لینک نامعتبر!")
    elif code.startswith("manhwa_"):
        try:
            manhwa_id = int(code.replace("manhwa_", ""))
            channels = get_channels()
            if channels:
                with open("temp.json", "w") as f:
                    json.dump({"manhwa_id": manhwa_id}, f)
                await message.answer(
                    "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
                    reply_markup=join_keyboard()
                )
                return
            await send_manhwa(message, manhwa_id)
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
    try:
        with open("temp.json", "r") as f:
            data = json.load(f)
        book_id = data.get("book_id")
        manga_id = data.get("manga_id")
        manhwa_id = data.get("manhwa_id")
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
    
    if book_id:
        await send_book(call.message, book_id)
    elif manga_id:
        await send_manga(call.message, manga_id)
    elif manhwa_id:
        await send_manhwa(call.message, manhwa_id)
