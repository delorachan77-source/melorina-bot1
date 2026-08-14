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
            [KeyboardButton(text="📤 ارسال همگانی")],
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
    await message.answer(
        "✅ پنل بسته شد!",
        reply_markup=types.ReplyKeyboardRemove()
    )

# ========================================
# 👀 پنل عضویت اجباری
# ========================================
@router.message(lambda m: m.text == "👀 پنل عضویت" and m.from_user.id == ADMIN_ID)
async def view_join_panel(message: types.Message):
    channels = get_channels()

    if not channels:
        await message.answer(
            "❌ هیچ کانالی برای عضویت اجباری تنظیم نشده!"
        )
        return

    buttons = []

    for ch in channels:
        buttons.append([
            InlineKeyboardButton(
                text="📢 عضویت",
                url=f"https://t.me/{ch}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="✅ عضو شدم",
            callback_data="check_mem_inline"
        )
    ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await message.answer(
        "👀 **پنل عضویت اجباری**\n\n"
        "برای دریافت فایل، در کانال‌های زیر عضو شوید:",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "check_mem_inline")
async def check_mem_inline(call: types.CallbackQuery):
    await call.answer(
        "✅ عضویت تایید شد!",
        show_alert=True
    )

# ========================================
# 📚 مدیریت کتاب‌ها
# ========================================
@router.message(lambda m: m.text == "📚 مدیریت کتاب‌ها" and m.from_user.id == ADMIN_ID)
async def manage_books(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ افزودن کتاب",
                callback_data="add_book"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 لیست کتاب‌ها",
                callback_data="list_books"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 حذف کتاب",
                callback_data="delete_book"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 جستجوی کتاب",
                callback_data="search_book"
            )
        ],
        [
            InlineKeyboardButton(
                text="📂 کتاب‌های یک ژانر",
                callback_data="genre_books"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back_to_panel"
            )
        ]
    ])

    await message.answer(
        "📚 **مدیریت کتاب‌ها**",
        reply_markup=keyboard
    )

# ===== افزودن کتاب =====
@router.callback_query(lambda c: c.data == "add_book")
async def add_book_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    user_states[call.from_user.id] = {
        "state": "waiting_title"
    }

    await call.message.edit_text(
        "📝 **عنوان کتاب رو بفرست:**"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_title")
async def get_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_author"

    await message.answer(
        "✍️ **نویسنده کتاب رو بفرست (اختیاری):**\n"
        "(برای رد شدن /skip بفرست)"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_author")
async def get_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text

    user_states[message.from_user.id]["state"] = "waiting_genre"

    await message.answer(
        "📂 **ژانر کتاب رو بفرست (اختیاری):**\n"
        "(برای رد شدن /skip بفرست)"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_genre")
async def get_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text

    user_states[message.from_user.id]["state"] = "waiting_description"

    await message.answer(
        "📝 **توضیحات کتاب رو بفرست (اختیاری):**\n"
        "(برای رد شدن /skip بفرست)"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_description")
async def get_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text

    user_states[message.from_user.id]["state"] = "waiting_cover"

    await message.answer(
        "🖼 **عکس جلد کتاب رو بفرست (اختیاری):**\n"
        "(برای رد شدن /skip بفرست)"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_cover")
async def get_cover(message: types.Message):

    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_file"

        await message.answer(
            "📄 **حالا فایل کتاب رو بفرست (PDF/ZIP):**"
        )
        return

    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_file"

        await message.answer(
            "📄 **حالا فایل کتاب رو بفرست (PDF/ZIP):**"
        )
    else:
        await message.answer(
            "❌ لطفاً یک عکس بفرست یا /skip بزن!"
        )


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

    await message.answer(
        f"✅ **کتاب «{data.get('title')}» با موفقیت اضافه شد!**"
    )

# ===== لیست کتاب‌ها =====
@router.callback_query(lambda c: c.data == "list_books")
async def list_books(call: types.CallbackQuery):
    books = get_all_books()

    if not books:
        await call.message.edit_text(
            "❌ هیچ کتابی ثبت نشده!"
        )
        return

    text = "📋 **لیست کتاب‌ها:**\n\n"

    for book in books[:10]:
        text += (
            f"• `{book[0]}` - {book[1]} "
            f"(دانلود: {book[8]})\n"
        )

    if len(books) > 10:
        text += (
            f"\n... و {len(books) - 10} کتاب دیگه"
        )

    await call.message.edit_text(text)

# ===== حذف کتاب =====
@router.callback_query(lambda c: c.data == "delete_book")
async def delete_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_delete"
    }

    await call.message.edit_text(
        "📝 **آیدی کتاب رو برای حذف بفرست:**"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete")
async def delete_book_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)

        if book:
            delete_book(book_id)

            await message.answer(
                f"✅ کتاب «{book[1]}» حذف شد!"
            )
        else:
            await message.answer(
                "❌ کتاب پیدا نشد!"
            )

    except:
        await message.answer(
            "❌ لطفاً یک عدد معتبر بفرست!"
        )

    user_states[message.from_user.id] = {}

# ===== جستجوی کتاب =====
@router.callback_query(lambda c: c.data == "search_book")
async def search_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_search"
    }

    await call.message.edit_text(
        "🔍 **عبارت جستجو رو بفرست:**"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_search")
async def search_book_confirm(message: types.Message):
    query = message.text
    results = search_books(query)

    if not results:
        await message.answer(
            f"❌ نتیجه‌ای برای «{query}» پیدا نشد!"
        )
        return

    text = (
        f"🔍 **نتایج جستجو برای «{query}»:**\n\n"
    )

    for book in results[:5]:
        text += (
            f"• `{book[0]}` - {book[1]} "
            f"(دانلود: {book[8]})\n"
        )

    if len(results) > 5:
        text += (
            f"\n... و {len(results) - 5} نتیجه دیگه"
        )

    await message.answer(text)

    user_states[message.from_user.id] = {}

# ===== کتاب‌های یک ژانر =====
@router.callback_query(lambda c: c.data == "genre_books")
async def genre_books_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_genre_list"
    }

    await call.message.edit_text(
        "📂 **نام ژانر رو بفرست:**"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_genre_list")
async def genre_books_confirm(message: types.Message):
    genre = message.text
    books = get_books_by_genre(genre)

    if not books:
        await message.answer(
            f"❌ هیچ کتابی در ژانر «{genre}» پیدا نشد!"
        )
        return

    text = (
        f"📂 **کتاب‌های ژانر «{genre}»:**\n\n"
    )

    for book in books[:10]:
        text += (
            f"• `{book[0]}` - {book[1]}\n"
        )

    if len(books) > 10:
        text += (
            f"\n... و {len(books) - 10} کتاب دیگه"
        )

    await message.answer(text)

    user_states[message.from_user.id] = {}

# ========================================
# 📢 مدیریت کانال‌ها
# ========================================

@router.message(lambda m: m.text == "📢 مدیریت کانال‌ها" and m.from_user.id == ADMIN_ID)
async def manage_channels(message: types.Message):
    channels = get_channels()

    text = "📢 **لیست کانال‌ها:**\n\n"

    text += (
        "\n".join([f"• @{ch}" for ch in channels])
        if channels
        else "❌ هیچ کانالی وجود نداره!"
    )

    await message.answer(text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ افزودن کانال",
                callback_data="add_channel"
            )
        ],
        [
            InlineKeyboardButton(
                text="➖ حذف کانال",
                callback_data="remove_channel"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back_to_panel"
            )
        ]
    ])

    await message.answer(
        "یک گزینه رو انتخاب کن:",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "add_channel")
async def add_channel_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_channel"
    }

    await call.message.edit_text(
        "📢 **نام کانال رو بفرست (بدون @):**"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_channel")
async def add_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")

    add_channel(ch)

    user_states[message.from_user.id] = {}

    await message.answer(
        f"✅ کانال @{ch} اضافه شد!"
    )


@router.callback_query(lambda c: c.data == "remove_channel")
async def remove_channel_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_remove_channel"
    }

    await call.message.edit_text(
        "📢 **نام کانال رو برای حذف بفرست:**"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_remove_channel")
async def remove_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")

    delete_channel(ch)

    user_states[message.from_user.id] = {}

    await message.answer(
        f"✅ کانال @{ch} حذف شد!"
    )

# ========================================
# 🎨 مدیریت بنر + 👀 دیدن بنر
# ========================================

@router.message(lambda m: m.text == "🎨 مدیریت بنر" and m.from_user.id == ADMIN_ID)
async def manage_banner(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 تنظیم بنر",
                callback_data="set_banner"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 حذف بنر",
                callback_data="delete_banner"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back_to_panel"
            )
        ]
    ])

    await message.answer(
        "🎨 **مدیریت بنر**",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "set_banner")
async def set_banner_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_banner"
    }

    await call.message.edit_text(
        "📝 **بنر رو بفرست**\n\n"
        "• متن\n"
        "• عکس\n"
        "• ویدیو"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_banner")
async def set_banner_confirm(message: types.Message):

    if message.text:
        set_banner(
            "text",
            None,
            message.text
        )

        await message.answer(
            "✅ بنر متنی ذخیره شد!"
        )

    elif message.photo:
        set_banner(
            "photo",
            message.photo[-1].file_id,
            message.caption or ""
        )

        await message.answer(
            "✅ بنر عکس ذخیره شد!"
        )

    elif message.video:
        set_banner(
            "video",
            message.video.file_id,
            message.caption or ""
        )

        await message.answer(
            "✅ بنر ویدیو ذخیره شد!"
        )

    else:
        await message.answer(
            "❌ نوع فایل پشتیبانی نمیشه!"
        )
        return

    user_states[message.from_user.id] = {}


@router.callback_query(lambda c: c.data == "delete_banner")
async def delete_banner_confirm(call: types.CallbackQuery):
    delete_banner()

    await call.message.edit_text(
        "✅ بنر حذف شد!"
    )


@router.message(lambda m: m.text == "👀 دیدن بنر" and m.from_user.id == ADMIN_ID)
async def view_banner(message: types.Message):
    banner = get_banner()

    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(
            banner["file_id"],
            caption=banner["text"]
        )

    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(
            banner["file_id"],
            caption=banner["text"]
        )

    else:
        await message.answer(
            f"📝 **بنر فعلی:**\n\n"
            f"{banner['text']}"
        )

# ========================================
# 👥 مدیریت کاربران
# ========================================

@router.message(lambda m: m.text == "👥 مدیریت کاربران" and m.from_user.id == ADMIN_ID)
async def manage_users(message: types.Message):
    users = get_all_users()
    count = get_user_count()

    text = (
        f"👥 **مدیریت کاربران**\n\n"
        f"📊 تعداد کل کاربران: {count} نفر\n\n"
    )

    if users:
        text += "**۱۰ کاربر اخیر:**\n"

        for user in users[:10]:
            text += (
                f"• {user[1] or 'نامشخص'} - {user[0]}\n"
            )
    else:
        text += "❌ هیچ کاربری ثبت نشده!"

    await message.answer(text)

# ========================================
# 📊 آمار پیشرفته
# ========================================

@router.message(lambda m: m.text == "📊 آمار پیشرفته" and m.from_user.id == ADMIN_ID)
async def advanced_stats(message: types.Message):
    books = get_all_books()
    channels = get_channels()
    users = get_user_count()

    total_downloads = sum(
        book[8] for book in books
    )

    popular = sorted(
        books,
        key=lambda x: x[8],
        reverse=True
    )

    popular_text = ""

    if popular:
        popular_text = (
            f"🏆 **کتاب پرفروش:** "
            f"{popular[0][1]} "
            f"({popular[0][8]} دانلود)"
        )

    await message.answer(
        f"📊 **آمار پیشرفته ربات:**\n\n"
        f"📁 **کتاب‌ها:** {len(books)} تا\n"
        f"📥 **کل دانلودها:** {total_downloads} بار\n"
        f"📢 **کانال‌ها:** {len(channels)} تا\n"
        f"👥 **کاربران:** {users} نفر\n\n"
        f"{popular_text}"
    )

# ========================================
# 🤖 هوش مصنوعی با جیمینای
# ========================================

@router.message(lambda m: m.text == "🤖 هوش مصنوعی" and m.from_user.id == ADMIN_ID)
async def ai_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 خلاصه‌سازی کتاب",
                callback_data="ai_summarize"
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 چت با جیمینای",
                callback_data="ai_chat"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 تحلیل کتاب",
                callback_data="ai_analyze"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back_to_panel"
            )
        ]
    ])

    await message.answer(
        "🤖 **پنل هوش مصنوعی با جیمینای**\n\n"
        "✨ قابلیت‌های پیشرفته:\n"
        "• خلاصه‌سازی هوشمند کتاب‌ها\n"
        "• چت با جیمینای\n"
        "• تحلیل عمیق کتاب‌ها",
        reply_markup=keyboard
    )

# ===== خلاصه‌سازی کتاب با جیمینای =====
@router.callback_query(lambda c: c.data == "ai_summarize")
async def ai_summarize_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_summarize"
    }

    await call.message.edit_text(
        "📝 **آیدی کتاب رو برای خلاصه‌سازی بفرست:**\n\n"
        "🤖 جیمینای خلاصه‌ای حرفه‌ای از کتاب تولید میکنه."
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_summarize")
async def ai_summarize_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)

        if not book:
            await message.answer(
                "❌ کتاب پیدا نشد!"
            )

            user_states[message.from_user.id] = {}
            return

        await message.answer(
            f"🔄 در حال خلاصه‌سازی کتاب "
            f"«{book[1]}» با جیمینای..."
        )

        if not GEMINI_API_KEY:
            await message.answer(
                "❌ کلید جیمینای تنظیم نشده!\n\n"
                "لطفاً GEMINI_API_KEY رو "
                "توی Secrets ریپلیت تنظیم کن."
            )

            user_states[message.from_user.id] = {}
            return

        summary = await get_gemini_summary(
            book[6]
        )

        if summary:
            await message.answer(
                f"📝 **خلاصه کتاب «{book[1]}»:**\n\n"
                f"{summary}\n\n"
                f"🤖 تولید شده توسط Gemini AI"
            )
        else:
            await message.answer(
                "❌ خطا در خلاصه‌سازی!\n"
                "جزئیات خطا در Console ریپلیت ثبت شده."
            )

    except Exception as e:
        await message.answer(
            f"❌ خطا: {str(e)[:500]}"
        )

    user_states[message.from_user.id] = {}

# ===== تحلیل کتاب با جیمینای =====
@router.callback_query(lambda c: c.data == "ai_analyze")
async def ai_analyze_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_analyze"
    }

    await call.message.edit_text(
        "📊 **آیدی کتاب رو برای تحلیل بفرست:**\n\n"
        "🤖 جیمینای تحلیل عمیقی از کتاب انجام میده:\n"
        "• شخصیت‌های اصلی\n"
        "• تم‌های اصلی\n"
        "• سبک نوشتاری\n"
        "• نکات کلیدی"
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_analyze")
async def ai_analyze_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)

        if not book:
            await message.answer(
                "❌ کتاب پیدا نشد!"
            )

            user_states[message.from_user.id] = {}
            return

        await message.answer(
            f"🔄 در حال تحلیل کتاب "
            f"«{book[1]}» با جیمینای..."
        )

        if not GEMINI_API_KEY:
            await message.answer(
                "❌ کلید جیمینای تنظیم نشده!"
            )

            user_states[message.from_user.id] = {}
            return

        analysis = await get_gemini_analysis(
            book[6]
        )

        if analysis:
            await message.answer(
                f"📊 **تحلیل کتاب «{book[1]}»:**\n\n"
                f"{analysis}\n\n"
                f"🤖 تحلیل شده توسط Gemini AI"
            )
        else:
            await message.answer(
                "❌ خطا در تحلیل کتاب!"
            )

    except Exception as e:
        await message.answer(
            f"❌ خطا: {str(e)[:500]}"
        )

    user_states[message.from_user.id] = {}

# ===== چت با جیمینای =====
@router.callback_query(lambda c: c.data == "ai_chat")
async def ai_chat_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_ai_chat"
    }

    await call.message.edit_text(
        "💬 **چت با جیمینای**\n\n"
        "هر چی دوست داری بپرس! جیمینای جواب میده 😊\n"
        "برای بستن /cancel بفرست."
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_ai_chat")
async def ai_chat_response(message: types.Message):

    if message.text == "/cancel":
        user_states[message.from_user.id] = {}

        await message.answer(
            "✅ چت بسته شد!"
        )
        return

    if not GEMINI_API_KEY:
        await message.answer(
            "❌ کلید جیمینای تنظیم نشده!\n\n"
            "لطفاً GEMINI_API_KEY رو "
            "توی Secrets ریپلیت تنظیم کن."
        )
        return

    await message.answer(
        "🤔 دارم از جیمینای میپرسم..."
    )

    response = await get_gemini_response(
        message.text
    )

    if response:
        await message.answer(response)
    else:
        await message.answer(
            "❌ خطا در ارتباط با جیمینای!"
        )

# ========================================
# ===== توابع ارتباط با جیمینای =====
# ========================================

async def get_gemini_summary(file_id):
    """دریافت خلاصه کتاب از جیمینای"""

    try:
        text = await extract_text_from_file(
            file_id
        )

        if not text:
            return None

        # ========================================
        # مدل اصلاح شد
        # ========================================
        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )

        prompt = (
            "این متن کتاب را به زبان فارسی "
            "خلاصه کن. "
            "خلاصه حداکثر ۱۰ خط باشد:\n\n"
            f"{text[:5000]}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(
                    total=60
                )
            ) as response:

                response_text = await response.text()

                try:
                    data = json.loads(
                        response_text
                    )
                except:
                    data = {}

                if response.status == 200:

                    return (
                        data.get(
                            "candidates",
                            [{}]
                        )[0]
                        .get(
                            "content",
                            {}
                        )
                        .get(
                            "parts",
                            [{}]
                        )[0]
                        .get(
                            "text",
                            ""
                        )
                    )

                error = data.get(
                    "error",
                    {}
                )

                error_message = error.get(
                    "message",
                    response_text
                )

                print(
                    f"❌ Gemini Summary Error "
                    f"{response.status}: "
                    f"{error_message}"
                )

                return None

    except Exception as e:

        print(
            f"❌ خطا در خلاصه‌سازی Gemini: {e}"
        )

        return None


async def get_gemini_analysis(file_id):
    """تحلیل کتاب با جیمینای"""

    try:
        text = await extract_text_from_file(
            file_id
        )

        if not text:
            return None

        # ========================================
        # مدل اصلاح شد
        # ========================================
        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )

        prompt = f"""
کتاب زیر را به زبان فارسی تحلیل کن.

۱. شخصیت‌های اصلی
۲. تم‌های اصلی
۳. سبک نوشتاری
۴. نکات کلیدی
۵. پیام اصلی

متن کتاب:

{text[:5000]}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(
                    total=60
                )
            ) as response:

                response_text = await response.text()

                try:
                    data = json.loads(
                        response_text
                    )
                except:
                    data = {}

                if response.status == 200:

                    return (
                        data.get(
                            "candidates",
                            [{}]
                        )[0]
                        .get(
                            "content",
                            {}
                        )
                        .get(
                            "parts",
                            [{}]
                        )[0]
                        .get(
                            "text",
                            ""
                        )
                    )

                error = data.get(
                    "error",
                    {}
                )

                error_message = error.get(
                    "message",
                    response_text
                )

                print(
                    f"❌ Gemini Analysis Error "
                    f"{response.status}: "
                    f"{error_message}"
                )

                return None

    except Exception as e:

        print(
            f"❌ خطا در تحلیل Gemini: {e}"
        )

        return None


async def get_gemini_response(prompt):
    """دریافت پاسخ از جیمینای"""

    try:

        if not GEMINI_API_KEY:

            print(
                "❌ GEMINI_API_KEY تنظیم نشده!"
            )

            return (
                "❌ GEMINI_API_KEY در "
                "Replit تنظیم نشده!"
            )

        # ========================================
        # مدل اصلاح شد
        # ========================================
        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )

        full_prompt = (
            "به فارسی پاسخ بده. "
            "پاسخ‌هات کوتاه و مفید باشه:\n\n"
            f"{prompt}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": full_prompt
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(
                    total=60
                )
            ) as response:

                response_text = await response.text()

                try:
                    data = json.loads(
                        response_text
                    )
                except:
                    data = {}

                # ========================================
                # پاسخ موفق
                # ========================================
                if response.status == 200:

                    candidates = data.get(
                        "candidates",
                        []
                    )

                    if not candidates:

                        print(
                            "❌ Gemini پاسخ خالی داد:"
                        )

                        print(data)

                        return (
                            "❌ جیمینای پاسخ خالی "
                            "برگرداند."
                        )

                    text = (
                        candidates[0]
                        .get(
                            "content",
                            {}
                        )
                        .get(
                            "parts",
                            [{}]
                        )[0]
                        .get(
                            "text",
                            ""
                        )
                    )

                    if text:
                        return text

                    print(
                        f"❌ Gemini متن پاسخ ندارد: "
                        f"{data}"
                    )

                    return (
                        "❌ جیمینای متن پاسخی "
                        "برنگرداند."
                    )

                # ========================================
                # خطای Gemini
                # ========================================
                error = data.get(
                    "error",
                    {}
                )

                error_message = error.get(
                    "message",
                    response_text
                )

                print(
                    f"❌ Gemini Error "
                    f"{response.status}: "
                    f"{error_message}"
                )

                return (
                    f"❌ خطای Gemini\n\n"
                    f"🔢 کد خطا: "
                    f"{response.status}\n\n"
                    f"📄 دلیل:\n"
                    f"{error_message[:1500]}"
                )

    except asyncio.TimeoutError:

        print(
            "❌ درخواست Gemini "
            "بیش از حد طول کشید."
        )

        return (
            "❌ زمان درخواست به Gemini "
            "تمام شد. دوباره امتحان کن."
        )

    except aiohttp.ClientError as e:

        print(
            f"❌ خطای اتصال به Gemini: {e}"
        )

        return (
            "❌ اتصال به سرور Gemini "
            "برقرار نشد.\n\n"
            f"جزئیات: {str(e)[:500]}"
        )

    except Exception as e:

        print(
            f"❌ خطا در ارتباط با Gemini: {e}"
        )

        return (
            "❌ خطای داخلی هنگام ارتباط "
            "با Gemini:\n\n"
            f"{str(e)[:1000]}"
        )


async def extract_text_from_file(file_id):
    """استخراج متن از فایل PDF"""

    try:

        # این قسمت از کد اصلی حفظ شده.
        # فعلاً برای تست اتصال Gemini
        # متن نمونه برمی‌گرداند.

        return (
            "این متن نمونه از کتاب است. "
            "برای دریافت متن واقعی، "
            "باید فایل PDF دانلود و "
            "پردازش شود."
        )

    except Exception as e:

        print(
            f"خطا در استخراج متن: {e}"
        )

        return None

# ========================================
# 📤 ارسال همگانی
# ========================================

@router.message(lambda m: m.text == "📤 ارسال همگانی" and m.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message):
    user_states[message.from_user.id] = {
        "state": "waiting_broadcast"
    }

    await message.answer(
        "📤 **ارسال همگانی**\n\n"
        "📝 پیام رو بفرست تا به همه کاربران ارسال بشه."
    )


@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_broadcast")
async def broadcast_confirm(message: types.Message):
    users = get_all_users()

    if not users:

        await message.answer(
            "❌ هیچ کاربری وجود نداره!"
        )

        user_states[message.from_user.id] = {}
        return

    await message.answer(
        f"📤 ارسال به {len(users)} کاربر شروع شد..."
    )

    success = 0

    for user_id, username, full_name in users:

        try:

            await message.bot.send_message(
                user_id,
                message.text
            )

            success += 1

            await asyncio.sleep(0.05)

        except:
            pass

    await message.answer(
        f"✅ پیام به {success} کاربر ارسال شد!"
    )

    user_states[message.from_user.id] = {}

# ========================================
# 💾 بکاپ و بازیابی
# ========================================

@router.message(lambda m: m.text == "💾 بکاپ و بازیابی" and m.from_user.id == ADMIN_ID)
async def backup_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💾 گرفتن بکاپ",
                callback_data="backup_db"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back_to_panel"
            )
        ]
    ])

    await message.answer(
        "💾 **مدیریت بکاپ**",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "backup_db")
async def backup_db_callback(call: types.CallbackQuery):

    result = backup_db()

    if result:

        await call.message.edit_text(
            "✅ **بکاپ با موفقیت گرفته شد!**"
        )

    else:

        await call.message.edit_text(
            "❌ خطا در گرفتن بکاپ!"
        )

# ========================================
# 🔙 برگشت به پنل
# ========================================

@router.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: types.CallbackQuery):

    await call.message.edit_text(
        "⚙️ **پنل مدیریت**\n\n"
        "📊 از دکمه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
)
