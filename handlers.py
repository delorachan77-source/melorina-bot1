from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID, GEMINI_API_KEY
from database import *
import json
import aiohttp

router = Router()
user_states = {}

# ========================================
# ===== شخصیت‌های جیمینای =====
# ========================================
PERSONALITIES = {
    "کیوت": "با لحن شیرین، صمیمی و دلنشین پاسخ بده. 😊",
    "مغرور": "با لحن مغرور و برتر پاسخ بده. 🦁",
    "بامزه": "با لحن شوخ و طنز پاسخ بده. 😂",
    "خجالتی": "با لحن خجالتی و کم‌رو پاسخ بده. 😳",
    "باهوش": "با لحن علمی و دقیق پاسخ بده. 🧠",
    "دارک": "با لحن تاریک و مرموز پاسخ بده. 🌙",
}

# ========================================
# ===== کیبورد منوی کاربر =====
# ========================================
def user_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 کتاب‌ها")],
            [KeyboardButton(text="💬 چت")],
            [KeyboardButton(text="💬 نظر و پیشنهاد")],
            [KeyboardButton(text="⭐ امتیاز به ربات")],
        ],
        resize_keyboard=True
    )

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
# ===== نظر و پیشنهاد =====
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
# ===== امتیاز به ربات =====
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
# ===== چت با جیمینای =====
# ========================================
@router.message(lambda m: m.text == "💬 چت")
async def user_ai_chat_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_user_ai_chat"}
    await message.answer("💬 **چت با جیمینای**\n\nهر چی دوست داری بپرس! 😊\nبرای بستن /cancel بفرست.")

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_user_ai_chat")
async def user_ai_chat_response(message: types.Message):
    if message.text == "/cancel":
        user_states[message.from_user.id] = {}
        await message.answer("✅ چت بسته شد!")
        return
    if not GEMINI_API_KEY:
        await message.answer("❌ جیمینای در دسترس نیست!")
        return
    await message.answer("🤔 دارم فکر میکنم...")
    
    personality = get_setting("gemini_personality") or "کیوت"
    personality_prompt = PERSONALITIES.get(personality, "")
    
    response = await get_gemini_response(message.text, personality_prompt)
    if response:
        await message.answer(response)
    else:
        await message.answer("❌ خطا در ارتباط با جیمینای!")

# ========================================
# ===== کتاب‌ها =====
# ========================================
@router.message(lambda m: m.text == "📚 کتاب‌ها")
async def list_books_user(message: types.Message):
    books = get_all_books()
    if not books:
        await message.answer("❌ هیچ کتابی موجود نیست!")
        return
    
    text = "📚 **لیست کتاب‌ها:**\n\n"
    for book in books[:10]:
        text += f"• {book[1]} - {book[2] or 'نامشخص'}\n"
    if len(books) > 10:
        text += f"\n... و {len(books) - 10} کتاب دیگه"
    await message.answer(text)

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
            "به ربات مدیریت کتاب خوش اومدی!",
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

# ========================================
# ===== توابع جیمینای =====
# ========================================
async def get_gemini_response(prompt, personality_prompt=""):
    try:
        if not GEMINI_API_KEY:
            return "❌ جیمینای در دسترس نیست!"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
        full_prompt = f"""{personality_prompt}
        
        به فارسی پاسخ بده. پاسخ‌هات کوتاه و جذاب باشه.
        
        سوال: {prompt}
        """
        payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return None
    except:
        return None
