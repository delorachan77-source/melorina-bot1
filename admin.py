# admin.py

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import ADMIN_ID, GEMINI_API_KEY
from database import *
import asyncio
import aiohttp
import os
from datetime import datetime

router = Router()

# وضعیت موقت مراحل پنل ادمین
user_states = {}


# =========================================================
# ابزارهای کمکی
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def clear_state(user_id: int):
    user_states[user_id] = {}


def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 مدیریت کتاب‌ها"),
                KeyboardButton(text="📢 مدیریت کانال‌ها"),
            ],
            [
                KeyboardButton(text="🎨 مدیریت بنر"),
                KeyboardButton(text="👀 دیدن بنر"),
            ],
            [
                KeyboardButton(text="👀 پنل عضویت"),
                KeyboardButton(text="👥 مدیریت کاربران"),
            ],
            [
                KeyboardButton(text="📊 آمار پیشرفته"),
                KeyboardButton(text="🤖 هوش مصنوعی"),
            ],
            [
                KeyboardButton(text="📨 ارسال بنر به آیدی‌ها"),
                KeyboardButton(text="📤 ارسال همگانی"),
            ],
            [
                KeyboardButton(text="🔐 رمز فایل"),
                KeyboardButton(text="💾 بکاپ و بازیابی"),
            ],
            [
                KeyboardButton(text="📝 فعالیت ادمین‌ها"),
                KeyboardButton(text="🔙 بستن پنل"),
            ],
        ],
        resize_keyboard=True,
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel",
                )
            ]
        ]
    )


# =========================================================
# پنل اصلی
# =========================================================

@router.message(Command("panel"))
async def panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    clear_state(message.from_user.id)

    await message.answer(
        "⚙️ **پنل مدیریت پیشرفته**\n\n"
        "از منوی زیر بخش موردنظر را انتخاب کن:",
        reply_markup=get_admin_keyboard(),
    )


@router.message(
    lambda m: m.text == "🔙 بستن پنل"
    and is_admin(m.from_user.id)
)
async def close_panel(message: types.Message):
    clear_state(message.from_user.id)

    await message.answer(
        "✅ پنل مدیریت بسته شد.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# =========================================================
# 📚 مدیریت کتاب‌ها
# =========================================================

@router.message(
    lambda m: m.text == "📚 مدیریت کتاب‌ها"
    and is_admin(m.from_user.id)
)
async def manage_books(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن کتاب",
                    callback_data="add_book",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 لیست کتاب‌ها",
                    callback_data="list_books",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 حذف کتاب",
                    callback_data="delete_book",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 جستجوی کتاب",
                    callback_data="search_book",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 کتاب‌های یک ژانر",
                    callback_data="genre_books",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 کتاب‌های محبوب",
                    callback_data="popular_books",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel",
                )
            ],
        ]
    )

    await message.answer(
        "📚 **مدیریت کتاب‌ها**\n\n"
        "یکی از گزینه‌ها را انتخاب کن:",
        reply_markup=keyboard,
    )


# -------------------------
# افزودن کتاب
# -------------------------

@router.callback_query(
    lambda c: c.data == "add_book"
    and is_admin(c.from_user.id)
)
async def add_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_title"
    }

    await call.message.edit_text(
        "📝 **عنوان کتاب را بفرست:**"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_title"
)
async def get_title(message: types.Message):
    if not message.text:
        await message.answer("❌ لطفاً عنوان را به صورت متن بفرست.")
        return

    user_states[message.from_user.id]["title"] = message.text.strip()
    user_states[message.from_user.id]["state"] = "waiting_author"

    await message.answer(
        "✍️ **نویسنده کتاب را بفرست:**\n\n"
        "اختیاری است؛ برای رد کردن `/skip` بفرست."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_author"
)
async def get_author(message: types.Message):
    value = message.text or ""

    if value.strip() == "/skip":
        value = ""

    user_states[message.from_user.id]["author"] = value.strip()
    user_states[message.from_user.id]["state"] = "waiting_genre"

    await message.answer(
        "📂 **ژانر کتاب را بفرست:**\n\n"
        "اختیاری است؛ برای رد کردن `/skip` بفرست."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_genre"
)
async def get_genre(message: types.Message):
    value = message.text or ""

    if value.strip() == "/skip":
        value = ""

    user_states[message.from_user.id]["genre"] = value.strip()
    user_states[message.from_user.id]["state"] = "waiting_description"

    await message.answer(
        "📝 **توضیحات کتاب را بفرست:**\n\n"
        "اختیاری است؛ برای رد کردن `/skip` بفرست."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_description"
)
async def get_description(message: types.Message):
    value = message.text or ""

    if value.strip() == "/skip":
        value = ""

    user_states[message.from_user.id]["description"] = value
    user_states[message.from_user.id]["state"] = "waiting_cover"

    await message.answer(
        "🖼 **جلد کتاب را بفرست:**\n\n"
        "یک عکس ارسال کن یا `/skip` بزن."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_cover"
)
async def get_cover(message: types.Message):
    state = user_states[message.from_user.id]

    if message.text and message.text.strip() == "/skip":
        state["cover"] = ""
        state["state"] = "waiting_file"

        await message.answer(
            "📄 **حالا فایل کتاب را بفرست:**\n\n"
            "PDF، ZIP یا فایل موردنظر."
        )
        return

    if message.photo:
        state["cover"] = message.photo[-1].file_id
        state["state"] = "waiting_file"

        await message.answer(
            "✅ جلد دریافت شد.\n\n"
            "📄 **حالا فایل کتاب را بفرست:**"
        )
        return

    await message.answer(
        "❌ لطفاً عکس جلد بفرست یا `/skip` را ارسال کن."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and m.document
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_file"
)
async def get_book_file(message: types.Message):
    state = user_states[message.from_user.id]

    book_id = add_book(
        title=state.get("title", ""),
        author=state.get("author", ""),
        description=state.get("description", ""),
        genre=state.get("genre", ""),
        cover_file_id=state.get("cover", ""),
        file_id=message.document.file_id,
        file_name=message.document.file_name or "",
        file_size=message.document.file_size or 0,
    )

    add_admin_activity(
        message.from_user.id,
        "add_book",
        f"book_id={book_id}, title={state.get('title', '')}",
    )

    title = state.get("title", "")
    clear_state(message.from_user.id)

    await message.answer(
        f"✅ **کتاب با موفقیت اضافه شد!**\n\n"
        f"📖 عنوان: {title}\n"
        f"🆔 شناسه: `{book_id}`"
    )


# -------------------------
# لیست کتاب‌ها
# -------------------------

@router.callback_query(
    lambda c: c.data == "list_books"
    and is_admin(c.from_user.id)
)
async def list_books(call: types.CallbackQuery):
    books = get_all_books()

    if not books:
        await call.message.edit_text(
            "❌ هیچ کتابی ثبت نشده است.",
            reply_markup=back_keyboard(),
        )
        return

    text = "📋 **لیست کتاب‌ها**\n\n"

    for book in books[:20]:
        text += (
            f"🆔 `{book[0]}`\n"
            f"📖 {book[1]}\n"
            f"📂 ژانر: {book[4] or 'نامشخص'}\n"
            f"📥 دانلود: {book[8]}\n"
            f"━━━━━━━━━━━━\n"
        )

    if len(books) > 20:
        text += f"\n... و {len(books) - 20} کتاب دیگر"

    await call.message.edit_text(
        text,
        reply_markup=back_keyboard(),
    )
    await call.answer()


# -------------------------
# حذف کتاب
# -------------------------

@router.callback_query(
    lambda c: c.data == "delete_book"
    and is_admin(c.from_user.id)
)
async def delete_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_delete_book"
    }

    await call.message.edit_text(
        "🗑 **حذف کتاب**\n\n"
        "آیدی کتاب را بفرست:"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_delete_book"
)
async def delete_book_confirm(message: types.Message):
    try:
        book_id = int(message.text.strip())
    except:
        await message.answer("❌ آیدی باید عدد باشد.")
        return

    book = get_book(book_id)

    if not book:
        await message.answer("❌ کتاب پیدا نشد.")
        clear_state(message.from_user.id)
        return

    delete_book(book_id)

    add_admin_activity(
        message.from_user.id,
        "delete_book",
        f"book_id={book_id}, title={book[1]}",
    )

    clear_state(message.from_user.id)

    await message.answer(
        f"✅ کتاب «{book[1]}» حذف شد."
    )


# -------------------------
# جستجوی کتاب
# -------------------------

@router.callback_query(
    lambda c: c.data == "search_book"
    and is_admin(c.from_user.id)
)
async def search_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_search"
    }

    await call.message.edit_text(
        "🔍 **عبارت جستجو را بفرست:**"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_search"
)
async def search_book_confirm(message: types.Message):
    query = message.text.strip()
    results = search_books(query)

    clear_state(message.from_user.id)

    if not results:
        await message.answer(
            f"❌ نتیجه‌ای برای «{query}» پیدا نشد."
        )
        return

    text = f"🔍 **نتایج جستجو برای:** `{query}`\n\n"

    for book in results[:15]:
        text += (
            f"🆔 `{book[0]}` — {book[1]}\n"
            f"✍️ {book[2] or 'نامشخص'}\n"
            f"📥 {book[8]} دانلود\n\n"
        )

    if len(results) > 15:
        text += f"... و {len(results) - 15} نتیجه دیگر"

    await message.answer(text)


# -------------------------
# ژانر
# -------------------------

@router.callback_query(
    lambda c: c.data == "genre_books"
    and is_admin(c.from_user.id)
)
async def genre_books_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_genre_list"
    }

    await call.message.edit_text(
        "📂 **نام ژانر را بفرست:**"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_genre_list"
)
async def genre_books_confirm(message: types.Message):
    genre = message.text.strip()
    books = get_books_by_genre(genre)

    clear_state(message.from_user.id)

    if not books:
        await message.answer(
            f"❌ کتابی در ژانر «{genre}» وجود ندارد."
        )
        return

    text = f"📂 **کتاب‌های ژانر {genre}:**\n\n"

    for book in books[:20]:
        text += f"🆔 `{book[0]}` — {book[1]}\n"

    await message.answer(text)


# -------------------------
# محبوب‌ترین کتاب‌ها
# -------------------------

@router.callback_query(
    lambda c: c.data == "popular_books"
    and is_admin(c.from_user.id)
)
async def popular_books(call: types.CallbackQuery):
    books = get_popular_books(10)

    if not books:
        await call.message.edit_text(
            "❌ هنوز کتابی وجود ندارد.",
            reply_markup=back_keyboard(),
        )
        return

    text = "🏆 **محبوب‌ترین کتاب‌ها**\n\n"

    for index, book in enumerate(books, 1):
        text += (
            f"{index}. 📖 {book[1]}\n"
            f"   📥 {book[8]} دانلود\n\n"
        )

    await call.message.edit_text(
        text,
        reply_markup=back_keyboard(),
    )

    await call.answer()


# =========================================================
# 📢 مدیریت کانال‌ها
# =========================================================

@router.message(
    lambda m: m.text == "📢 مدیریت کانال‌ها"
    and is_admin(m.from_user.id)
)
async def manage_channels(message: types.Message):
    channels = get_channels()

    text = "📢 **کانال‌های عضویت اجباری**\n\n"

    if channels:
        for ch in channels:
            text += f"• @{ch}\n"
    else:
        text += "❌ هیچ کانالی ثبت نشده."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن کانال",
                    callback_data="add_channel",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ حذف کانال",
                    callback_data="remove_channel",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 تازه‌سازی",
                    callback_data="refresh_channels",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel",
                )
            ],
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard,
    )


@router.callback_query(
    lambda c: c.data == "refresh_channels"
    and is_admin(c.from_user.id)
)
async def refresh_channels(call: types.CallbackQuery):
    channels = get_channels()

    text = "📢 **کانال‌های عضویت اجباری**\n\n"

    if channels:
        text += "\n".join(f"• @{ch}" for ch in channels)
    else:
        text += "❌ هیچ کانالی ثبت نشده."

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ افزودن",
                        callback_data="add_channel",
                    ),
                    InlineKeyboardButton(
                        text="➖ حذف",
                        callback_data="remove_channel",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="back_to_panel",
                    )
                ],
            ]
        ),
    )

    await call.answer("🔄 به‌روزرسانی شد.")


@router.callback_query(
    lambda c: c.data == "add_channel"
    and is_admin(c.from_user.id)
)
async def add_channel_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_channel"
    }

    await call.message.edit_text(
        "📢 **نام کانال را بفرست:**\n\n"
        "مثال:\n"
        "`my_channel`\n\n"
        "بدون @"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_channel"
)
async def add_channel_confirm(message: types.Message):
    ch = message.text.strip().replace("@", "")

    if not ch:
        await message.answer("❌ نام کانال نامعتبر است.")
        return

    add_channel(ch)

    add_admin_activity(
        message.from_user.id,
        "add_channel",
        f"channel=@{ch}",
    )

    clear_state(message.from_user.id)

    await message.answer(
        f"✅ کانال @{ch} اضافه شد."
    )


@router.callback_query(
    lambda c: c.data == "remove_channel"
    and is_admin(c.from_user.id)
)
async def remove_channel_start(call: types.CallbackQuery):
    channels = get_channels()

    if not channels:
        await call.message.edit_text(
            "❌ کانالی برای حذف وجود ندارد.",
            reply_markup=back_keyboard(),
        )
        return

    buttons = []

    for ch in channels:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 @{ch}",
                    callback_data=f"remove_ch_{ch}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back_to_panel",
            )
        ]
    )

    await call.message.edit_text(
        "🗑 **کانالی که می‌خواهی حذف شود انتخاب کن:**",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )

    await call.answer()


@router.callback_query(
    lambda c:
    c.data.startswith("remove_ch_")
    and is_admin(c.from_user.id)
)
async def remove_channel_confirm(call: types.CallbackQuery):
    ch = call.data.replace("remove_ch_", "")

    delete_channel(ch)

    add_admin_activity(
        call.from_user.id,
        "delete_channel",
        f"channel=@{ch}",
    )

    await call.message.edit_text(
        f"✅ کانال @{ch} حذف شد.",
        reply_markup=back_keyboard(),
    )

    await call.answer()


# =========================================================
# 👀 پنل عضویت اجباری
# =========================================================

@router.message(
    lambda m: m.text == "👀 پنل عضویت"
    and is_admin(m.from_user.id)
)
async def view_join_panel(message: types.Message):
    channels = get_channels()

    if not channels:
        await message.answer(
            "❌ هیچ کانالی برای عضویت اجباری تنظیم نشده."
        )
        return

    buttons = []

    for ch in channels:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📢 عضویت در @{ch}",
                    url=f"https://t.me/{ch}",
                )
            ]
        )

    await message.answer(
        "🔒 **پنل عضویت اجباری**\n\n"
        "کانال‌های زیر را دنبال کن:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )


# =========================================================
# 🎨 مدیریت بنر
# =========================================================

@router.message(
    lambda m: m.text == "🎨 مدیریت بنر"
    and is_admin(m.from_user.id)
)
async def manage_banner(message: types.Message):
    banner = get_banner()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 تنظیم بنر",
                    callback_data="set_banner",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👀 پیش‌نمایش",
                    callback_data="preview_banner",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 حذف بنر",
                    callback_data="delete_banner",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel",
                )
            ],
        ]
    )

    await message.answer(
        f"🎨 **مدیریت بنر**\n\n"
        f"نوع فعلی: `{banner['type']}`",
        reply_markup=keyboard,
    )


@router.callback_query(
    lambda c: c.data == "set_banner"
    and is_admin(c.from_user.id)
)
async def set_banner_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_banner"
    }

    await call.message.edit_text(
        "🎨 **بنر جدید را بفرست:**\n\n"
        "پشتیبانی:\n"
        "📝 متن\n"
        "🖼 عکس\n"
        "🎬 ویدیو\n"
        "📄 فایل"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_banner"
)
async def set_banner_confirm(message: types.Message):
    if message.text:
        set_banner("text", None, message.text)
        banner_type = "text"

    elif message.photo:
        set_banner(
            "photo",
            message.photo[-1].file_id,
            message.caption or "",
        )
        banner_type = "photo"

    elif message.video:
        set_banner(
            "video",
            message.video.file_id,
            message.caption or "",
        )
        banner_type = "video"

    elif message.document:
        set_banner(
            "document",
            message.document.file_id,
            message.caption or "",
        )
        banner_type = "document"

    else:
        await message.answer(
            "❌ این نوع پیام برای بنر پشتیبانی نمی‌شود."
        )
        return

    add_admin_activity(
        message.from_user.id,
        "set_banner",
        f"type={banner_type}",
    )

    clear_state(message.from_user.id)

    await message.answer(
        "✅ بنر با موفقیت ذخیره شد."
    )


@router.callback_query(
    lambda c: c.data == "preview_banner"
    and is_admin(c.from_user.id)
)
async def preview_banner(call: types.CallbackQuery):
    await send_current_banner(call.message)
    await call.answer()


async def send_current_banner(message: types.Message):
    banner = get_banner()

    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(
            banner["file_id"],
            caption=banner["text"],
        )

    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(
            banner["file_id"],
            caption=banner["text"],
        )

    elif banner["type"] == "document" and banner["file_id"]:
        await message.answer_document(
            banner["file_id"],
            caption=banner["text"],
        )

    else:
        await message.answer(
            f"📝 **بنر فعلی:**\n\n"
            f"{banner['text']}"
        )


@router.message(
    lambda m: m.text == "👀 دیدن بنر"
    and is_admin(m.from_user.id)
)
async def view_banner(message: types.Message):
    await send_current_banner(message)


@router.callback_query(
    lambda c: c.data == "delete_banner"
    and is_admin(c.from_user.id)
)
async def delete_banner_confirm(call: types.CallbackQuery):
    delete_banner()

    add_admin_activity(
        call.from_user.id,
        "delete_banner",
        "",
    )

    await call.message.edit_text(
        "✅ بنر حذف شد.",
        reply_markup=back_keyboard(),
    )

    await call.answer()


# =========================================================
# 👥 مدیریت کاربران
# =========================================================

@router.message(
    lambda m: m.text == "👥 مدیریت کاربران"
    and is_admin(m.from_user.id)
)
async def manage_users(message: types.Message):
    users = get_all_users()

    text = (
        "👥 **مدیریت کاربران**\n\n"
        f"📊 تعداد کاربران: {len(users)}\n\n"
    )

    if users:
        text += "👤 **کاربران اخیر:**\n\n"

        for user in users[:15]:
            user_id = user[0]
            username = user[1]
            full_name = user[2]

            text += (
                f"🆔 `{user_id}`\n"
                f"👤 {full_name or 'نامشخص'}\n"
                f"🔗 @{username if username else 'ندارد'}\n\n"
            )
    else:
        text += "❌ کاربری ثبت نشده."

    await message.answer(text)


# =========================================================
# 📊 آمار پیشرفته
# =========================================================

@router.message(
    lambda m: m.text == "📊 آمار پیشرفته"
    and is_admin(m.from_user.id)
)
async def advanced_stats(message: types.Message):
    stats = get_db_stats()
    popular = get_popular_books(5)

    text = (
        "📊 **آمار پیشرفته ربات**\n\n"
        f"📚 کتاب‌ها: **{stats['books']}**\n"
        f"📥 کل دانلودها: **{stats['total_downloads']}**\n"
        f"👥 کاربران: **{stats['users']}**\n"
        f"📢 کانال‌ها: **{stats['channels']}**\n"
        f"🔐 فایل‌های رمزدار: **{stats['password_files']}**\n\n"
    )

    if popular:
        text += "🏆 **محبوب‌ترین کتاب‌ها:**\n\n"

        for i, book in enumerate(popular, 1):
            text += (
                f"{i}. {book[1]} — "
                f"{book[8]} دانلود\n"
            )

    await message.answer(text)


# =========================================================
# 📝 فعالیت ادمین‌ها
# =========================================================

@router.message(
    lambda m: m.text == "📝 فعالیت ادمین‌ها"
    and is_admin(m.from_user.id)
)
async def admin_activities(message: types.Message):
    activities = get_admin_activities(limit=30)

    if not activities:
        await message.answer(
            "📝 هنوز فعالیتی ثبت نشده."
        )
        return

    text = "📝 **آخرین فعالیت‌های ادمین**\n\n"

    for activity in activities:
        if len(activity) == 4:
            aid, action, details, created = activity
            admin_id = message.from_user.id
        else:
            aid, admin_id, action, details, created = activity

        text += (
            f"🆔 `{aid}`\n"
            f"👤 `{admin_id}`\n"
            f"⚙️ {action}\n"
            f"📌 {details or '-'}\n"
            f"🕐 {created}\n"
            f"━━━━━━━━━━━━\n"
        )

    await message.answer(text)


# =========================================================
# 🔐 فایل‌های رمزدار
# =========================================================

@router.message(
    lambda m: m.text == "🔐 رمز فایل"
    and is_admin(m.from_user.id)
)
async def manage_password_files(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن فایل",
                    callback_data="add_password_file",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 لیست فایل‌ها",
                    callback_data="list_password_files",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 حذف فایل",
                    callback_data="delete_password_file",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel",
                )
            ],
        ]
    )

    await message.answer(
        "🔐 **سیستم فایل‌های رمزدار**\n\n"
        "کاربر با ارسال رمز، فایل مربوطه را دریافت می‌کند.",
        reply_markup=keyboard,
    )


@router.callback_query(
    lambda c:
    c.data == "add_password_file"
    and is_admin(c.from_user.id)
)
async def add_password_file_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_pw_name"
    }

    await call.message.edit_text(
        "📝 **نام فایل را بفرست:**"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_pw_name"
)
async def get_pw_name(message: types.Message):
    user_states[message.from_user.id]["pw_name"] = (
        message.text.strip()
    )
    user_states[message.from_user.id]["state"] = (
        "waiting_pw_code"
    )

    await message.answer(
        "🔑 **رمز فایل را بفرست:**"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_pw_code"
)
async def get_pw_code(message: types.Message):
    code = message.text.strip()

    # جلوگیری از رمز خالی
    if not code:
        await message.answer(
            "❌ رمز نمی‌تواند خالی باشد."
        )
        return

    user_states[message.from_user.id]["pw_code"] = code
    user_states[message.from_user.id]["state"] = (
        "waiting_pw_file"
    )

    await message.answer(
        "📄 **فایل را بفرست:**\n\n"
        "📄 document\n"
        "🖼 photo\n"
        "🎬 video"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_pw_file"
)
async def save_password_file(message: types.Message):
    data = user_states[message.from_user.id]

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
        await message.answer(
            "❌ لطفاً فایل، عکس یا ویدیو ارسال کن."
        )
        return

    file_db_id = add_password_file(
        name=data["pw_name"],
        password=data["pw_code"],
        file_id=file_id,
        file_type=file_type,
        caption=message.caption or "",
    )

    add_admin_activity(
        message.from_user.id,
        "add_password_file",
        f"id={file_db_id}, name={data['pw_name']}",
    )

    name = data["pw_name"]
    code = data["pw_code"]

    clear_state(message.from_user.id)

    await message.answer(
        "✅ **فایل رمزدار ذخیره شد!**\n\n"
        f"📝 نام: {name}\n"
        f"🆔 شناسه: `{file_db_id}`\n"
        f"🔑 رمز: `{code}`\n"
        f"📂 نوع: {file_type}"
    )


@router.callback_query(
    lambda c:
    c.data == "list_password_files"
    and is_admin(c.from_user.id)
)
async def list_password_files(call: types.CallbackQuery):
    files = get_all_password_files()

    if not files:
        await call.message.edit_text(
            "❌ هیچ فایل رمز‌داری وجود ندارد.",
            reply_markup=back_keyboard(),
        )
        return

    text = "🔐 **فایل‌های رمزدار**\n\n"

    for file in files:
        text += (
            f"🆔 `{file[0]}`\n"
            f"📝 {file[1]}\n"
            f"🔑 `{file[2]}`\n"
            f"📂 {file[3]}\n"
            f"━━━━━━━━━━━━\n"
        )

    await call.message.edit_text(
        text,
        reply_markup=back_keyboard(),
    )

    await call.answer()


@router.callback_query(
    lambda c:
    c.data == "delete_password_file"
    and is_admin(c.from_user.id)
)
async def delete_password_file_start(call: types.CallbackQuery):
    files = get_all_password_files()

    if not files:
        await call.message.edit_text(
            "❌ هیچ فایل رمز‌داری وجود ندارد.",
            reply_markup=back_keyboard(),
        )
        return

    buttons = []

    for file in files:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {file[1]}",
                    callback_data=f"del_pw_{file[0]}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back_to_panel",
            )
        ]
    )

    await call.message.edit_text(
        "🗑 **فایل موردنظر را انتخاب کن:**",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )

    await call.answer()


@router.callback_query(
    lambda c:
    c.data.startswith("del_pw_")
    and is_admin(c.from_user.id)
)
async def delete_password_file_confirm(call: types.CallbackQuery):
    try:
        file_db_id = int(
            call.data.replace("del_pw_", "")
        )
    except:
        await call.answer(
            "❌ شناسه نامعتبر.",
            show_alert=True,
        )
        return

    delete_password_file(file_db_id)

    add_admin_activity(
        call.from_user.id,
        "delete_password_file",
        f"id={file_db_id}",
    )

    await call.message.edit_text(
        "✅ فایل رمزدار حذف شد.",
        reply_markup=back_keyboard(),
    )

    await call.answer()


# =========================================================
# 🤖 هوش مصنوعی
# =========================================================

@router.message(
    lambda m: m.text == "🤖 هوش مصنوعی"
    and is_admin(m.from_user.id)
)
async def ai_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 خلاصه‌سازی کتاب",
                    callback_data="ai_summarize",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 تحلیل کتاب",
                    callback_data="ai_analyze",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 چت با Gemini",
                    callback_data="ai_chat",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel",
                )
            ],
        ]
    )

    await message.answer(
        "🤖 **هوش مصنوعی**\n\n"
        "قابلیت‌ها:\n"
        "📝 خلاصه‌سازی\n"
        "📊 تحلیل\n"
        "💬 چت",
        reply_markup=keyboard,
    )


async def gemini_request(prompt):
    if not GEMINI_API_KEY:
        return None

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=60,
            ) as response:

                if response.status != 200:
                    print(
                        "Gemini HTTP:",
                        response.status,
                        await response.text(),
                    )
                    return None

                data = await response.json()

                candidates = data.get(
                    "candidates",
                    [],
                )

                if not candidates:
                    return None

                return (
                    candidates[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )

    except Exception as e:
        print("Gemini error:", e)
        return None


async def get_gemini_response(prompt):
    return await gemini_request(
        "به فارسی پاسخ بده. کوتاه، واضح و مفید پاسخ بده.\n\n"
        + prompt
    )


async def extract_text_from_file(file_id):
    # این تابع عمداً ساده نگه داشته شده.
    # برای PDF واقعی باید فایل از Telegram دانلود و
    # با یک PDF parser مثل pypdf پردازش شود.
    return (
        "متن نمونه برای پردازش هوش مصنوعی. "
        "برای پردازش واقعی PDF باید فایل Telegram "
        "دانلود و متن آن استخراج شود."
    )


async def get_gemini_summary(file_id):
    text = await extract_text_from_file(file_id)

    if not text:
        return None

    return await gemini_request(
        "این متن را به فارسی خلاصه کن. "
        "خلاصه حداکثر ۱۰ خط باشد:\n\n"
        + text[:12000]
    )


async def get_gemini_analysis(file_id):
    text = await extract_text_from_file(file_id)

    if not text:
        return None

    prompt = """
این کتاب را به زبان فارسی تحلیل کن.

۱. شخصیت‌های اصلی
۲. تم‌های اصلی
۳. سبک نوشتاری
۴. نکات کلیدی
۵. پیام اصلی

متن:
""" + text[:12000]

    return await gemini_request(prompt)


@router.callback_query(
    lambda c:
    c.data == "ai_chat"
    and is_admin(c.from_user.id)
)
async def ai_chat_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_ai_chat"
    }

    await call.message.edit_text(
        "💬 **چت با Gemini**\n\n"
        "پیامت را بفرست.\n"
        "برای خروج `/cancel` را بفرست."
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_ai_chat"
)
async def ai_chat_response(message: types.Message):
    if message.text == "/cancel":
        clear_state(message.from_user.id)
        await message.answer("✅ چت بسته شد.")
        return

    if not GEMINI_API_KEY:
        await message.answer(
            "❌ GEMINI_API_KEY تنظیم نشده."
        )
        return

    await message.answer("🤔 در حال دریافت پاسخ...")

    response = await get_gemini_response(
        message.text or ""
    )

    if response:
        await message.answer(response)
    else:
        await message.answer(
            "❌ خطا در ارتباط با Gemini."
        )


@router.callback_query(
    lambda c:
    c.data == "ai_summarize"
    and is_admin(c.from_user.id)
)
async def ai_summarize_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_summarize"
    }

    await call.message.edit_text(
        "📝 **آیدی کتاب را بفرست:**"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_summarize"
)
async def ai_summarize_confirm(message: types.Message):
    try:
        book_id = int(message.text.strip())
    except:
        await message.answer("❌ آیدی نامعتبر.")
        clear_state(message.from_user.id)
        return

    book = get_book(book_id)

    if not book:
        await message.answer("❌ کتاب پیدا نشد.")
        clear_state(message.from_user.id)
        return

    if not GEMINI_API_KEY:
        await message.answer(
            "❌ GEMINI_API_KEY تنظیم نشده."
        )
        clear_state(message.from_user.id)
        return

    await message.answer(
        f"🔄 در حال خلاصه‌سازی «{book[1]}»..."
    )

    result = await get_gemini_summary(book[6])

    clear_state(message.from_user.id)

    if result:
        await message.answer(
            f"📝 **خلاصه «{book[1]}»**\n\n"
            f"{result}"
        )
    else:
        await message.answer(
            "❌ خلاصه‌سازی انجام نشد."
        )


@router.callback_query(
    lambda c:
    c.data == "ai_analyze"
    and is_admin(c.from_user.id)
)
async def ai_analyze_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {
        "state": "waiting_analyze"
    }

    await call.message.edit_text(
        "📊 **آیدی کتاب را بفرست:**"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_analyze"
)
async def ai_analyze_confirm(message: types.Message):
    try:
        book_id = int(message.text.strip())
    except:
        await message.answer("❌ آیدی نامعتبر.")
        clear_state(message.from_user.id)
        return

    book = get_book(book_id)

    if not book:
        await message.answer("❌ کتاب پیدا نشد.")
        clear_state(message.from_user.id)
        return

    if not GEMINI_API_KEY:
        await message.answer(
            "❌ GEMINI_API_KEY تنظیم نشده."
        )
        clear_state(message.from_user.id)
        return

    await message.answer(
        f"🔄 در حال تحلیل «{book[1]}»..."
    )

    result = await get_gemini_analysis(book[6])

    clear_state(message.from_user.id)

    if result:
        await message.answer(
            f"📊 **تحلیل «{book[1]}»**\n\n"
            f"{result}"
        )
    else:
        await message.answer(
            "❌ تحلیل انجام نشد."
        )


# =========================================================
# 📨 ارسال به آیدی‌های مشخص
# =========================================================

@router.message(
    lambda m:
    m.text == "📨 ارسال بنر به آیدی‌ها"
    and is_admin(m.from_user.id)
)
async def send_banner_to_ids_start(message: types.Message):
    user_states[message.from_user.id] = {
        "state": "waiting_banner_ids"
    }

    await message.answer(
        "📨 **ارسال به آیدی‌های مشخص**\n\n"
        "آیدی‌ها را با کاما یا فاصله وارد کن.\n\n"
        "مثال:\n"
        "`123456789, 987654321`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_banner_ids"
)
async def get_banner_ids(message: types.Message):
    if not message.text:
        await message.answer(
            "❌ آیدی‌ها را به صورت متن بفرست."
        )
        return

    ids = []

    for part in message.text.replace(",", " ").split():
        try:
            user_id = int(part)

            if user_id > 0:
                ids.append(user_id)

        except:
            pass

    if not ids:
        await message.answer(
            "❌ هیچ آیدی معتبر پیدا نشد."
        )
        return

    unique_ids = list(dict.fromkeys(ids))

    duplicates = len(ids) - len(unique_ids)

    user_states[message.from_user.id] = {
        "state": "waiting_banner_content",
        "ids": unique_ids,
    }

    await message.answer(
        f"✅ {len(unique_ids)} آیدی معتبر دریافت شد.\n"
        f"♻️ تکراری حذف‌شده: {duplicates}\n\n"
        "📨 حالا پیام/بنر موردنظر را بفرست."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_banner_content"
)
async def send_banner_to_ids(message: types.Message):
    ids = user_states[message.from_user.id]["ids"]

    success = 0
    failed = []

    for user_id in ids:
        try:
            if message.text:
                await message.bot.send_message(
                    user_id,
                    message.text,
                )

            elif message.photo:
                await message.bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption or "",
                )

            elif message.video:
                await message.bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=message.caption or "",
                )

            elif message.document:
                await message.bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption or "",
                )

            else:
                failed.append(user_id)
                continue

            success += 1
            await asyncio.sleep(0.05)

        except Exception:
            failed.append(user_id)

    add_admin_activity(
        message.from_user.id,
        "send_to_ids",
        f"success={success}, failed={len(failed)}",
    )

    clear_state(message.from_user.id)

    text = (
        "📨 **نتیجه ارسال**\n\n"
        f"✅ موفق: {success}\n"
        f"❌ ناموفق: {len(failed)}"
    )

    if failed:
        text += (
            "\n\nآیدی‌های ناموفق:\n"
            + ", ".join(map(str, failed[:50]))
        )

    await message.answer(text)


# =========================================================
# 📤 ارسال همگانی
# =========================================================

@router.message(
    lambda m:
    m.text == "📤 ارسال همگانی"
    and is_admin(m.from_user.id)
)
async def broadcast_start(message: types.Message):
    user_states[message.from_user.id] = {
        "state": "waiting_broadcast"
    }

    await message.answer(
        "📤 **ارسال همگانی**\n\n"
        "پیام، عکس، ویدیو یا فایل را بفرست."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and user_states.get(m.from_user.id, {}).get("state")
    == "waiting_broadcast"
)
async def broadcast_confirm(message: types.Message):
    users = get_all_users()

    if not users:
        await message.answer(
            "❌ هیچ کاربری ثبت نشده."
        )
        clear_state(message.from_user.id)
        return

    await message.answer(
        f"📤 ارسال به {len(users)} کاربر شروع شد..."
    )

    success = 0
    failed = []

    for user in users:
        user_id = user[0]

        try:
            if message.text:
                await message.bot.send_message(
                    user_id,
                    message.text,
                )

            elif message.photo:
                await message.bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption or "",
                )

            elif message.video:
                await message.bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=message.caption or "",
                )

            elif message.document:
                await message.bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption or "",
                )

            else:
                failed.append(user_id)
                continue

            success += 1
            await asyncio.sleep(0.05)

        except Exception:
            failed.append(user_id)

    add_admin_activity(
        message.from_user.id,
        "broadcast",
        f"success={success}, failed={len(failed)}",
    )

    clear_state(message.from_user.id)

    await message.answer(
        "📤 **نتیجه ارسال همگانی**\n\n"
        f"✅ موفق: {success}\n"
        f"❌ ناموفق: {len(failed)}"
    )


# =========================================================
# 💾 بکاپ و بازیابی
# =========================================================

@router.message(
    lambda m:
    m.text == "💾 بکاپ و بازیابی"
    and is_admin(m.from_user.id)
)
async def backup_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 گرفتن بکاپ",
                    callback_data="backup_db",
                )
            ],
            [
                InlineKeyboardButton(
                    text="♻️ بازیابی بکاپ",
                    callback_data="restore_db",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 وضعیت دیتابیس",
                    callback_data="db_status",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel",
                )
            ],
        ]
    )

    await message.answer(
        "💾 **مدیریت دیتابیس**\n\n"
        "⚠️ قبل از Restore بهتر است ربات Restart شود.",
        reply_markup=keyboard,
    )


@router.callback_query(
    lambda c:
    c.data == "backup_db"
    and is_admin(c.from_user.id)
)
async def backup_db_callback(call: types.CallbackQuery):
    result = backup_db()

    if result:
        add_admin_activity(
            call.from_user.id,
            "backup_database",
            "",
        )

        await call.message.edit_text(
            "✅ **بکاپ با موفقیت ساخته شد.**\n\n"
            f"📁 فایل:\n`{DB_PATH}.backup`",
            reply_markup=back_keyboard(),
        )
    else:
        await call.message.edit_text(
            "❌ دیتابیس برای بکاپ پیدا نشد.",
            reply_markup=back_keyboard(),
        )

    await call.answer()


@router.callback_query(
    lambda c:
    c.data == "restore_db"
    and is_admin(c.from_user.id)
)
async def restore_db_callback(call: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ بله، بازیابی کن",
                    callback_data="confirm_restore",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data="back_to_panel",
                )
            ],
        ]
    )

    await call.message.edit_text(
        "⚠️ **هشدار بازیابی دیتابیس**\n\n"
        "داده‌های فعلی با نسخه بکاپ جایگزین می‌شوند.\n\n"
        "بعد از Restore باید ربات را Restart کنی.\n\n"
        "آیا مطمئنی؟",
        reply_markup=keyboard,
    )

    await call.answer()


@router.callback_query(
    lambda c:
    c.data == "confirm_restore"
    and is_admin(c.from_user.id)
)
async def confirm_restore(call: types.CallbackQuery):
    try:
        result = restore_db()

        if result:
            add_admin_activity(
                call.from_user.id,
                "restore_database",
                "",
            )

            await call.message.edit_text(
                "♻️ **بازیابی انجام شد.**\n\n"
                "⚠️ اتصال دیتابیس باید دوباره ساخته شود؛ "
                "لطفاً ربات را Restart کن.",
                reply_markup=back_keyboard(),
            )
        else:
            await call.message.edit_text(
                "❌ فایل بکاپ پیدا نشد.",
                reply_markup=back_keyboard(),
            )

    except Exception as e:
        await call.message.edit_text(
            f"❌ خطا در بازیابی:\n`{str(e)[:500]}`",
            reply_markup=back_keyboard(),
        )

    await call.answer()


@router.callback_query(
    lambda c:
    c.data == "db_status"
    and is_admin(c.from_user.id)
)
async def db_status(call: types.CallbackQuery):
    stats = get_db_stats()

    await call.message.edit_text(
        "📊 **وضعیت دیتابیس**\n\n"
        f"📚 کتاب‌ها: {stats['books']}\n"
        f"👥 کاربران: {stats['users']}\n"
        f"📢 کانال‌ها: {stats['channels']}\n"
        f"📥 دانلودها: {stats['total_downloads']}\n"
        f"🔐 فایل‌های رمزدار: {stats['password_files']}",
        reply_markup=back_keyboard(),
    )

    await call.answer()


# =========================================================
# 🔙 بازگشت به پنل
# =========================================================

@router.callback_query(
    lambda c:
    c.data == "back_to_panel"
    and is_admin(c.from_user.id)
)
async def back_to_panel(call: types.CallbackQuery):
    clear_state(call.from_user.id)

    await call.message.edit_text(
        "⚙️ **پنل مدیریت**\n\n"
        "برای باز کردن منوی اصلی از `/panel` استفاده کن."
    )

    await call.answer()


# =========================================================
# پایان admin.py
# =========================================================
