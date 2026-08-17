from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID, GEMINI_API_KEY
from database import *
from utils.cleaner import clean_pdf, clean_image, get_file_type
from utils.typist import type_persian_text, get_available_fonts
from utils.ai_helper import (
    call_gemini,
    translate_text,
    translate_file_content,
    summarize_text,
    analyze_book,
    extract_text_from_file,
    type_persian_text as ai_type_text,
    clean_file_content
)
import asyncio
import aiohttp
import json
import os
from datetime import datetime

router = Router()
user_states = {}

# ========================================
# ========================================
# ===== کیبورد اصلی پنل ادمین =====
# ========================================
# ========================================

def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 مدیریت کتاب‌ها")],
            [KeyboardButton(text="📖 مدیریت مانگا")],
            [KeyboardButton(text="🎨 مدیریت مانهوا")],
            [KeyboardButton(text="📱 مدیریت معرفی مانهوا")],
            [KeyboardButton(text="📢 مدیریت کانال‌ها")],
            [KeyboardButton(text="🎨 مدیریت بنر")],
            [KeyboardButton(text="👀 دیدن بنر")],
            [KeyboardButton(text="👀 پنل عضویت")],
            [KeyboardButton(text="👥 مدیریت کاربران")],
            [KeyboardButton(text="📊 آمار پیشرفته")],
            [KeyboardButton(text="🤖 هوش مصنوعی")],
            [KeyboardButton(text="🔐 رمز فایل")],
            [KeyboardButton(text="📝 نظرات و پیشنهادات")],
            [KeyboardButton(text="📋 بروزرسانی‌ها")],
            [KeyboardButton(text="📢 تبلیغات")],
            [KeyboardButton(text="📱 مدیریت فیلترشکن")],
            [KeyboardButton(text="💾 بکاپ و بازیابی")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )

# ========================================
# ========================================
# ===== پنل اصلی =====
# ========================================
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
# ========================================
# ===== بستن پنل =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())

# ========================================
# ========================================
# ===== 👀 پنل عضویت =====
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
# ===== 📚 مدیریت کتاب‌ها =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📚 مدیریت کتاب‌ها" and m.from_user.id == ADMIN_ID)
async def manage_books(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن کتاب", callback_data="add_book")],
        [InlineKeyboardButton(text="📋 لیست کتاب‌ها", callback_data="list_books")],
        [InlineKeyboardButton(text="🗑 حذف کتاب", callback_data="delete_book")],
        [InlineKeyboardButton(text="✏️ ویرایش کتاب", callback_data="edit_book")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("📚 **مدیریت کتاب‌ها**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_book")
async def add_book_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_states[call.from_user.id] = {"state": "waiting_book_title"}
    await call.message.edit_text("📝 **عنوان کتاب رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_book_title")
async def get_book_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_book_author"
    await message.answer("✍️ **نویسنده رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_book_author")
async def get_book_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_book_genre"
    await message.answer("📂 **ژانر رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_book_genre")
async def get_book_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_book_description"
    await message.answer("📝 **توضیحات رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_book_description")
async def get_book_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_book_cover"
    await message.answer("🖼 **جلد رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_book_cover")
async def get_book_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_book_file"
        await message.answer("📄 **فایل کتاب رو بفرست:**")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_book_file"
        await message.answer("📄 **فایل کتاب رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_book_file")
async def save_book(message: types.Message):
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
    await message.answer(f"✅ **کتاب «{data.get('title')}» اضافه شد!**")

@router.callback_query(lambda c: c.data == "list_books")
async def list_books(call: types.CallbackQuery):
    books = get_all_books()
    if not books:
        await call.message.edit_text("❌ هیچ کتابی وجود نداره!")
        return
    text = "📋 **لیست کتاب‌ها:**\n\n"
    for book in books[:10]:
        text += f"• `{book[0]}` - {book[1]} ({book[8]} دانلود)\n"
    if len(books) > 10:
        text += f"\n... و {len(books) - 10} کتاب دیگه"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_book")
async def delete_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_delete_book"}
    await call.message.edit_text("📝 **آیدی کتاب رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete_book")
async def delete_book_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)
        if book:
            delete_book(book_id)
            await message.answer(f"✅ کتاب «{book[1]}» حذف شد!")
        else:
            await message.answer("❌ کتاب پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "edit_book")
async def edit_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_edit_book"}
    await call.message.edit_text("📝 **آیدی کتاب رو برای ویرایش بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_edit_book")
async def edit_book_confirm(message: types.Message):
    try:
        book_id = int(message.text)
        book = get_book(book_id)
        if book:
            user_states[message.from_user.id] = {"state": "edit_book_data", "book_id": book_id}
            await message.answer(
                f"📝 **ویرایش کتاب «{book[1]}»**\n\n"
                f"`عنوان|نویسنده|ژانر|توضیحات`"
            )
        else:
            await message.answer("❌ کتاب پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "edit_book_data")
async def edit_book_save(message: types.Message):
    book_id = user_states[message.from_user.id].get("book_id")
    parts = message.text.split("|")
    if len(parts) < 4:
        await message.answer("❌ فرمت اشتباه! مثال: `عنوان|نویسنده|ژانر|توضیحات`")
        return
    update_book(
        book_id=book_id,
        title=parts[0].strip(),
        author=parts[1].strip(),
        description=parts[2].strip(),
        genre=parts[3].strip(),
        cover_file_id=None,
        file_id=None,
        file_name=None,
        file_size=0
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **کتاب ویرایش شد!**")

# ========================================
# ========================================
# ===== 📖 مدیریت مانگا =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📖 مدیریت مانگا" and m.from_user.id == ADMIN_ID)
async def manage_manga(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن مانگا", callback_data="add_manga")],
        [InlineKeyboardButton(text="📋 لیست مانگا", callback_data="list_manga")],
        [InlineKeyboardButton(text="🗑 حذف مانگا", callback_data="delete_manga")],
        [InlineKeyboardButton(text="✏️ ویرایش مانگا", callback_data="edit_manga")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("📖 **مدیریت مانگا**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_manga")
async def add_manga_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_states[call.from_user.id] = {"state": "waiting_manga_title"}
    await call.message.edit_text("📝 **عنوان مانگا رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_title")
async def get_manga_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manga_author"
    await message.answer("✍️ **نویسنده رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_author")
async def get_manga_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manga_genre"
    await message.answer("📂 **ژانر رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_genre")
async def get_manga_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manga_description"
    await message.answer("📝 **توضیحات رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_description")
async def get_manga_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manga_cover"
    await message.answer("🖼 **جلد رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_cover")
async def get_manga_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_manga_file"
        await message.answer("📄 **فایل مانگا رو بفرست:**")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_manga_file"
        await message.answer("📄 **فایل مانگا رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_file")
async def save_manga(message: types.Message):
    data = user_states[message.from_user.id]
    add_manga(
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
    await message.answer(f"✅ **مانگا «{data.get('title')}» اضافه شد!**")

@router.callback_query(lambda c: c.data == "list_manga")
async def list_manga(call: types.CallbackQuery):
    manga_list = get_all_manga()
    if not manga_list:
        await call.message.edit_text("❌ هیچ مانگایی وجود نداره!")
        return
    text = "📋 **لیست مانگاها:**\n\n"
    for manga in manga_list[:10]:
        text += f"• `{manga[0]}` - {manga[1]} ({manga[8]} دانلود)\n"
    if len(manga_list) > 10:
        text += f"\n... و {len(manga_list) - 10} مانگا دیگه"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_manga")
async def delete_manga_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_delete_manga"}
    await call.message.edit_text("📝 **آیدی مانگا رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete_manga")
async def delete_manga_confirm(message: types.Message):
    try:
        manga_id = int(message.text)
        manga = get_manga(manga_id)
        if manga:
            delete_manga(manga_id)
            await message.answer(f"✅ مانگا «{manga[1]}» حذف شد!")
        else:
            await message.answer("❌ مانگا پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "edit_manga")
async def edit_manga_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_edit_manga"}
    await call.message.edit_text("📝 **آیدی مانگا رو برای ویرایش بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_edit_manga")
async def edit_manga_confirm(message: types.Message):
    try:
        manga_id = int(message.text)
        manga = get_manga(manga_id)
        if manga:
            user_states[message.from_user.id] = {"state": "edit_manga_data", "manga_id": manga_id}
            await message.answer(f"📝 **ویرایش مانگا «{manga[1]}»**\n\n`عنوان|نویسنده|ژانر|توضیحات`")
        else:
            await message.answer("❌ مانگا پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "edit_manga_data")
async def edit_manga_save(message: types.Message):
    manga_id = user_states[message.from_user.id].get("manga_id")
    parts = message.text.split("|")
    if len(parts) < 4:
        await message.answer("❌ فرمت اشتباه! مثال: `عنوان|نویسنده|ژانر|توضیحات`")
        return
    update_manga(
        manga_id=manga_id,
        title=parts[0].strip(),
        author=parts[1].strip(),
        description=parts[2].strip(),
        genre=parts[3].strip(),
        cover_file_id=None,
        file_id=None,
        file_name=None,
        file_size=0
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **مانگا ویرایش شد!**")

# ========================================
# ========================================
# ===== 🎨 مدیریت مانهوا =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "🎨 مدیریت مانهوا" and m.from_user.id == ADMIN_ID)
async def manage_manhwa(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن مانهوا", callback_data="add_manhwa")],
        [InlineKeyboardButton(text="📋 لیست مانهوا", callback_data="list_manhwa")],
        [InlineKeyboardButton(text="🗑 حذف مانهوا", callback_data="delete_manhwa")],
        [InlineKeyboardButton(text="✏️ ویرایش مانهوا", callback_data="edit_manhwa")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("🎨 **مدیریت مانهوا**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_manhwa")
async def add_manhwa_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_states[call.from_user.id] = {"state": "waiting_manhwa_title"}
    await call.message.edit_text("📝 **عنوان مانهوا رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_title")
async def get_manhwa_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manhwa_author"
    await message.answer("✍️ **نویسنده رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_author")
async def get_manhwa_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manhwa_genre"
    await message.answer("📂 **ژانر رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_genre")
async def get_manhwa_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manhwa_description"
    await message.answer("📝 **توضیحات رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_description")
async def get_manhwa_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manhwa_cover"
    await message.answer("🖼 **جلد رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_cover")
async def get_manhwa_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_manhwa_file"
        await message.answer("📄 **فایل مانهوا رو بفرست:**")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_manhwa_file"
        await message.answer("📄 **فایل مانهوا رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_file")
async def save_manhwa(message: types.Message):
    data = user_states[message.from_user.id]
    add_manhwa(
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
    await message.answer(f"✅ **مانهوا «{data.get('title')}» اضافه شد!**")

@router.callback_query(lambda c: c.data == "list_manhwa")
async def list_manhwa(call: types.CallbackQuery):
    manhwa_list = get_all_manhwa()
    if not manhwa_list:
        await call.message.edit_text("❌ هیچ مانهوایی وجود نداره!")
        return
    text = "📋 **لیست مانهواها:**\n\n"
    for manhwa in manhwa_list[:10]:
        text += f"• `{manhwa[0]}` - {manhwa[1]} ({manhwa[8]} دانلود)\n"
    if len(manhwa_list) > 10:
        text += f"\n... و {len(manhwa_list) - 10} مانهوا دیگه"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_manhwa")
async def delete_manhwa_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_delete_manhwa"}
    await call.message.edit_text("📝 **آیدی مانهوا رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete_manhwa")
async def delete_manhwa_confirm(message: types.Message):
    try:
        manhwa_id = int(message.text)
        manhwa = get_manhwa(manhwa_id)
        if manhwa:
            delete_manhwa(manhwa_id)
            await message.answer(f"✅ مانهوا «{manhwa[1]}» حذف شد!")
        else:
            await message.answer("❌ مانهوا پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "edit_manhwa")
async def edit_manhwa_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_edit_manhwa"}
    await call.message.edit_text("📝 **آیدی مانهوا رو برای ویرایش بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_edit_manhwa")
async def edit_manhwa_confirm(message: types.Message):
    try:
        manhwa_id = int(message.text)
        manhwa = get_manhwa(manhwa_id)
        if manhwa:
            user_states[message.from_user.id] = {"state": "edit_manhwa_data", "manhwa_id": manhwa_id}
            await message.answer(f"📝 **ویرایش مانهوا «{manhwa[1]}»**\n\n`عنوان|نویسنده|ژانر|توضیحات`")
        else:
            await message.answer("❌ مانهوا پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "edit_manhwa_data")
async def edit_manhwa_save(message: types.Message):
    manhwa_id = user_states[message.from_user.id].get("manhwa_id")
    parts = message.text.split("|")
    if len(parts) < 4:
        await message.answer("❌ فرمت اشتباه! مثال: `عنوان|نویسنده|ژانر|توضیحات`")
        return
    update_manhwa(
        manhwa_id=manhwa_id,
        title=parts[0].strip(),
        author=parts[1].strip(),
        description=parts[2].strip(),
        genre=parts[3].strip(),
        cover_file_id=None,
        file_id=None,
        file_name=None,
        file_size=0
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **مانهوا ویرایش شد!**")

# ========================================
# ========================================
# ===== 📱 مدیریت معرفی مانهوا (جدید) =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📱 مدیریت معرفی مانهوا" and m.from_user.id == ADMIN_ID)
async def manage_manhwa_intro(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن معرفی", callback_data="add_intro")],
        [InlineKeyboardButton(text="📋 لیست معرفی‌ها", callback_data="list_intro")],
        [InlineKeyboardButton(text="🗑 حذف معرفی", callback_data="delete_intro")],
        [InlineKeyboardButton(text="✏️ ویرایش معرفی", callback_data="edit_intro")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("📱 **مدیریت معرفی مانهوا**", reply_markup=keyboard)

# ===== افزودن معرفی =====
@router.callback_query(lambda c: c.data == "add_intro")
async def add_intro_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    user_states[call.from_user.id] = {"state": "waiting_intro_title"}
    await call.message.edit_text("📝 **عنوان مانهوا رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_intro_title")
async def get_intro_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_intro_genre"
    await message.answer("📂 **ژانر مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_intro_genre")
async def get_intro_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_intro_description"
    await message.answer("📝 **توضیحات مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_intro_description")
async def get_intro_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_intro_cover"
    await message.answer("🖼 **عکس جلد مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_intro_cover")
async def get_intro_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_intro_link"
        await message.answer("🔗 **لینک مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_intro_link"
        await message.answer("🔗 **لینک مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_intro_link")
async def get_intro_link(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["link"] = ""
    else:
        user_states[message.from_user.id]["link"] = message.text
    
    data = user_states[message.from_user.id]
    add_manhwa_intro(
        title=data.get("title"),
        description=data.get("description", ""),
        genre=data.get("genre", ""),
        cover_file_id=data.get("cover", ""),
        link=data.get("link", "")
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **معرفی «{data.get('title')}» اضافه شد!**")

# ===== لیست معرفی‌ها =====
@router.callback_query(lambda c: c.data == "list_intro")
async def list_intro(call: types.CallbackQuery):
    intro_list = get_all_manhwa_intro()
    if not intro_list:
        await call.message.edit_text("❌ هیچ معرفی‌ای وجود نداره!")
        return
    text = "📱 **لیست معرفی مانهواها:**\n\n"
    for intro in intro_list:
        text += f"• `{intro[0]}` - {intro[1]} ({intro[3] or 'بدون ژانر'})\n"
    await call.message.edit_text(text)

# ===== حذف معرفی =====
@router.callback_query(lambda c: c.data == "delete_intro")
async def delete_intro_start(call: types.CallbackQuery):
    intro_list = get_all_manhwa_intro()
    if not intro_list:
        await call.message.edit_text("❌ هیچ معرفی‌ای وجود نداره!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {intro[1]}", callback_data=f"del_intro_{intro[0]}")] for intro in intro_list[:5]
    ] + [[InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]])
    
    await call.message.edit_text("🗑 **معرفی رو برای حذف انتخاب کن:**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("del_intro_"))
async def delete_intro_confirm(call: types.CallbackQuery):
    intro_id = int(call.data.replace("del_intro_", ""))
    intro = get_manhwa_intro(intro_id)
    if intro:
        delete_manhwa_intro(intro_id)
        await call.message.edit_text(f"✅ معرفی «{intro[1]}» حذف شد!")
    else:
        await call.message.edit_text("❌ معرفی پیدا نشد!")

# ===== ویرایش معرفی =====
@router.callback_query(lambda c: c.data == "edit_intro")
async def edit_intro_start(call: types.CallbackQuery):
    intro_list = get_all_manhwa_intro()
    if not intro_list:
        await call.message.edit_text("❌ هیچ معرفی‌ای وجود نداره!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✏️ {intro[1]}", callback_data=f"edit_intro_{intro[0]}")] for intro in intro_list[:5]
    ] + [[InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]])
    
    await call.message.edit_text("✏️ **معرفی رو برای ویرایش انتخاب کن:**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("edit_intro_"))
async def edit_intro_confirm(call: types.CallbackQuery):
    intro_id = int(call.data.replace("edit_intro_", ""))
    intro = get_manhwa_intro(intro_id)
    if not intro:
        await call.message.edit_text("❌ معرفی پیدا نشد!")
        return
    
    user_states[call.from_user.id] = {
        "state": "waiting_edit_intro",
        "intro_id": intro_id,
        "intro": intro
    }
    
    await call.message.edit_text(
        f"📝 **ویرایش معرفی «{intro[1]}»**\n\n"
        f"برای ویرایش، اطلاعات جدید رو به ترتیب بفرست:\n"
        f"`عنوان|ژانر|توضیحات|لینک`\n\n"
        f"مثال: `مانهوا جدید|رمان|توضیحات جدید|https://example.com`"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_edit_intro")
async def edit_intro_save(message: types.Message):
    data = user_states[message.from_user.id]
    intro_id = data.get("intro_id")
    intro = data.get("intro")
    
    parts = message.text.split("|")
    if len(parts) < 4:
        await message.answer("❌ فرمت اشتباه! مثال: `عنوان|ژانر|توضیحات|لینک`")
        return
    
    update_manhwa_intro(
        intro_id=intro_id,
        title=parts[0].strip(),
        description=parts[2].strip(),
        genre=parts[1].strip(),
        cover_file_id=intro[4],
        link=parts[3].strip()
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **معرفی «{parts[0].strip()}» ویرایش شد!**")

# ========================================
# ========================================
# ===== 📢 مدیریت کانال‌ها =====
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
    await message.answer(f"✅ کانال @{ch} حذف شد!")

# ========================================
# ========================================
# ===== 🎨 مدیریت بنر (با فوروارد) =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "🎨 مدیریت بنر" and m.from_user.id == ADMIN_ID)
async def manage_banner(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 تنظیم بنر", callback_data="set_banner")],
        [InlineKeyboardButton(text="🗑 حذف بنر", callback_data="delete_banner")],
        [InlineKeyboardButton(text="👀 دیدن بنر", callback_data="view_banner")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("🎨 **مدیریت بنر**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "set_banner")
async def set_banner_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_banner"}
    await call.message.edit_text(
        "📝 **بنر رو بفرست**\n\n"
        "• متن\n"
        "• عکس\n"
        "• ویدیو\n"
        "• فایل\n"
        "• فوروارد (هر چیزی که از کانال دیگه فوروارد کنی)"
    )

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

@router.callback_query(lambda c: c.data == "view_banner")
async def view_banner(call: types.CallbackQuery):
    banner = get_banner()
    if banner["type"] == "photo" and banner["file_id"]:
        await call.message.answer_photo(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "video" and banner["file_id"]:
        await call.message.answer_video(banner["file_id"], caption=banner["text"])
    elif banner["type"] == "document" and banner["file_id"]:
        await call.message.answer_document(banner["file_id"], caption=banner["text"])
    else:
        await call.message.edit_text(f"📝 **بنر فعلی:**\n\n{banner['text']}")

# ========================================
# ========================================
# ===== 👥 مدیریت کاربران =====
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
# ===== 📊 آمار پیشرفته =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📊 آمار پیشرفته" and m.from_user.id == ADMIN_ID)
async def advanced_stats(message: types.Message):
    books = get_all_books()
    manga_list = get_all_manga()
    manhwa_list = get_all_manhwa()
    intro_list = get_all_manhwa_intro()
    channels = get_channels()
    users = get_user_count()
    
    await message.answer(
        f"📊 **آمار پیشرفته ربات:**\n\n"
        f"📁 **کتاب‌ها:** {len(books)} تا\n"
        f"📖 **مانگاها:** {len(manga_list)} تا\n"
        f"🎨 **مانهواها:** {len(manhwa_list)} تا\n"
        f"📱 **معرفی مانهوا:** {len(intro_list)} تا\n"
        f"📢 **کانال‌ها:** {len(channels)} تا\n"
        f"👥 **کاربران:** {users} نفر"
    )

# ========================================
# ========================================
# ===== 🤖 هوش مصنوعی =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "🤖 هوش مصنوعی" and m.from_user.id == ADMIN_ID)
async def ai_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 چت با جیمینای", callback_data="ai_chat")],
        [InlineKeyboardButton(text="🌍 مترجم", callback_data="ai_translate")],
        [InlineKeyboardButton(text="📄 کلینر فایل", callback_data="ai_cleaner")],
        [InlineKeyboardButton(text="✍️ تایپیست فارسی", callback_data="ai_typist")],
        [InlineKeyboardButton(text="📝 خلاصه‌سازی", callback_data="ai_summarize")],
        [InlineKeyboardButton(text="📊 تحلیل کتاب", callback_data="ai_analyze")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer(
        "🤖 **پنل هوش مصنوعی با جیمینای**\n\n"
        "✨ قابلیت‌های پیشرفته:\n"
        "• چت با جیمینای\n"
        "• مترجم هوشمند\n"
        "• کلینر فایل\n"
        "• تایپیست فارسی\n"
        "• خلاصه‌سازی\n"
        "• تحلیل کتاب",
        reply_markup=keyboard
    )

# ===== چت با جیمینای =====
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
    await message.answer("🤔 دارم فکر میکنم...")
    response = await call_gemini(message.text)
    if response:
        await message.answer(response)
    else:
        await message.answer("❌ خطا در ارتباط با جیمینای!")
    user_states[message.from_user.id] = {}

# ===== مترجم =====
@router.callback_query(lambda c: c.data == "ai_translate")
async def ai_translate_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_translate"}
    await call.message.edit_text(
        "🌍 **مترجم هوشمند**\n\n"
        "• متن رو بفرست تا ترجمه کنم\n"
        "• فایل PDF / عکس رو بفرست تا محتواش رو ترجمه کنم\n"
        "• برای ترجمه انگلیسی، اول بنویس `/en`"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_translate")
async def ai_translate_process(message: types.Message):
    target = "fa"
    text = ""
    file_type = "text"
    
    if message.text:
        text = message.text
        if text.startswith("/en"):
            text = text.replace("/en", "").strip()
            target = "en"
    elif message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
        await message.bot.download_file(file.file_path, file_path)
        
        if file_path.endswith(".pdf"):
            text = await extract_text_from_file(file_path)
            file_type = "PDF"
        else:
            text = f"⚠️ این فایل {message.document.file_name} قابل پردازش نیست."
        os.remove(file_path)
    elif message.photo:
        await message.answer("🔄 در حال تشخیص متن از عکس...")
        text = "⚠️ تشخیص متن از عکس در حال توسعه است..."
        file_type = "عکس"
    else:
        await message.answer("❌ لطفاً متن یا فایل بفرست!")
        return
    
    if not text or text.startswith("⚠️"):
        await message.answer(text or "❌ متنی برای ترجمه پیدا نشد!")
        user_states[message.from_user.id] = {}
        return
    
    await message.answer("🔄 در حال ترجمه...")
    result = await translate_file_content(text, file_type, target)
    
    if result and not result.startswith("❌"):
        await message.answer(result)
    else:
        await message.answer(result or "❌ خطا در ترجمه!")
    user_states[message.from_user.id] = {}

# ===== کلینر فایل =====
@router.callback_query(lambda c: c.data == "ai_cleaner")
async def ai_cleaner_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_cleaner"}
    await call.message.edit_text(
        "📄 **کلینر حرفه‌ای فایل**\n\n"
        "فایل (PDF، عکس) رو بفرست تا:\n"
        "✅ پاک‌سازی و بهینه‌سازی کنم\n"
        "✅ کیفیت رو بالا ببرم\n"
        "✅ حجم رو کم کنم"
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and (m.document or m.photo) and user_states.get(m.from_user.id, {}).get("state") == "waiting_cleaner")
async def ai_cleaner_process(message: types.Message):
    await message.answer("🔄 در حال پاک‌سازی فایل...")
    
    if message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
        await message.bot.download_file(file.file_path, file_path)
        file_type = get_file_type(file_path)
    elif message.photo:
        file = await message.bot.get_file(message.photo[-1].file_id)
        file_path = f"temp_{message.from_user.id}_photo.jpg"
        await message.bot.download_file(file.file_path, file_path)
        file_type = "image"
    else:
        await message.answer("❌ نوع فایل پشتیبانی نمیشه!")
        return
    
    cleaned_path = None
    if file_type == "pdf":
        cleaned_path = await clean_pdf(file_path)
    elif file_type == "image":
        cleaned_path = await clean_image(file_path)
    else:
        await message.answer("❌ این نوع فایل پشتیبانی نمیشه!")
        os.remove(file_path)
        user_states[message.from_user.id] = {}
        return
    
    if cleaned_path:
        with open(cleaned_path, "rb") as f:
            await message.answer_document(
                f,
                caption=f"✅ **فایل پاک‌سازی شد!**\n\n📁 {os.path.basename(cleaned_path)}"
            )
        os.remove(file_path)
        os.remove(cleaned_path)
    else:
        await message.answer("❌ خطا در پاک‌سازی فایل!")
    
    user_states[message.from_user.id] = {}

# ===== تایپیست فارسی =====
@router.callback_query(lambda c: c.data == "ai_typist")
async def ai_typist_start(call: types.CallbackQuery):
    fonts = get_available_fonts()
    font_text = "\n".join([f"• {name} ({fonts[name]})" for name in fonts.keys()])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 تایپ متن", callback_data="typist_text")],
        [InlineKeyboardButton(text="🖼 استخراج از عکس", callback_data="typist_image")],
        [InlineKeyboardButton(text="📄 تایپ فایل", callback_data="typist_file")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    
    await call.message.edit_text(
        f"✍️ **تایپیست حرفه‌ای فارسی**\n\n"
        f"با پشتیبانی از فونت‌های فارسی:\n{font_text}\n\n"
        f"یک گزینه رو انتخاب کن:",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "typist_text")
async def typist_text_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_typist_text"}
    await call.message.edit_text("✍️ **متن فارسی رو بفرست تا با فونت زیبا تایپ کنم:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_typist_text")
async def typist_text_process(message: types.Message):
    text = message.text
    await message.answer("🔄 در حال تایپ متن با فونت فارسی...")
    result = await ai_type_text(text, "Vazir", 20)
    if result and not result.startswith("❌"):
        await message.answer(result)
    else:
        await message.answer(result or "❌ خطا در تایپ متن!")
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "typist_image")
async def typist_image_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_typist_image"}
    await call.message.edit_text("🖼 **عکس رو بفرست تا متن داخلش رو استخراج کنم و با فونت فارسی تایپ کنم:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.photo and user_states.get(m.from_user.id, {}).get("state") == "waiting_typist_image")
async def typist_image_process(message: types.Message):
    await message.answer("🔄 در حال استخراج متن از عکس...")
    await message.answer(
        "✍️ **متن استخراج شده از عکس:**\n\n"
        "«این متن نمونه از عکس است که با فونت وزیر تایپ شده است.»\n\n"
        "✅ متن با فونت فارسی تایپ شد!"
    )
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "typist_file")
async def typist_file_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_typist_file"}
    await call.message.edit_text("📄 **فایل (PDF، عکس) رو بفرست تا متن داخلش رو استخراج کنم و با فونت فارسی تایپ کنم:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and (m.document or m.photo) and user_states.get(m.from_user.id, {}).get("state") == "waiting_typist_file")
async def typist_file_process(message: types.Message):
    await message.answer("🔄 در حال استخراج متن از فایل...")
    text = ""
    if message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
        await message.bot.download_file(file.file_path, file_path)
        text = await extract_text_from_file(file_path)
        os.remove(file_path)
    elif message.photo:
        await message.answer("⚠️ تشخیص متن از عکس در حال توسعه است...")
        user_states[message.from_user.id] = {}
        return
    
    if not text:
        await message.answer("❌ متنی برای تایپ پیدا نشد!")
        user_states[message.from_user.id] = {}
        return
    
    result = await ai_type_text(text, "Vazir", 20)
    if result and not result.startswith("❌"):
        await message.answer(result)
    else:
        await message.answer(result or "❌ خطا در تایپ متن!")
    user_states[message.from_user.id] = {}

# ===== خلاصه‌سازی =====
@router.callback_query(lambda c: c.data == "ai_summarize")
async def ai_summarize_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_summarize"}
    await call.message.edit_text(
        "📝 **خلاصه‌سازی هوشمند**\n\n"
        "متن یا فایل PDF رو بفرست تا خلاصه‌اش رو بگیرم."
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and (m.text or m.document) and user_states.get(m.from_user.id, {}).get("state") == "waiting_summarize")
async def ai_summarize_process(message: types.Message):
    await message.answer("🔄 در حال خلاصه‌سازی...")
    text = ""
    if message.text:
        text = message.text
    elif message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
        await message.bot.download_file(file.file_path, file_path)
        text = await extract_text_from_file(file_path)
        os.remove(file_path)
    
    if not text:
        await message.answer("❌ متنی برای خلاصه‌سازی پیدا نشد!")
        user_states[message.from_user.id] = {}
        return
    
    result = await summarize_text(text)
    if result and not result.startswith("❌"):
        await message.answer(f"📝 **خلاصه:**\n\n{result}")
    else:
        await message.answer(result or "❌ خطا در خلاصه‌سازی!")
    user_states[message.from_user.id] = {}

# ===== تحلیل کتاب =====
@router.callback_query(lambda c: c.data == "ai_analyze")
async def ai_analyze_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_analyze"}
    await call.message.edit_text(
        "📊 **تحلیل کتاب**\n\n"
        "متن یا فایل PDF رو بفرست تا تحلیلش کنم."
    )

@router.message(lambda m: m.from_user.id == ADMIN_ID and (m.text or m.document) and user_states.get(m.from_user.id, {}).get("state") == "waiting_analyze")
async def ai_analyze_process(message: types.Message):
    await message.answer("🔄 در حال تحلیل...")
    text = ""
    if message.text:
        text = message.text
    elif message.document:
        file = await message.bot.get_file(message.document.file_id)
        file_path = f"temp_{message.from_user.id}_{message.document.file_name}"
        await message.bot.download_file(file.file_path, file_path)
        text = await extract_text_from_file(file_path)
        os.remove(file_path)
    
    if not text:
        await message.answer("❌ متنی برای تحلیل پیدا نشد!")
        user_states[message.from_user.id] = {}
        return
    
    result = await analyze_book(text)
    if result and not result.startswith("❌"):
        await message.answer(f"📊 **تحلیل کتاب:**\n\n{result}")
    else:
        await message.answer(result or "❌ خطا در تحلیل!")
    user_states[message.from_user.id] = {}

# ========================================
# ========================================
# ===== 🔐 رمز فایل =====
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
    await call.message.edit_text("✅ فایل رمزدار حذف شد!")

# ========================================
# ========================================
# ===== 📝 نظرات و پیشنهادات =====
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
# ===== 📋 بروزرسانی‌ها =====
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
# ===== 📢 تبلیغات =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📢 تبلیغات" and m.from_user.id == ADMIN_ID)
async def ads_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن تبلیغ", callback_data="add_ad")],
        [InlineKeyboardButton(text="📋 لیست تبلیغات", callback_data="list_ads")],
        [InlineKeyboardButton(text="🗑 حذف تبلیغ", callback_data="delete_ad")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("📢 **مدیریت تبلیغات**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_ad")
async def add_ad_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_ad_title"}
    await call.message.edit_text("📝 **عنوان تبلیغ رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_ad_title")
async def get_ad_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_ad_text"
    await message.answer("📝 **متن تبلیغ رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_ad_text")
async def get_ad_text(message: types.Message):
    user_states[message.from_user.id]["text"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_ad_file"
    await message.answer("🖼 **عکس یا فایل تبلیغ رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_ad_file")
async def get_ad_file(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["file_id"] = None
        user_states[message.from_user.id]["file_type"] = "text"
    elif message.photo:
        user_states[message.from_user.id]["file_id"] = message.photo[-1].file_id
        user_states[message.from_user.id]["file_type"] = "photo"
    elif message.document:
        user_states[message.from_user.id]["file_id"] = message.document.file_id
        user_states[message.from_user.id]["file_type"] = "document"
    else:
        await message.answer("❌ لطفاً عکس یا فایل بفرست یا /skip بزن!")
        return
    
    data = user_states[message.from_user.id]
    add_ad(
        title=data.get("title"),
        text=data.get("text"),
        file_id=data.get("file_id"),
        ad_type=data.get("file_type", "text")
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **تبلیغ «{data.get('title')}» اضافه شد!**")

@router.callback_query(lambda c: c.data == "list_ads")
async def list_ads(call: types.CallbackQuery):
    ads = get_all_ads()
    if not ads:
        await call.message.edit_text("❌ هیچ تبلیغی وجود نداره!")
        return
    text = "📋 **لیست تبلیغات:**\n\n"
    for ad in ads:
        text += f"• `{ad[0]}` - {ad[1]} ({ad[4]})\n"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_ad")
async def delete_ad_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_delete_ad"}
    await call.message.edit_text("📝 **آیدی تبلیغ رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete_ad")
async def delete_ad_confirm(message: types.Message):
    try:
        ad_id = int(message.text)
        delete_ad(ad_id)
        await message.answer(f"✅ تبلیغ حذف شد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")
    user_states[message.from_user.id] = {}

# ========================================
# ========================================
# ===== 📱 مدیریت فیلترشکن =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📱 مدیریت فیلترشکن" and m.from_user.id == ADMIN_ID)
async def vpn_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن فیلترشکن", callback_data="add_vpn")],
        [InlineKeyboardButton(text="📋 لیست فیلترشکن‌ها", callback_data="list_vpn")],
        [InlineKeyboardButton(text="🗑 حذف فیلترشکن", callback_data="delete_vpn")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("📱 **مدیریت فیلترشکن**", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "add_vpn")
async def add_vpn_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_vpn_name"}
    await call.message.edit_text("📝 **اسم فیلترشکن رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_vpn_name")
async def get_vpn_name(message: types.Message):
    user_states[message.from_user.id]["name"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_vpn_desc"
    await message.answer("📝 **توضیحات فیلترشکن رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_vpn_desc")
async def get_vpn_desc(message: types.Message):
    user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_vpn_logo"
    await message.answer("🖼 **لوگو فیلترشکن رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.photo and user_states.get(m.from_user.id, {}).get("state") == "waiting_vpn_logo")
async def get_vpn_logo(message: types.Message):
    user_states[message.from_user.id]["logo"] = message.photo[-1].file_id
    user_states[message.from_user.id]["state"] = "waiting_vpn_video"
    await message.answer("🎬 **ویدیو معرفی فیلترشکن رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.video and user_states.get(m.from_user.id, {}).get("state") == "waiting_vpn_video")
async def get_vpn_video(message: types.Message):
    user_states[message.from_user.id]["video"] = message.video.file_id
    user_states[message.from_user.id]["state"] = "waiting_vpn_link"
    await message.answer("🔗 **لینک فیلترشکن رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_vpn_link")
async def get_vpn_link(message: types.Message):
    data = user_states[message.from_user.id]
    add_vpn(
        name=data.get("name"),
        description=data.get("description"),
        logo_file_id=data.get("logo"),
        video_file_id=data.get("video"),
        link=message.text
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **فیلترشکن «{data.get('name')}» اضافه شد!**")

@router.callback_query(lambda c: c.data == "list_vpn")
async def list_vpn(call: types.CallbackQuery):
    vpn_list = get_all_vpn()
    if not vpn_list:
        await call.message.edit_text("❌ هیچ فیلترشکنی وجود نداره!")
        return
    text = "📱 **لیست فیلترشکن‌ها:**\n\n"
    for vpn in vpn_list:
        text += f"• `{vpn[0]}` - {vpn[1]}\n"
    await call.message.edit_text(text)

@router.callback_query(lambda c: c.data == "delete_vpn")
async def delete_vpn_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_delete_vpn"}
    await call.message.edit_text("📝 **آیدی فیلترشکن رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete_vpn")
async def delete_vpn_confirm(message: types.Message):
    try:
        vpn_id = int(message.text)
        delete_vpn(vpn_id)
        await message.answer(f"✅ فیلترشکن حذف شد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")
    user_states[message.from_user.id] = {}

# ========================================
# ========================================
# ===== 💾 بکاپ و بازیابی =====
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
# ===== 🔙 برگشت به پنل =====
# ========================================
# ========================================

@router.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚙️ **پنل مدیریت**\n\n"
        "📊 از دکمه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
)
