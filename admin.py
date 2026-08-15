from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID, GEMINI_API_KEY
from database import *
import asyncio
import aiohttp
import json
import os
from datetime import datetime

router = Router()
user_states = {}

# ========================================
# ===== کیبورد اصلی پنل ادمین =====
# ========================================
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 مدیریت کتاب‌ها")],
            [KeyboardButton(text="📢 مدیریت کانال‌ها")],
            [KeyboardButton(text="🎨 مدیریت بنر")],
            [KeyboardButton(text="👀 دیدن بنر")],
            [KeyboardButton(text="👀 پنل عضویت")],
            [KeyboardButton(text="👥 مدیریت کاربران")],
            [KeyboardButton(text="📊 آمار پیشرفته")],
            [KeyboardButton(text="🤖 هوش مصنوعی")],
            [KeyboardButton(text="🎭 شخصیت جیمینای")],
            [KeyboardButton(text="📨 ارسال بنر به آیدی‌ها")],
            [KeyboardButton(text="📤 ارسال همگانی")],
            [KeyboardButton(text="🔐 رمز فایل")],
            [KeyboardButton(text="📝 نظرات و پیشنهادات")],
            [KeyboardButton(text="📋 بروزرسانی‌ها")],
            [KeyboardButton(text="💾 بکاپ و بازیابی")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )

# ========================================
# ===== پنل اصلی =====
# ========================================
@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    add_admin_activity(message.from_user.id, "ورود به پنل")
    await message.answer(
        "⚙️ **پنل مدیریت پیشرفته**\n\n"
        "📊 از دکمه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
    )

# ========================================
# ===== بستن پنل =====
# ========================================
@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ========================================
# ========================================
# 🎭 شخصیت جیمینای
# ========================================
# ========================================
PERSONALITIES = {
    "کیوت": "با لحن شیرین، صمیمی و دلنشین پاسخ بده. 😊",
    "مغرور": "با لحن مغرور و برتر پاسخ بده. 🦁",
    "بامزه": "با لحن شوخ و طنز پاسخ بده. 😂",
    "خجالتی": "با لحن خجالتی و کم‌رو پاسخ بده. 😳",
    "باهوش": "با لحن علمی و دقیق پاسخ بده. 🧠",
    "دارک": "با لحن تاریک و مرموز پاسخ بده. 🌙",
}

@router.message(lambda m: m.text == "🎭 شخصیت جیمینای" and m.from_user.id == ADMIN_ID)
async def personality_panel(message: types.Message):
    current = get_setting("gemini_personality") or "کیوت"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🌸 {name}", callback_data=f"personality_{name}")] for name in PERSONALITIES.keys()
    ] + [[InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]])
    await message.answer(
        f"🎭 **شخصیت جیمینای**\n\n"
        f"شخصیت فعلی: «{current}»\n\n"
        f"یک شخصیت رو انتخاب کن:",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data.startswith("personality_"))
async def set_personality(call: types.CallbackQuery):
    personality = call.data.replace("personality_", "")
    set_setting("gemini_personality", personality)
    await call.message.edit_text(
        f"✅ شخصیت به «{personality}» تغییر کرد!\n\n"
        f"📝 توضیحات: {PERSONALITIES.get(personality, '')}"
    )

# ========================================
# ========================================
# 👀 پنل عضویت اجباری
# ========================================
# ========================================
@router.message(lambda m: m.text == "👀 پنل عضویت" and m.from_user.id == ADMIN_ID)
async def view_join_panel(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("❌ هیچ کانالی برای عضویت اجباری تنظیم نشده!")
        return
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 عضویت", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_mem_inline")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "👀 **پنل عضویت اجباری**\n\n"
        "برای دریافت فایل، در کانال‌های زیر عضو شوید:",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "check_mem_inline")
async def check_mem_inline(call: types.CallbackQuery):
    await call.answer("✅ عضویت تایید شد!", show_alert=True)

# ========================================
# ========================================
# 📚 مدیریت کتاب‌ها
# ========================================
# ========================================
@router.message(lambda m: m.text == "📚 مدیریت کتاب‌ها" and m.from_user.id == ADMIN_ID)
async def manage_books(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن کتاب", callback_data="add_book")],
        [InlineKeyboardButton(text="📋 لیست کتاب‌ها", callback_data="list_books")],
        [InlineKeyboardButton(text="🗑 حذف کتاب", callback_data="delete_book")],
        [InlineKeyboardButton(text="🔍 جستجوی کتاب", callback_data="search_book")],
        [InlineKeyboardButton(text="📂 کتاب‌های یک ژانر", callback_data="genre_books")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("📚 **مدیریت کتاب‌ها**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_book")
async def add_book_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_states[call.from_user.id] = {"state": "waiting_title"}
    await call.message.edit_text("📝 **عنوان کتاب رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_title")
async def get_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_author"
    await message.answer("✍️ **نویسنده کتاب رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_author")
async def get_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_genre"
    await message.answer("📂 **ژانر کتاب رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_genre")
async def get_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_description"
    await message.answer("📝 **توضیحات کتاب رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_description")
async def get_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_cover"
    await message.answer("🖼 **عکس جلد کتاب رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_cover")
async def get_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_file"
        await message.answer("📄 **حالا فایل کتاب رو بفرست (PDF/ZIP):**")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_file"
        await message.answer("📄 **حالا فایل کتاب رو بفرست (PDF/ZIP):**")
    else:
        await message.answer("❌ لطفاً یک عکس بفرست یا /skip بزن!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_file")
async def get_file(message: types.Message):
    data = user_states[message.from_user.id]
    add_book(
        title=data.get("title"),
        author=data.get("author", ""),
        description=data.get("description", ""),
        genre=data.get("genre", ""),
        cover_file_id=data.get("cover", ""),
        file_id=message.document.file_id,
        file_name=message.document.file_name or "",
        file_size=message.document.file_size or 0
    )
    user_states[message.from_user.id] = {}
    add_admin_activity(message.from_user.id, "افزودن کتاب", f"کتاب: {data.get('title')}")
    await message.answer(f"✅ **کتاب «{data.get('title')}» با موفقیت اضافه شد!**")

@router.callback_query(lambda c: c.data == "list_books")
async def list_books(call: types.CallbackQuery):
    books = get_all_books()
    if not books:
        await call.message.edit_text("❌ هیچ کتابی ثبت نشده!")
        return
    text = "📋 **لیست کتاب‌ها:**\n\n"
    for book in books[:10]:
        text += f"• `{book[0]}` - {book[1]} (دانلود: {book[8]})\n"
    if len(books) > 10:
        text += f"\n... و {len(books) - 10} کتاب دیگه"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_book")
async def delete_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_delete"}
    await call.message.edit_text("📝 **آیدی کتاب رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete")
async def delete_book_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)
        if book:
            delete_book(book_id)
            add_admin_activity(message.from_user.id, "حذف کتاب", f"کتاب: {book[1]}")
            await message.answer(f"✅ کتاب «{book[1]}» حذف شد!")
        else:
            await message.answer("❌ کتاب پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "search_book")
async def search_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_search"}
    await call.message.edit_text("🔍 **عبارت جستجو رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_search")
async def search_book_confirm(message: types.Message):
    query = message.text
    results = search_books(query)
    if not results:
        await message.answer(f"❌ نتیجه‌ای برای «{query}» پیدا نشد!")
        return
    text = f"🔍 **نتایج جستجو برای «{query}»:**\n\n"
    for book in results[:5]:
        text += f"• `{book[0]}` - {book[1]} (دانلود: {book[8]})\n"
    if len(results) > 5:
        text += f"\n... و {len(results) - 5} نتیجه دیگه"
    await message.answer(text)
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "genre_books")
async def genre_books_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_genre_list"}
    await call.message.edit_text("📂 **نام ژانر رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_genre_list")
async def genre_books_confirm(message: types.Message):
    genre = message.text
    books = get_books_by_genre(genre)
    if not books:
        await message.answer(f"❌ هیچ کتابی در ژانر «{genre}» پیدا نشد!")
        return
    text = f"📂 **کتاب‌های ژانر «{genre}»:**\n\n"
    for book in books[:10]:
        text += f"• `{book[0]}` - {book[1]}\n"
    if len(books) > 10:
        text += f"\n... و {len(books) - 10} کتاب دیگه"
    await message.answer(text)
    user_states[message.from_user.id] = {}

# ========================================
# ========================================
# 📢 مدیریت کانال‌ها
# ========================================
# ========================================
@router.message(lambda m: m.text == "📢 مدیریت کانال‌ها" and m.from_user.id == ADMIN_ID)
async def manage_channels(message: types.Message):
    channels = get_channels()
    text = "📢 **لیست کانال‌ها:**\n\n"
    text += "\n".join([f"• @{ch}" for ch in channels]) if channels else "❌ هیچ کانالی وجود نداره!"
    await message.answer(text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن کانال", callback_data="add_channel")],
        [InlineKeyboardButton(text="➖ حذف کانال", callback_data="remove_channel")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("یک گزینه رو انتخاب کن:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_channel")
async def add_channel_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_channel"}
    await call.message.edit_text("📢 **نام کانال رو بفرست (بدون @):**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_channel")
async def add_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    add_channel(ch)
    user_states[message.from_user.id] = {}
    add_admin_activity(message.from_user.id, "افزودن کانال", f"کانال: @{ch}")
    await message.answer(f"✅ کانال @{ch} اضافه شد!")

@router.callback_query(lambda c: c.data == "remove_channel")
async def remove_channel_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_remove_channel"}
    await call.message.edit_text("📢 **نام کانال رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_remove_channel")
async def remove_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")
    delete_channel(ch)
    user_states[message.from_user.id] = {}
    add_admin_activity(message.from_user.id, "حذف کانال", f"کانال: @{ch}")
    await message.answer(f"✅ کانال @{ch} حذف شد!")

# ========================================
# ========================================
# 🎨 مدیریت بنر
# ========================================
# ========================================
@router.message(lambda m: m.text == "🎨 مدیریت بنر" and m.from_user.id == ADMIN_ID)
async def manage_banner(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 تنظیم بنر", callback_data="set_banner")],
        [InlineKeyboardButton(text="🗑 حذف بنر", callback_data="delete_banner")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("🎨 **مدیریت بنر**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "set_banner")
async def set_banner_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_banner"}
    await call.message.edit_text("📝 **بنر رو بفرست**\n\n• متن\n• عکس\n• ویدیو\n• فایل (PDF, ZIP و...)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner")
async def set_banner_confirm(message: types.Message):
    if message.text:
        set_banner("text", None, message.text)
        await message.answer("✅ بنر متنی ذخیره شد!")
    elif message.photo:
        set_banner("photo", message.photo[-1].file_id, message.caption or "")
        await message.answer("✅ بنر عکس ذخیره شد!")
    elif message.video:
        set_banner("video", message.video.file_id, message.caption or "")
        await message.answer("✅ بنر ویدیو ذخیره شد!")
    elif message.document:
        set_banner("document", message.document.file_id, message.caption or "")
        await message.answer("✅ بنر فایل ذخیره شد!")
    else:
        await message.answer("❌ نوع فایل پشتیبانی نمیشه!")
        return
    user_states[message.from_user.id] = {}
    add_admin_activity(message.from_user.id, "تنظیم بنر")

@router.callback_query(lambda c: c.data == "delete_banner")
async def delete_banner_confirm(call: types.CallbackQuery):
    delete_banner()
    add_admin_activity(call.from_user.id, "حذف بنر")
    await call.message.edit_text("✅ بنر حذف شد!")

@router.message(lambda m: m.text == "👀 دیدن بنر" and m.from_user.id == ADMIN_ID)
async def view_banner(message: types.Message):
    banner = get_banner()
    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "document" and banner["file_id"]:
        await message.answer_document(banner["file_id"], caption=banner["text"])
    else:
        await message.answer(f"📝 **بنر فعلی:**\n\n{banner['text']}")

# ========================================
# ========================================
# 👥 مدیریت کاربران
# ========================================
# ========================================
@router.message(lambda m: m.text == "👥 مدیریت کاربران" and m.from_user.id == ADMIN_ID)
async def manage_users(message: types.Message):
    users = get_all_users()
    count = get_user_count()
    text = f"👥 **مدیریت کاربران**\n\n📊 تعداد کل کاربران: {count} نفر\n\n"
    if users:
        text += "**۱۰ کاربر اخیر:**\n"
        for user in users[:10]:
            text += f"• {user[1] or 'نامشخص'} - {user[0]}\n"
    else:
        text += "❌ هیچ کاربری ثبت نشده!"
    await message.answer(text)

# ========================================
# ========================================
# 📊 آمار پیشرفته
# ========================================
# ========================================
@router.message(lambda m: m.text == "📊 آمار پیشرفته" and m.from_user.id == ADMIN_ID)
async def advanced_stats(message: types.Message):
    books = get_all_books()
    channels = get_channels()
    users = get_user_count()
    total_downloads = sum(book[8] for book in books)
    popular = sorted(books, key=lambda x: x[8], reverse=True)
    popular_text = ""
    if popular:
        popular_text = f"🏆 **کتاب پرفروش:** {popular[0][1]} ({popular[0][8]} دانلود)"
    
    ratings = get_robot_ratings()
    
    await message.answer(
        f"📊 **آمار پیشرفته ربات:**\n\n"
        f"📁 **کتاب‌ها:** {len(books)} تا\n"
        f"📥 **کل دانلودها:** {total_downloads} بار\n"
        f"📢 **کانال‌ها:** {len(channels)} تا\n"
        f"👥 **کاربران:** {users} نفر\n"
        f"⭐ **امتیاز ربات:** {ratings['avg']} از ۱۰ ({ratings['count']} نظر)\n\n"
        f"{popular_text}"
    )

# ========================================
# ========================================
# 🤖 هوش مصنوعی
# ========================================
# ========================================
@router.message(lambda m: m.text == "🤖 هوش مصنوعی" and m.from_user.id == ADMIN_ID)
async def ai_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 خلاصه‌سازی کتاب", callback_data="ai_summarize")],
        [InlineKeyboardButton(text="💬 چت با جیمینای", callback_data="ai_chat")],
        [InlineKeyboardButton(text="📊 تحلیل کتاب", callback_data="ai_analyze")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer(
        "🤖 **پنل هوش مصنوعی با جیمینای**\n\n"
        "✨ قابلیت‌های پیشرفته:\n"
        "• خلاصه‌سازی هوشمند کتاب‌ها\n"
        "• چت با جیمینای\n"
        "• تحلیل عمیق کتاب‌ها",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "ai_summarize")
async def ai_summarize_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_summarize"}
    await call.message.edit_text("📝 **آیدی کتاب رو برای خلاصه‌سازی بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_summarize")
async def ai_summarize_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)
        if not book:
            await message.answer("❌ کتاب پیدا نشد!")
            user_states[message.from_user.id] = {}
            return
        await message.answer(f"🔄 در حال خلاصه‌سازی کتاب «{book[1]}» با جیمینای...")
        if not GEMINI_API_KEY:
            await message.answer("❌ کلید جیمینای تنظیم نشده!")
            user_states[message.from_user.id] = {}
            return
        summary = await get_gemini_summary(book[6])
        if summary:
            await message.answer(f"📝 **خلاصه کتاب «{book[1]}»:**\n\n{summary}\n\n🤖 تولید شده توسط Gemini AI")
        else:
            await message.answer("❌ خطا در خلاصه‌سازی!")
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)[:500]}")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "ai_analyze")
async def ai_analyze_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_analyze"}
    await call.message.edit_text("📊 **آیدی کتاب رو برای تحلیل بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_analyze")
async def ai_analyze_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)
        if not book:
            await message.answer("❌ کتاب پیدا نشد!")
            user_states[message.from_user.id] = {}
            return
        await message.answer(f"🔄 در حال تحلیل کتاب «{book[1]}» با جیمینای...")
        if not GEMINI_API_KEY:
            await message.answer("❌ کلید جیمینای تنظیم نشده!")
            user_states[message.from_user.id] = {}
            return
        analysis = await get_gemini_analysis(book[6])
        if analysis:
            await message.answer(f"📊 **تحلیل کتاب «{book[1]}»:**\n\n{analysis}\n\n🤖 تحلیل شده توسط Gemini AI")
        else:
            await message.answer("❌ خطا در تحلیل کتاب!")
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)[:500]}")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "ai_chat")
async def ai_chat_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_ai_chat"}
    await call.message.edit_text("💬 **چت با جیمینای**\n\nهر چی دوست داری بپرس! 😊\nبرای بستن /cancel بفرست.")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_ai_chat")
async def ai_chat_response(message: types.Message):
    if message.text == "/cancel":
        user_states[message.from_user.id] = {}
        await message.answer("✅ چت بسته شد!")
        return
    if not GEMINI_API_KEY:
        await message.answer("❌ کلید جیمینای تنظیم نشده!")
        return
    
    personality = get_setting("gemini_personality") or "کیوت"
    personality_prompt = PERSONALITIES.get(personality, "")
    
    await message.answer(f"🤔 دارم فکر میکنم... (شخصیت: {personality})")
    response = await get_gemini_response(message.text, personality_prompt)
    if response:
        await message.answer(response)
    else:
        await message.answer("❌ خطا در ارتباط با جیمینای!")

# ========================================
# ========================================
# 📨 ارسال بنر به آیدی‌ها
# ========================================
# ========================================
@router.message(lambda m: m.text == "📨 ارسال بنر به آیدی‌ها" and m.from_user.id == ADMIN_ID)
async def send_banner_to_ids_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_banner_ids"}
    await message.answer(
        "📨 **ارسال بنر به آیدی‌ها**\n\n"
        "لیست آیدی‌ها رو بفرست (با کاما یا خط جدید جدا کن):\n"
        "مثال: `123456789, 987654321, 111222333`"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_ids")
async def get_banner_ids(message: types.Message):
    ids_text = message.text
    ids = []
    for part in ids_text.replace(",", " ").split():
        try:
            ids.append(int(part))
        except:
            pass
    unique_ids = []
    duplicates = []
    for i in ids:
        if i in unique_ids:
            duplicates.append(i)
        else:
            unique_ids.append(i)
    if duplicates:
        await message.answer(
            f"⚠️ **آیدی‌های تکراری:** {', '.join(map(str, duplicates))}\n\n"
            f"اگه میخوای بهشون هم پیام بدی، بگو «بله»"
        )
        user_states[message.from_user.id] = {"state": "waiting_duplicate_decision", "ids": unique_ids, "duplicates": duplicates}
        return
    user_states[message.from_user.id] = {"state": "waiting_banner_content", "ids": unique_ids}
    await message.answer(f"✅ {len(unique_ids)} آیدی معتبر دریافت شد.\n\n📝 حالا بنر رو بفرست")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_duplicate_decision")
async def handle_duplicate_decision(message: types.Message):
    data = user_states[message.from_user.id]
    if message.text == "بله":
        all_ids = data.get("ids") + data.get("duplicates")
        user_states[message.from_user.id] = {"state": "waiting_banner_content", "ids": all_ids}
        await message.answer(f"✅ {len(all_ids)} آیدی (با تکراری‌ها) دریافت شد.\n\n📝 حالا بنر رو بفرست.")
    else:
        user_states[message.from_user.id] = {"state": "waiting_banner_content", "ids": data.get("ids")}
        await message.answer(f"✅ {len(data.get('ids'))} آیدی بدون تکراری دریافت شد.\n\n📝 حالا بنر رو بفرست.")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner_content")
async def send_banner_to_ids(message: types.Message):
    ids = user_states[message.from_user.id].get("ids", [])
    success = 0
    failed = []
    for user_id in ids:
        try:
            if message.text:
                await message.bot.send_message(user_id, message.text)
            elif message.photo:
                await message.bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
            elif message.video:
                await message.bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
            elif message.document:
                await message.bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
            success += 1
        except:
            failed.append(user_id)
    user_states[message.from_user.id] = {}
    result = f"✅ **نتیجه ارسال:**\n\n📤 موفق: {success} نفر\n"
    if failed:
        result += f"❌ ناموفق: {len(failed)} نفر\nآیدی‌های ناموفق: {', '.join(map(str, failed))}"
    else:
        result += "🎉 همه پیام‌ها با موفقیت ارسال شدند!"
    await message.answer(result)

# ========================================
# ========================================
# 🔐 رمز فایل
# ========================================
# ========================================
@router.message(lambda m: m.text == "🔐 رمز فایل" and m.from_user.id == ADMIN_ID)
async def manage_password_files(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن فایل با رمز", callback_data="add_password_file")],
        [InlineKeyboardButton(text="📋 لیست فایل‌های رمزدار", callback_data="list_password_files")],
        [InlineKeyboardButton(text="🗑 حذف فایل رمزدار", callback_data="delete_password_file")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("🔐 **سیستم رمز فایل**\n\nبا این بخش می‌تونی فایل‌ها رو با رمز محافظت کنی.", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_password_file")
async def add_password_file_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_pw_name"}
    await call.message.edit_text("📝 **نام فایل رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_pw_name")
async def get_pw_name(message: types.Message):
    user_states[message.from_user.id]["pw_name"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_pw_code"
    await message.answer("🔑 **رمز فایل رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_pw_code")
async def get_pw_code(message: types.Message):
    user_states[message.from_user.id]["pw_code"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_pw_file"
    await message.answer("📄 **حالا فایل رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_pw_file" and (m.document or m.photo or m.video))
async def save_password_file(message: types.Message):
    data = user_states[message.from_user.id]
    name = data.get("pw_name")
    code = data.get("pw_code")
    
    if message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    else:
        await message.answer("❌ نوع فایل پشتیبانی نمیشه!")
        return
    
    add_password_file(name, code, file_id, file_type, message.caption or "")
    user_states[message.from_user.id] = {}
    add_admin_activity(message.from_user.id, "افزودن فایل رمزدار", f"نام: {name}")
    await message.answer(f"✅ **فایل با رمز ذخیره شد!**\n\n📝 نام: {name}\n🔑 رمز: `{code}`")

@router.callback_query(lambda c: c.data == "list_password_files")
async def list_password_files(call: types.CallbackQuery):
    files = get_all_password_files()
    if not files:
        await call.message.edit_text("❌ هیچ فایل رمز‌داری وجود نداره!")
        return
    text = "🔐 **لیست فایل‌های رمزدار:**\n\n"
    for f in files:
        text += f"• {f[1]} (رمز: `{f[2]}`) - {f[3]}\n"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_password_file")
async def delete_password_file_start(call: types.CallbackQuery):
    files = get_all_password_files()
    if not files:
        await call.message.edit_text("❌ هیچ فایل رمز‌داری وجود نداره!")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {f[1]}", callback_data=f"del_pw_{f[0]}")] for f in files
    ] + [[InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]])
    await call.message.edit_text("🗑 **فایل رو برای حذف انتخاب کن:**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("del_pw_"))
async def delete_password_file_confirm(call: types.CallbackQuery):
    file_id = int(call.data.replace("del_pw_", ""))
    delete_password_file(file_id)
    add_admin_activity(call.from_user.id, "حذف فایل رمزدار")
    await call.message.edit_text("✅ فایل رمزدار حذف شد!")

# ========================================
# ========================================
# 📝 نظرات و پیشنهادات
# ========================================
# ========================================
@router.message(lambda m: m.text == "📝 نظرات و پیشنهادات" and m.from_user.id == ADMIN_ID)
async def view_feedback_panel(message: types.Message):
    feedbacks = get_all_feedback()
    if not feedbacks:
        await message.answer("❌ هیچ نظر یا پیشنهادی ثبت نشده!")
        return
    text = "📝 **نظرات و پیشنهادات:**\n\n"
    for f in feedbacks[:10]:
        text += f"• از {f[1]}:\n{f[2]}\n{f[3]}\n---\n"
    if len(feedbacks) > 10:
        text += f"\n... و {len(feedbacks) - 10} نظر دیگه"
    await message.answer(text)

# ========================================
# ========================================
# 📋 بروزرسانی‌ها
# ========================================
# ========================================
@router.message(lambda m: m.text == "📋 بروزرسانی‌ها" and m.from_user.id == ADMIN_ID)
async def updates_panel(message: types.Message):
    updates = get_all_updates()
    if not updates:
        await message.answer("❌ هیچ بروزرسانی ثبت نشده!")
        return
    text = "📋 **بروزرسانی‌ها:**\n\n"
    for u in updates[:10]:
        text += f"• {u[1]}\n{u[2]}\n---\n"
    if len(updates) > 10:
        text += f"\n... و {len(updates) - 10} بروزرسانی دیگه"
    await message.answer(text)

# ========================================
# ========================================
# 📤 ارسال همگانی
# ========================================
# ========================================
@router.message(lambda m: m.text == "📤 ارسال همگانی" and m.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_broadcast"}
    await message.answer("📤 **ارسال همگانی**\n\n📝 پیام رو بفرست تا به همه کاربران ارسال بشه.")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_broadcast")
async def broadcast_confirm(message: types.Message):
    users = get_all_users()
    if not users:
        await message.answer("❌ هیچ کاربری وجود نداره!")
        user_states[message.from_user.id] = {}
        return
    await message.answer(f"📤 ارسال به {len(users)} کاربر شروع شد...")
    success = 0
    for user_id, username, full_name in users:
        try:
            await message.bot.send_message(user_id, message.text)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer(f"✅ پیام به {success} کاربر ارسال شد!")
    user_states[message.from_user.id] = {}

# ========================================
# ========================================
# 💾 بکاپ و بازیابی
# ========================================
# ========================================
@router.message(lambda m: m.text == "💾 بکاپ و بازیابی" and m.from_user.id == ADMIN_ID)
async def backup_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💾 گرفتن بکاپ", callback_data="backup_db")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("💾 **مدیریت بکاپ**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "backup_db")
async def backup_db_callback(call: types.CallbackQuery):
    result = backup_db()
    if result:
        await call.message.edit_text("✅ **بکاپ با موفقیت گرفته شد!**")
    else:
        await call.message.edit_text("❌ خطا در گرفتن بکاپ!")

# ========================================
# ========================================
# 🔙 برگشت به پنل
# ========================================
# ========================================
@router.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚙️ **پنل مدیریت**\n\n"
        "📊 از دکمه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
    )

# ========================================
# ========================================
# ===== توابع جیمینای =====
# ========================================
# ========================================
async def get_gemini_summary(file_id):
    try:
        text = "این متن نمونه از کتاب است."
        if not text:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"این متن کتاب را به زبان فارسی خلاصه کن. خلاصه حداکثر ۱۰ خط باشد:\n\n{text[:5000]}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return None
    except:
        return None

async def get_gemini_analysis(file_id):
    try:
        text = "این متن نمونه از کتاب است."
        if not text:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"""کتاب زیر را به زبان فارسی تحلیل کن:\n\n{text[:5000]}"""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return None
    except:
        return None

async def get_gemini_response(prompt, personality_prompt=""):
    try:
        if not GEMINI_API_KEY:
            return "❌ کلید جیمینای تنظیم نشده!"
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
