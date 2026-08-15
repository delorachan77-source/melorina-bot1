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

# =========================================================
# تنظیمات
# =========================================================

user_states = {}

BOOKS_PER_PAGE = 8
USERS_PER_PAGE = 10


# =========================================================
# سیستم ادمین
# =========================================================

def is_admin(user_id: int) -> bool:
    """
    بررسی ادمین بودن کاربر.
    اگر ADMIN_IDS در config وجود داشته باشد، از آن استفاده می‌شود.
    در غیر این صورت ADMIN_ID استفاده می‌شود.
    """

    try:
        from config import ADMIN_IDS

        if isinstance(ADMIN_IDS, (list, tuple, set)):
            return user_id in ADMIN_IDS

    except ImportError:
        pass

    return user_id == ADMIN_ID


def clear_state(user_id: int):
    user_states[user_id] = {}


def set_state(user_id: int, state: str, **data):
    user_states[user_id] = {
        "state": state,
        **data
    }


def get_state(user_id: int):
    return user_states.get(user_id, {})


def log_admin(admin_id, action, details=""):
    try:
        add_admin_activity(
            admin_id,
            action,
            details
        )
    except Exception as e:
        print("Admin log error:", e)


# =========================================================
# کیبورد اصلی
# =========================================================

def get_admin_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 مدیریت کتاب‌ها"),
                KeyboardButton(text="📢 مدیریت کانال‌ها")
            ],
            [
                KeyboardButton(text="🎨 مدیریت بنر"),
                KeyboardButton(text="👀 دیدن بنر")
            ],
            [
                KeyboardButton(text="👀 پنل عضویت"),
                KeyboardButton(text="👥 مدیریت کاربران")
            ],
            [
                KeyboardButton(text="📊 آمار پیشرفته"),
                KeyboardButton(text="🤖 هوش مصنوعی")
            ],
            [
                KeyboardButton(text="📨 ارسال بنر به آیدی‌ها"),
                KeyboardButton(text="📤 ارسال همگانی")
            ],
            [
                KeyboardButton(text="💾 بکاپ و بازیابی"),
                KeyboardButton(text="🔐 رمز فایل")
            ],
            [
                KeyboardButton(text="⚙️ تنظیمات"),
                KeyboardButton(text="📝 فعالیت ادمین")
            ],
            [
                KeyboardButton(text="🔙 بستن پنل")
            ]
        ],
        resize_keyboard=True
    )


# =========================================================
# پنل اصلی
# =========================================================

@router.message(Command("panel"))
async def panel(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "OPEN_PANEL",
        "پنل مدیریت باز شد"
    )

    await message.answer(
        "⚙️ **پنل مدیریت پیشرفته**\n\n"
        "📊 از گزینه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
    )


# =========================================================
# لغو عملیات
# =========================================================

@router.message(Command("cancel"))
async def cancel_operation(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    state = get_state(message.from_user.id)

    if state:
        clear_state(message.from_user.id)

        await message.answer(
            "✅ عملیات لغو شد.",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer("ℹ️ عملیاتی در حال اجرا نیست.")


# =========================================================
# بستن پنل
# =========================================================

@router.message(
    lambda m:
    m.text == "🔙 بستن پنل"
    and is_admin(m.from_user.id)
)
async def close_panel(message: types.Message):

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "CLOSE_PANEL",
        "پنل بسته شد"
    )

    await message.answer(
        "✅ پنل مدیریت بسته شد.",
        reply_markup=types.ReplyKeyboardRemove()
    )


# =========================================================
# 📚 مدیریت کتاب‌ها
# =========================================================

@router.message(
    lambda m:
    m.text == "📚 مدیریت کتاب‌ها"
    and is_admin(m.from_user.id)
)
async def manage_books(message: types.Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن کتاب",
                    callback_data="add_book"
                ),
                InlineKeyboardButton(
                    text="📋 لیست کتاب‌ها",
                    callback_data="list_books_0"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ ویرایش کتاب",
                    callback_data="edit_book"
                ),
                InlineKeyboardButton(
                    text="🗑 حذف کتاب",
                    callback_data="delete_book"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 جستجوی کتاب",
                    callback_data="search_book"
                ),
                InlineKeyboardButton(
                    text="📂 بر اساس ژانر",
                    callback_data="genre_books"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 محبوب‌ترین‌ها",
                    callback_data="popular_books"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await message.answer(
        "📚 **مدیریت کتاب‌ها**\n\n"
        "از گزینه موردنظر استفاده کن:",
        reply_markup=keyboard
    )


# =========================================================
# ➕ افزودن کتاب
# =========================================================

@router.callback_query(lambda c: c.data == "add_book")
async def add_book_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        await call.answer("⛔ دسترسی ندارید.", show_alert=True)
        return

    set_state(
        call.from_user.id,
        "waiting_title"
    )

    await call.message.edit_text(
        "📝 **عنوان کتاب را بفرست:**\n\n"
        "برای لغو /cancel"
    )

    await call.answer()


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_title"
)
async def get_title(message: types.Message):

    if not message.text:
        await message.answer("❌ لطفاً عنوان را به صورت متن بفرست.")
        return

    user_states[message.from_user.id]["title"] = message.text.strip()
    user_states[message.from_user.id]["state"] = "waiting_author"

    await message.answer(
        "✍️ **نویسنده را بفرست:**\n"
        "اختیاری است؛ برای رد شدن `/skip`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_author"
)
async def get_author(message: types.Message):

    user_states[message.from_user.id]["author"] = (
        "" if message.text == "/skip"
        else message.text.strip()
    )

    user_states[message.from_user.id]["state"] = "waiting_genre"

    await message.answer(
        "📂 **ژانر کتاب را بفرست:**\n"
        "اختیاری؛ برای رد شدن `/skip`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_genre"
)
async def get_genre(message: types.Message):

    user_states[message.from_user.id]["genre"] = (
        "" if message.text == "/skip"
        else message.text.strip()
    )

    user_states[message.from_user.id]["state"] = "waiting_description"

    await message.answer(
        "📝 **توضیحات کتاب را بفرست:**\n"
        "اختیاری؛ برای رد شدن `/skip`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_description"
)
async def get_description(message: types.Message):

    user_states[message.from_user.id]["description"] = (
        "" if message.text == "/skip"
        else message.text.strip()
    )

    user_states[message.from_user.id]["state"] = "waiting_cover"

    await message.answer(
        "🖼 **جلد کتاب را بفرست:**\n"
        "عکس ارسال کن یا `/skip`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_cover"
)
async def get_cover(message: types.Message):

    if message.text == "/skip":

        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_file"

        await message.answer(
            "📄 **حالا فایل کتاب را بفرست.**\n"
            "PDF / ZIP / EPUB و..."
        )

        return

    if message.photo:

        user_states[message.from_user.id]["cover"] = (
            message.photo[-1].file_id
        )

        user_states[message.from_user.id]["state"] = "waiting_file"

        await message.answer(
            "📄 **حالا فایل کتاب را بفرست.**"
        )

    else:

        await message.answer(
            "❌ لطفاً عکس جلد بفرست یا `/skip` بزن."
        )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and m.document
    and get_state(m.from_user.id).get("state") == "waiting_file"
)
async def get_file(message: types.Message):

    data = user_states[message.from_user.id]

    book_id = add_book(
        title=data.get("title", ""),
        author=data.get("author", ""),
        description=data.get("description", ""),
        genre=data.get("genre", ""),
        cover_file_id=data.get("cover", ""),
        file_id=message.document.file_id,
        file_name=message.document.file_name or "",
        file_size=message.document.file_size or 0
    )

    title = data.get("title", "")

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "ADD_BOOK",
        f"book_id={book_id}, title={title}"
    )

    await message.answer(
        f"✅ **کتاب با موفقیت اضافه شد!**\n\n"
        f"📖 {title}\n"
        f"🆔 ID: `{book_id}`"
    )


# =========================================================
# 📋 لیست کتاب‌ها + صفحه‌بندی
# =========================================================

@router.callback_query(
    lambda c: c.data.startswith("list_books_")
)
async def list_books(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        await call.answer("⛔ دسترسی ندارید.", show_alert=True)
        return

    page = int(call.data.split("_")[-1])

    books = get_all_books()

    if not books:
        await call.message.edit_text(
            "❌ هیچ کتابی ثبت نشده."
        )
        return

    total = len(books)
    start = page * BOOKS_PER_PAGE
    end = start + BOOKS_PER_PAGE

    current = books[start:end]

    text = (
        f"📚 **لیست کتاب‌ها**\n"
        f"صفحه {page + 1} از "
        f"{max(1, (total + BOOKS_PER_PAGE - 1) // BOOKS_PER_PAGE)}\n\n"
    )

    for book in current:

        text += (
            f"🆔 `{book[0]}`\n"
            f"📖 {book[1]}\n"
            f"📥 دانلود: {book[8]}\n\n"
        )

    buttons = []

    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ قبلی",
                callback_data=f"list_books_{page - 1}"
            )
        )

    if end < total:
        buttons.append(
            InlineKeyboardButton(
                text="بعدی ➡️",
                callback_data=f"list_books_{page + 1}"
            )
        )

    keyboard_rows = []

    if buttons:
        keyboard_rows.append(buttons)

    keyboard_rows.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_books"
        )
    ])

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard_rows
        )
    )

    await call.answer()


# =========================================================
# ✏️ ویرایش کتاب
# =========================================================

@router.callback_query(lambda c: c.data == "edit_book")
async def edit_book_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_edit_id"
    )

    await call.message.edit_text(
        "✏️ **ویرایش کتاب**\n\n"
        "🆔 آیدی کتاب را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_edit_id"
)
async def edit_book_id(message: types.Message):

    try:
        book_id = int(message.text)
    except:
        await message.answer("❌ آیدی باید عدد باشد.")
        return

    book = get_book(book_id)

    if not book:
        await message.answer("❌ کتاب پیدا نشد.")
        return

    user_states[message.from_user.id] = {
        "state": "waiting_edit_field",
        "book_id": book_id
    }

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 عنوان",
                    callback_data="edit_field_title"
                ),
                InlineKeyboardButton(
                    text="✍️ نویسنده",
                    callback_data="edit_field_author"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 ژانر",
                    callback_data="edit_field_genre"
                ),
                InlineKeyboardButton(
                    text="📝 توضیحات",
                    callback_data="edit_field_description"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🖼 جلد",
                    callback_data="edit_field_cover"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 لغو",
                    callback_data="back_to_books"
                )
            ]
        ]
    )

    await message.answer(
        f"✏️ **ویرایش:** {book[1]}\n\n"
        "کدام قسمت را می‌خواهی تغییر بدهی؟",
        reply_markup=keyboard
    )


@router.callback_query(
    lambda c: c.data.startswith("edit_field_")
)
async def edit_field(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    field = call.data.replace(
        "edit_field_",
        ""
    )

    state = get_state(call.from_user.id)

    if not state.get("book_id"):
        await call.answer(
            "❌ عملیات منقضی شده.",
            show_alert=True
        )
        return

    user_states[call.from_user.id]["edit_field"] = field
    user_states[call.from_user.id]["state"] = "waiting_edit_value"

    messages = {
        "title": "📖 عنوان جدید را بفرست:",
        "author": "✍️ نویسنده جدید را بفرست:",
        "genre": "📂 ژانر جدید را بفرست:",
        "description": "📝 توضیحات جدید را بفرست:",
        "cover": "🖼 عکس جلد جدید را بفرست:"
    }

    await call.message.edit_text(
        messages.get(
            field,
            "مقدار جدید را بفرست:"
        )
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_edit_value"
)
async def edit_value(message: types.Message):

    state = get_state(message.from_user.id)

    book_id = state.get("book_id")
    field = state.get("edit_field")

    book = get_book(book_id)

    if not book:
        clear_state(message.from_user.id)
        await message.answer("❌ کتاب پیدا نشد.")
        return

    value = None

    if field == "cover":

        if not message.photo:
            await message.answer(
                "❌ لطفاً عکس ارسال کن."
            )
            return

        value = message.photo[-1].file_id

    else:

        if not message.text:
            await message.answer(
                "❌ لطفاً متن ارسال کن."
            )
            return

        value = message.text

    allowed_fields = {
        "title": "title",
        "author": "author",
        "genre": "genre",
        "description": "description",
        "cover": "cover_file_id"
    }

    db_field = allowed_fields.get(field)

    if not db_field:
        clear_state(message.from_user.id)
        return

    try:

        c.execute(
            f"UPDATE books SET {db_field}=? WHERE id=?",
            (value, book_id)
        )

        db.commit()

        log_admin(
            message.from_user.id,
            "EDIT_BOOK",
            f"book_id={book_id}, field={field}"
        )

        await message.answer(
            "✅ اطلاعات کتاب با موفقیت ویرایش شد."
        )

    except Exception as e:

        await message.answer(
            f"❌ خطا در ویرایش:\n{str(e)[:300]}"
        )

    clear_state(message.from_user.id)


# =========================================================
# 🗑 حذف کتاب
# =========================================================

@router.callback_query(lambda c: c.data == "delete_book")
async def delete_book_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_delete"
    )

    await call.message.edit_text(
        "🗑 **حذف کتاب**\n\n"
        "آیدی کتاب را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_delete"
)
async def delete_book_confirm(message: types.Message):

    try:
        book_id = int(message.text)
    except:
        await message.answer("❌ آیدی نامعتبر.")
        return

    book = get_book(book_id)

    if not book:
        await message.answer("❌ کتاب پیدا نشد.")
        clear_state(message.from_user.id)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ بله، حذف شود",
                    callback_data=f"confirm_delete_book_{book_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data="back_to_books"
                )
            ]
        ]
    )

    await message.answer(
        f"⚠️ آیا مطمئنی کتاب زیر حذف شود؟\n\n"
        f"📖 **{book[1]}**\n"
        f"🆔 `{book_id}`",
        reply_markup=keyboard
    )


@router.callback_query(
    lambda c: c.data.startswith("confirm_delete_book_")
)
async def confirm_delete_book(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    book_id = int(
        call.data.replace(
            "confirm_delete_book_",
            ""
        )
    )

    book = get_book(book_id)

    if book:
        delete_book(book_id)

        log_admin(
            call.from_user.id,
            "DELETE_BOOK",
            f"book_id={book_id}, title={book[1]}"
        )

        await call.message.edit_text(
            f"✅ کتاب **{book[1]}** حذف شد."
        )
    else:
        await call.message.edit_text(
            "❌ کتاب پیدا نشد."
        )

    clear_state(call.from_user.id)


# =========================================================
# 🔍 جستجو
# =========================================================

@router.callback_query(lambda c: c.data == "search_book")
async def search_book_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_search"
    )

    await call.message.edit_text(
        "🔍 عبارت جستجو را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_search"
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

    text = (
        f"🔍 **نتایج جستجو:**\n\n"
    )

    for book in results[:15]:

        text += (
            f"🆔 `{book[0]}` | "
            f"📖 {book[1]} | "
            f"📥 {book[8]}\n"
        )

    await message.answer(text)


# =========================================================
# 📂 ژانر
# =========================================================

@router.callback_query(lambda c: c.data == "genre_books")
async def genre_books_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_genre_list"
    )

    await call.message.edit_text(
        "📂 نام ژانر را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_genre_list"
)
async def genre_books_confirm(message: types.Message):

    genre = message.text.strip()

    books = get_books_by_genre(genre)

    clear_state(message.from_user.id)

    if not books:
        await message.answer(
            f"❌ کتابی در ژانر «{genre}» پیدا نشد."
        )
        return

    text = (
        f"📂 **کتاب‌های ژانر {genre}:**\n\n"
    )

    for book in books[:20]:
        text += (
            f"🆔 `{book[0]}` - "
            f"📖 {book[1]}\n"
        )

    await message.answer(text)


# =========================================================
# 🏆 محبوب‌ترین‌ها
# =========================================================

@router.callback_query(lambda c: c.data == "popular_books")
async def popular_books(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    books = get_popular_books(10)

    if not books:
        await call.message.edit_text(
            "❌ کتابی وجود ندارد."
        )
        return

    text = "🏆 **محبوب‌ترین کتاب‌ها:**\n\n"

    for i, book in enumerate(books, 1):

        text += (
            f"{i}. 📖 {book[1]}\n"
            f"   📥 {book[8]} دانلود\n\n"
        )

    await call.message.edit_text(text)


# =========================================================
# 🔗 ساخت لینک کتاب
# =========================================================

@router.callback_query(lambda c: c.data == "book_link")
async def book_link_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_link_book"
    )

    await call.message.edit_text(
        "🔗 آیدی کتاب را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_link_book"
)
async def create_book_link(message: types.Message):

    try:
        book_id = int(message.text)
    except:
        await message.answer("❌ آیدی نامعتبر.")
        return

    book = get_book(book_id)

    if not book:
        await message.answer("❌ کتاب پیدا نشد.")
        clear_state(message.from_user.id)
        return

    # بهتر است BOT_USERNAME را در config قرار دهید.
    try:
        from config import BOT_USERNAME
    except ImportError:
        BOT_USERNAME = ""

    if not BOT_USERNAME:

        await message.answer(
            "⚠️ `BOT_USERNAME` در config تعریف نشده.\n\n"
            "مثال:\n"
            "`BOT_USERNAME = \"YourBot\"`"
        )

        clear_state(message.from_user.id)
        return

    link = (
        f"https://t.me/{BOT_USERNAME}"
        f"?start=book_{book_id}"
    )

    await message.answer(
        f"🔗 **لینک کتاب:**\n\n"
        f"📖 {book[1]}\n"
        f"🆔 `{book_id}`\n\n"
        f"`{link}`"
    )

    clear_state(message.from_user.id)


# =========================================================
# 📢 مدیریت کانال‌ها
# =========================================================

@router.message(
    lambda m:
    m.text == "📢 مدیریت کانال‌ها"
    and is_admin(m.from_user.id)
)
async def manage_channels(message: types.Message):

    channels = get_channels()

    text = "📢 **کانال‌های اجباری:**\n\n"

    if channels:
        for ch in channels:
            text += f"• @{ch}\n"
    else:
        text += "❌ هیچ کانالی وجود ندارد."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن",
                    callback_data="add_channel"
                ),
                InlineKeyboardButton(
                    text="➖ حذف",
                    callback_data="remove_channel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 تازه‌سازی",
                    callback_data="refresh_channels"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "refresh_channels")
async def refresh_channels(call: types.CallbackQuery):

    channels = get_channels()

    text = "📢 **کانال‌های اجباری:**\n\n"

    if channels:
        text += "\n".join(
            f"• @{ch}" for ch in channels
        )
    else:
        text += "❌ هیچ کانالی وجود ندارد."

    await call.message.edit_text(text)
    await call.answer("🔄 بروزرسانی شد.")


@router.callback_query(lambda c: c.data == "add_channel")
async def add_channel_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_channel"
    )

    await call.message.edit_text(
        "📢 نام کانال را بفرست.\n\n"
        "مثال:\n"
        "`mychannel`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_channel"
)
async def add_channel_confirm(message: types.Message):

    ch = message.text.strip().replace("@", "")

    if not ch:
        await message.answer("❌ نام کانال نامعتبر.")
        return

    add_channel(ch)

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "ADD_CHANNEL",
        f"channel=@{ch}"
    )

    await message.answer(
        f"✅ کانال @{ch} اضافه شد.",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(lambda c: c.data == "remove_channel")
async def remove_channel_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    channels = get_channels()

    if not channels:
        await call.message.edit_text(
            "❌ کانالی وجود ندارد."
        )
        return

    buttons = []

    for ch in channels:

        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 @{ch}",
                callback_data=f"delete_channel_{ch}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_panel"
        )
    ])

    await call.message.edit_text(
        "🗑 کانال موردنظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


@router.callback_query(
    lambda c: c.data.startswith("delete_channel_")
)
async def remove_channel_confirm(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    ch = call.data.replace(
        "delete_channel_",
        ""
    )

    delete_channel(ch)

    log_admin(
        call.from_user.id,
        "DELETE_CHANNEL",
        f"channel=@{ch}"
    )

    await call.message.edit_text(
        f"✅ کانال @{ch} حذف شد."
    )


# =========================================================
# 🎨 مدیریت بنر
# =========================================================

@router.message(
    lambda m:
    m.text == "🎨 مدیریت بنر"
    and is_admin(m.from_user.id)
)
async def manage_banner(message: types.Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 تنظیم بنر",
                    callback_data="set_banner"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👀 پیش‌نمایش",
                    callback_data="preview_banner"
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
        ]
    )

    await message.answer(
        "🎨 **مدیریت بنر**",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "set_banner")
async def set_banner_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_banner"
    )

    await call.message.edit_text(
        "🎨 **بنر جدید را بفرست:**\n\n"
        "پشتیبانی:\n"
        "📝 متن\n"
        "🖼 عکس\n"
        "🎥 ویدیو\n"
        "📄 فایل"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_banner"
)
async def set_banner_confirm(message: types.Message):

    if message.text:

        set_banner(
            "text",
            None,
            message.text
        )

        banner_type = "text"

    elif message.photo:

        set_banner(
            "photo",
            message.photo[-1].file_id,
            message.caption or ""
        )

        banner_type = "photo"

    elif message.video:

        set_banner(
            "video",
            message.video.file_id,
            message.caption or ""
        )

        banner_type = "video"

    elif message.document:

        set_banner(
            "document",
            message.document.file_id,
            message.caption or ""
        )

        banner_type = "document"

    else:

        await message.answer(
            "❌ این نوع محتوا پشتیبانی نمی‌شود."
        )
        return

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "SET_BANNER",
        f"type={banner_type}"
    )

    await message.answer(
        "✅ بنر با موفقیت ذخیره شد."
    )


@router.callback_query(lambda c: c.data == "delete_banner")
async def delete_banner_confirm(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    delete_banner()

    log_admin(
        call.from_user.id,
        "DELETE_BANNER"
    )

    await call.message.edit_text(
        "✅ بنر حذف شد."
    )


@router.callback_query(lambda c: c.data == "preview_banner")
async def preview_banner(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    banner = get_banner()

    if banner["type"] == "photo" and banner["file_id"]:

        await call.message.answer_photo(
            banner["file_id"],
            caption=banner["text"]
        )

    elif banner["type"] == "video" and banner["file_id"]:

        await call.message.answer_video(
            banner["file_id"],
            caption=banner["text"]
        )

    elif banner["type"] == "document" and banner["file_id"]:

        await call.message.answer_document(
            banner["file_id"],
            caption=banner["text"]
        )

    else:

        await call.message.answer(
            f"📝 **بنر فعلی:**\n\n"
            f"{banner['text']}"
        )

    await call.answer()


@router.message(
    lambda m:
    m.text == "👀 دیدن بنر"
    and is_admin(m.from_user.id)
)
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

    elif banner["type"] == "document" and banner["file_id"]:

        await message.answer_document(
            banner["file_id"],
            caption=banner["text"]
        )

    else:

        await message.answer(
            f"📝 **بنر فعلی:**\n\n"
            f"{banner['text']}"
        )


# =========================================================
# 👀 پنل عضویت
# =========================================================

@router.message(
    lambda m:
    m.text == "👀 پنل عضویت"
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

        buttons.append([
            InlineKeyboardButton(
                text=f"📢 @{ch}",
                url=f"https://t.me/{ch}"
            )
        ])

    await message.answer(
        "👀 **پنل عضویت اجباری**\n\n"
        "کانال‌های فعلی:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


# =========================================================
# 👥 مدیریت کاربران
# =========================================================

@router.message(
    lambda m:
    m.text == "👥 مدیریت کاربران"
    and is_admin(m.from_user.id)
)
async def manage_users(message: types.Message):

    users = get_all_users()

    text = (
        f"👥 **مدیریت کاربران**\n\n"
        f"📊 تعداد کل: {len(users)} نفر\n\n"
    )

    if users:

        text += "👤 کاربران اخیر:\n\n"

        for user in users[:10]:

            user_id = user[0]
            username = user[1]
            full_name = user[2]
            join_date = user[3]

            text += (
                f"👤 {full_name or 'بدون نام'}\n"
                f"🆔 `{user_id}`\n"
                f"🔹 @{username or 'ندارد'}\n"
                f"📅 {join_date[:10] if join_date else '-'}\n\n"
            )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 جستجوی کاربر",
                    callback_data="search_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 همه کاربران",
                    callback_data="list_users_0"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard
    )


# =========================================================
# 📋 لیست کاربران
# =========================================================

@router.callback_query(
    lambda c: c.data.startswith("list_users_")
)
async def list_users(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    page = int(call.data.split("_")[-1])

    users = get_all_users()

    if not users:
        await call.message.edit_text(
            "❌ کاربری وجود ندارد."
        )
        return

    total = len(users)

    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE

    current = users[start:end]

    text = (
        f"👥 **کاربران**\n"
        f"صفحه {page + 1}\n\n"
    )

    for user in current:

        text += (
            f"👤 {user[2] or 'بدون نام'}\n"
            f"🆔 `{user[0]}`\n"
            f"🔹 @{user[1] or 'ندارد'}\n\n"
        )

    buttons = []

    if page > 0:

        buttons.append(
            InlineKeyboardButton(
                text="⬅️ قبلی",
                callback_data=f"list_users_{page - 1}"
            )
        )

    if end < total:

        buttons.append(
            InlineKeyboardButton(
                text="بعدی ➡️",
                callback_data=f"list_users_{page + 1}"
            )
        )

    rows = []

    if buttons:
        rows.append(buttons)

    rows.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_users"
        )
    ])

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=rows
        )
    )


# =========================================================
# 🔍 جستجوی کاربر
# =========================================================

@router.callback_query(lambda c: c.data == "search_user")
async def search_user_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_user_search"
    )

    await call.message.edit_text(
        "🔍 آیدی یا username کاربر را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_user_search"
)
async def search_user_confirm(message: types.Message):

    query = message.text.strip().replace("@", "")

    users = get_all_users()

    results = []

    for user in users:

        if (
            query in str(user[0])
            or query.lower() in (user[1] or "").lower()
            or query.lower() in (user[2] or "").lower()
        ):
            results.append(user)

    clear_state(message.from_user.id)

    if not results:

        await message.answer(
            "❌ کاربری پیدا نشد."
        )
        return

    text = "🔍 **نتایج:**\n\n"

    for user in results[:20]:

        text += (
            f"👤 {user[2] or 'بدون نام'}\n"
            f"🆔 `{user[0]}`\n"
            f"🔹 @{user[1] or 'ندارد'}\n\n"
        )

    await message.answer(text)


# =========================================================
# 📊 آمار پیشرفته
# =========================================================

@router.message(
    lambda m:
    m.text == "📊 آمار پیشرفته"
    and is_admin(m.from_user.id)
)
async def advanced_stats(message: types.Message):

    books = get_all_books()
    channels = get_channels()
    users = get_all_users()

    total_downloads = sum(
        book[8] or 0
        for book in books
    )

    popular = sorted(
        books,
        key=lambda x: x[8] or 0,
        reverse=True
    )

    top_text = "🏆 **پربازدیدترین‌ها:**\n\n"

    if popular:

        for i, book in enumerate(popular[:5], 1):

            top_text += (
                f"{i}. {book[1]} — "
                f"{book[8] or 0} دانلود\n"
            )

    else:

        top_text += "هنوز کتابی وجود ندارد."

    password_count = len(
        get_all_password_files()
    )

    stats = get_db_stats()

    await message.answer(
        "📊 **آمار پیشرفته ربات**\n\n"
        f"📚 کتاب‌ها: {len(books)}\n"
        f"📥 کل دانلودها: {total_downloads}\n"
        f"👥 کاربران: {len(users)}\n"
        f"📢 کانال‌ها: {len(channels)}\n"
        f"🔐 فایل‌های رمزدار: {password_count}\n\n"
        f"{top_text}"
    )


# =========================================================
# 🤖 پنل هوش مصنوعی
# =========================================================

@router.message(
    lambda m:
    m.text == "🤖 هوش مصنوعی"
    and is_admin(m.from_user.id)
)
async def ai_panel(message: types.Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 خلاصه‌سازی",
                    callback_data="ai_summarize"
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
                    text="💬 چت",
                    callback_data="ai_chat"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await message.answer(
        "🤖 **هوش مصنوعی**\n\n"
        "قابلیت‌های Gemini:",
        reply_markup=keyboard
    )


# =========================================================
# 🤖 چت Gemini
# =========================================================

@router.callback_query(lambda c: c.data == "ai_chat")
async def ai_chat_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_ai_chat"
    )

    await call.message.edit_text(
        "💬 **چت با Gemini**\n\n"
        "پیامت را بفرست.\n"
        "برای خروج `/cancel`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_ai_chat"
)
async def ai_chat_response(message: types.Message):

    if not GEMINI_API_KEY:

        await message.answer(
            "❌ GEMINI_API_KEY تنظیم نشده."
        )
        return

    if not message.text:
        await message.answer(
            "❌ فقط پیام متنی ارسال کن."
        )
        return

    await message.answer(
        "🤔 در حال دریافت پاسخ..."
    )

    response = await get_gemini_response(
        message.text
    )

    if response:
        await message.answer(response)
    else:
        await message.answer(
            "❌ خطا در ارتباط با Gemini."
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

    set_state(
        message.from_user.id,
        "waiting_banner_ids"
    )

    await message.answer(
        "📨 **ارسال به آیدی‌ها**\n\n"
        "آیدی‌ها را با کاما یا فاصله بفرست.\n\n"
        "مثال:\n"
        "`123456789, 987654321`"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_banner_ids"
)
async def get_banner_ids(message: types.Message):

    ids = []

    parts = (
        message.text
        .replace(",", " ")
        .replace("\n", " ")
        .split()
    )

    for part in parts:

        try:
            user_id = int(part)

            if user_id not in ids:
                ids.append(user_id)

        except:
            pass

    if not ids:

        await message.answer(
            "❌ هیچ آیدی معتبر پیدا نشد."
        )
        return

    user_states[message.from_user.id] = {
        "state": "waiting_banner_content",
        "ids": ids
    }

    await message.answer(
        f"✅ {len(ids)} آیدی دریافت شد.\n\n"
        "📨 حالا محتوا را بفرست:\n"
        "متن / عکس / ویدیو / فایل"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_banner_content"
)
async def send_banner_to_ids(message: types.Message):

    data = get_state(message.from_user.id)

    ids = data.get("ids", [])

    success = 0
    failed = []

    for user_id in ids:

        try:

            if message.text:

                await message.bot.send_message(
                    user_id,
                    message.text
                )

            elif message.photo:

                await message.bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption or ""
                )

            elif message.video:

                await message.bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=message.caption or ""
                )

            elif message.document:

                await message.bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption or ""
                )

            else:

                failed.append(user_id)
                continue

            success += 1

            await asyncio.sleep(0.05)

        except Exception:

            failed.append(user_id)

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "SEND_TO_IDS",
        f"success={success}, failed={len(failed)}"
    )

    text = (
        "📨 **نتیجه ارسال**\n\n"
        f"✅ موفق: {success}\n"
        f"❌ ناموفق: {len(failed)}"
    )

    await message.answer(text)


# =========================================================
# 📤 Broadcast
# =========================================================

@router.message(
    lambda m:
    m.text == "📤 ارسال همگانی"
    and is_admin(m.from_user.id)
)
async def broadcast_start(message: types.Message):

    set_state(
        message.from_user.id,
        "waiting_broadcast"
    )

    await message.answer(
        "📤 **ارسال همگانی**\n\n"
        "متن، عکس، ویدیو یا فایل را بفرست."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_broadcast"
)
async def broadcast_confirm(message: types.Message):

    users = get_all_users()

    if not users:

        await message.answer(
            "❌ هیچ کاربری وجود ندارد."
        )

        clear_state(message.from_user.id)
        return

    await message.answer(
        f"📤 شروع ارسال به {len(users)} کاربر..."
    )

    success = 0
    failed = 0

    for user in users:

        user_id = user[0]

        try:

            if message.text:

                await message.bot.send_message(
                    user_id,
                    message.text
                )

            elif message.photo:

                await message.bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption=message.caption or ""
                )

            elif message.video:

                await message.bot.send_video(
                    user_id,
                    message.video.file_id,
                    caption=message.caption or ""
                )

            elif message.document:

                await message.bot.send_document(
                    user_id,
                    message.document.file_id,
                    caption=message.caption or ""
                )

            else:

                failed += 1
                continue

            success += 1

            await asyncio.sleep(0.05)

        except Exception:

            failed += 1

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "BROADCAST",
        f"success={success}, failed={failed}"
    )

    await message.answer(
        "📤 **Broadcast تمام شد.**\n\n"
        f"✅ موفق: {success}\n"
        f"❌ ناموفق: {failed}"
    )


# =========================================================
# 🔐 فایل رمزدار
# =========================================================

@router.message(
    lambda m:
    m.text == "🔐 رمز فایل"
    and is_admin(m.from_user.id)
)
async def manage_password_files(message: types.Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن",
                    callback_data="add_password_file"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 لیست",
                    callback_data="list_password_files"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 حذف",
                    callback_data="delete_password_file"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await message.answer(
        "🔐 **مدیریت فایل‌های رمزدار**",
        reply_markup=keyboard
    )


@router.callback_query(
    lambda c: c.data == "add_password_file"
)
async def add_password_file_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    set_state(
        call.from_user.id,
        "waiting_pw_name"
    )

    await call.message.edit_text(
        "📝 نام فایل را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_pw_name"
)
async def get_pw_name(message: types.Message):

    user_states[message.from_user.id]["pw_name"] = (
        message.text.strip()
    )

    user_states[message.from_user.id]["state"] = (
        "waiting_pw_code"
    )

    await message.answer(
        "🔑 رمز فایل را بفرست:"
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_pw_code"
)
async def get_pw_code(message: types.Message):

    code = message.text.strip()

    existing = get_password_file_by_code(code)

    if existing:

        await message.answer(
            "❌ این رمز قبلاً استفاده شده.\n"
            "یک رمز دیگر انتخاب کن."
        )
        return

    user_states[message.from_user.id]["pw_code"] = code

    user_states[message.from_user.id]["state"] = (
        "waiting_pw_file"
    )

    await message.answer(
        "📄 حالا فایل را بفرست."
    )


@router.message(
    lambda m:
    is_admin(m.from_user.id)
    and get_state(m.from_user.id).get("state") == "waiting_pw_file"
    and (m.document or m.photo or m.video)
)
async def save_password_file(message: types.Message):

    data = get_state(message.from_user.id)

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

        await message.answer(
            "❌ نوع فایل پشتیبانی نمی‌شود."
        )
        return

    add_password_file(
        name,
        code,
        file_id,
        file_type,
        message.caption or ""
    )

    clear_state(message.from_user.id)

    log_admin(
        message.from_user.id,
        "ADD_PASSWORD_FILE",
        f"name={name}"
    )

    await message.answer(
        "✅ **فایل رمزدار ذخیره شد.**\n\n"
        f"📝 نام: {name}\n"
        f"🔑 رمز: `{code}`"
    )


@router.callback_query(
    lambda c: c.data == "list_password_files"
)
async def list_password_files(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    files = get_all_password_files()

    if not files:

        await call.message.edit_text(
            "❌ هیچ فایل رمز‌داری وجود ندارد."
        )
        return

    text = "🔐 **فایل‌های رمزدار:**\n\n"

    for f in files:

        text += (
            f"🆔 `{f[0]}`\n"
            f"📄 {f[1]}\n"
            f"🔑 `{f[2]}`\n"
            f"📂 {f[3]}\n\n"
        )

    await call.message.edit_text(text)


@router.callback_query(
    lambda c: c.data == "delete_password_file"
)
async def delete_password_file_start(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    files = get_all_password_files()

    if not files:

        await call.message.edit_text(
            "❌ فایلی وجود ندارد."
        )
        return

    buttons = []

    for f in files:

        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {f[1]}",
                callback_data=f"del_pw_{f[0]}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_to_panel"
        )
    ])

    await call.message.edit_text(
        "🗑 فایل را برای حذف انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


@router.callback_query(
    lambda c: c.data.startswith("del_pw_")
)
async def delete_password_file_confirm(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    file_id = int(
        call.data.replace(
            "del_pw_",
            ""
        )
    )

    delete_password_file(file_id)

    log_admin(
        call.from_user.id,
        "DELETE_PASSWORD_FILE",
        f"id={file_id}"
    )

    await call.message.edit_text(
        "✅ فایل رمزدار حذف شد."
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
                    callback_data="backup_db"
                )
            ],
            [
                InlineKeyboardButton(
                    text="♻️ بازیابی بکاپ",
                    callback_data="restore_db"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 وضعیت دیتابیس",
                    callback_data="db_status"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await message.answer(
        "💾 **بکاپ و بازیابی دیتابیس**",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "backup_db")
async def backup_db_callback(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    result = backup_db()

    if result:

        log_admin(
            call.from_user.id,
            "BACKUP_DATABASE"
        )

        await call.message.edit_text(
            "✅ بکاپ با موفقیت گرفته شد."
        )

    else:

        await call.message.edit_text(
            "❌ گرفتن بکاپ ناموفق بود."
        )


@router.callback_query(lambda c: c.data == "restore_db")
async def restore_db_callback(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ بله، بازیابی کن",
                    callback_data="confirm_restore_db"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await call.message.edit_text(
        "⚠️ **هشدار**\n\n"
        "بازیابی بکاپ اطلاعات فعلی دیتابیس را "
        "با نسخه بکاپ جایگزین می‌کند.\n\n"
        "ادامه می‌دهی؟",
        reply_markup=keyboard
    )


@router.callback_query(
    lambda c: c.data == "confirm_restore_db"
)
async def confirm_restore_db(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    result = restore_db()

    if result:

        log_admin(
            call.from_user.id,
            "RESTORE_DATABASE"
        )

        await call.message.edit_text(
            "✅ بکاپ بازیابی شد.\n\n"
            "⚠️ برای اطمینان بهتر است ربات را restart کنی."
        )

    else:

        await call.message.edit_text(
            "❌ فایل بکاپ پیدا نشد."
        )


@router.callback_query(lambda c: c.data == "db_status")
async def db_status(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    stats = get_db_stats()

    await call.message.edit_text(
        "💾 **وضعیت دیتابیس**\n\n"
        f"📚 کتاب‌ها: {stats['books']}\n"
        f"📢 کانال‌ها: {stats['channels']}\n"
        f"👥 کاربران: {stats['users']}\n"
        f"📥 دانلودها: {stats['total_downloads']}\n"
        f"🔐 فایل‌های رمزدار: {stats['password_files']}"
    )


# =========================================================
# 📝 فعالیت ادمین
# =========================================================

@router.message(
    lambda m:
    m.text == "📝 فعالیت ادمین"
    and is_admin(m.from_user.id)
)
async def admin_activity_panel(message: types.Message):

    activities = get_admin_activities(
        limit=30
    )

    if not activities:

        await message.answer(
            "📝 هنوز فعالیتی ثبت نشده."
        )
        return

    text = "📝 **آخرین فعالیت‌های ادمین:**\n\n"

    for item in activities:

        # چون بدون admin_id پنج مقدار داریم
        activity_id = item[0]
        admin_id = item[1]
        action = item[2]
        details = item[3]
        created_at = item[4]

        text += (
            f"🆔 {activity_id}\n"
            f"👑 `{admin_id}`\n"
            f"⚙️ {action}\n"
            f"📄 {details or '-'}\n"
            f"🕐 {created_at[:19]}\n\n"
        )

    await message.answer(text)


# =========================================================
# ⚙️ تنظیمات
# =========================================================

@router.message(
    lambda m:
    m.text == "⚙️ تنظیمات"
    and is_admin(m.from_user.id)
)
async def settings_panel(message: types.Message):

    stats = get_db_stats()

    await message.answer(
        "⚙️ **تنظیمات ربات**\n\n"
        f"📚 تعداد کتاب: {stats['books']}\n"
        f"👥 کاربران: {stats['users']}\n"
        f"📢 کانال اجباری: {stats['channels']}\n\n"
        "🔧 تنظیمات پیشرفته در نسخه بعدی "
        "می‌تواند از همین بخش کنترل شود."
    )


# =========================================================
# 🔙 برگشت به کتاب‌ها
# =========================================================

@router.callback_query(lambda c: c.data == "back_to_books")
async def back_to_books(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    clear_state(call.from_user.id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ افزودن کتاب",
                    callback_data="add_book"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 لیست",
                    callback_data="list_books_0"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ ویرایش",
                    callback_data="edit_book"
                ),
                InlineKeyboardButton(
                    text="🗑 حذف",
                    callback_data="delete_book"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 جستجو",
                    callback_data="search_book"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 پنل اصلی",
                    callback_data="back_to_panel"
                )
            ]
        ]
    )

    await call.message.edit_text(
        "📚 **مدیریت کتاب‌ها**",
        reply_markup=keyboard
    )


# =========================================================
# 🔙 برگشت به کاربران
# =========================================================

@router.callback_query(lambda c: c.data == "back_to_users")
async def back_to_users(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    clear_state(call.from_user.id)

    await call.message.edit_text(
        "👥 **مدیریت کاربران**\n\n"
        f"تعداد کاربران: {get_user_count()}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 کاربران",
                        callback_data="list_users_0"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔍 جستجو",
                        callback_data="search_user"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 پنل",
                        callback_data="back_to_panel"
                    )
                ]
            ]
        )
    )


# =========================================================
# 🔙 برگشت به پنل اصلی
# =========================================================

@router.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: types.CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    clear_state(call.from_user.id)

    await call.message.edit_text(
        "⚙️ **پنل مدیریت**\n\n"
        "از منوی پایین گزینه موردنظر را انتخاب کن."
    )

    await call.message.answer(
        "📊 منوی مدیریت:",
        reply_markup=get_admin_keyboard()
    )

    await call.answer()


# =========================================================
# 🤖 توابع Gemini
# =========================================================

async def get_gemini_response(prompt):

    if not GEMINI_API_KEY:
        return None

    try:

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-3.5-flash:"
            f"generateContent?key={GEMINI_API_KEY}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text":
                            "به فارسی پاسخ بده. "
                            "پاسخ کوتاه و مفید باشد.\n\n"
                            + prompt
                        }
                    ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:

            async with session.post(
                url,
                json=payload,
                timeout=60
            ) as response:

                if response.status != 200:
                    print(
                        "Gemini status:",
                        response.status
                    )
                    return None

                data = await response.json()

                candidates = data.get(
                    "candidates",
                    []
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

        print(
            "Gemini error:",
            e
        )

        return None


# =========================================================
# پایان
# =========================================================

print("✅ Admin Router با قابلیت‌های جدید بارگذاری شد.")
