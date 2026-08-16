from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import asyncio

router = Router()
user_states = {}

# ========================================
# ===== کیبورد اصلی پنل ادمین =====
# ========================================
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 مدیریت کتاب‌ها")],
            [KeyboardButton(text="📖 مدیریت مانگا")],
            [KeyboardButton(text="🎨 مدیریت مانهوا")],
            [KeyboardButton(text="📢 مدیریت کانال‌ها")],
            [KeyboardButton(text="🎨 مدیریت بنر")],
            [KeyboardButton(text="👥 مدیریت کاربران")],
            [KeyboardButton(text="📊 آمار پیشرفته")],
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
# ===== مدیریت کتاب‌ها =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📚 مدیریت کتاب‌ها" and m.from_user.id == ADMIN_ID)
async def manage_books(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن کتاب", callback_data="add_book")],
        [InlineKeyboardButton(text="📋 لیست کتاب‌ها", callback_data="list_books")],
        [InlineKeyboardButton(text="🗑 حذف کتاب", callback_data="delete_book")],
        [InlineKeyboardButton(text="✏️ ویرایش کتاب", callback_data="edit_book")],
        [InlineKeyboardButton(text="🔍 جستجوی کتاب", callback_data="search_book")],
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
async def get_book_title(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_author"
    await message.answer("✍️ **نویسنده رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_author")
async def get_book_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_genre"
    await message.answer("📂 **ژانر رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_genre")
async def get_book_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_description"
    await message.answer("📝 **توضیحات رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_description")
async def get_book_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_cover"
    await message.answer("🖼 **جلد کتاب رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_cover")
async def get_book_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_file"
        await message.answer("📄 **حالا فایل کتاب رو بفرست:**")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_file"
        await message.answer("📄 **حالا فایل کتاب رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_file")
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
            user_states[message.from_user.id] = {"state": "edit_book_data", "book_id": book_id, "book": book}
            await message.answer(
                f"📝 **ویرایش کتاب «{book[1]}»**\n\n"
                f"عنوان: {book[1]}\n"
                f"نویسنده: {book[2] or '-'}\n"
                f"ژانر: {book[3] or '-'}\n"
                f"توضیحات: {book[4] or '-'}\n\n"
                f"برای ویرایش، اطلاعات جدید رو به ترتیب بفرست:\n"
                f"`عنوان|نویسنده|ژانر|توضیحات`\n\n"
                f"مثال: `کتاب جدید|نویسنده جدید|رمان|توضیحات جدید`"
            )
        else:
            await message.answer("❌ کتاب پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "edit_book_data")
async def edit_book_save(message: types.Message):
    data = user_states[message.from_user.id]
    book_id = data.get("book_id")
    book = data.get("book")
    
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
        cover_file_id=book[5],
        file_id=book[6],
        file_name=book[7],
        file_size=book[8]
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **کتاب ویرایش شد!**")

@router.callback_query(lambda c: c.data == "search_book")
async def search_book_start(call: types.CallbackQuery):
    user_states[call.from_user.id] = {"state": "waiting_search_book"}
    await call.message.edit_text("🔍 **عبارت جستجو رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_search_book")
async def search_book_confirm(message: types.Message):
    query = message.text
    results = search_books(query)
    if not results:
        await message.answer(f"❌ نتیجه‌ای برای «{query}» پیدا نشد!")
        return
    text = f"🔍 **نتایج جستجو:**\n\n"
    for book in results[:5]:
        text += f"• `{book[0]}` - {book[1]}\n"
    await message.answer(text)
    user_states[message.from_user.id] = {}

# ========================================
# ========================================
# ===== مدیریت مانگا =====
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

# ===== افزودن مانگا (همون مراحل کتاب) =====
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
    await message.answer("✍️ **نویسنده مانگا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_author")
async def get_manga_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manga_genre"
    await message.answer("📂 **ژانر مانگا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_genre")
async def get_manga_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manga_description"
    await message.answer("📝 **توضیحات مانگا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_description")
async def get_manga_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manga_cover"
    await message.answer("🖼 **جلد مانگا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manga_cover")
async def get_manga_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_manga_file"
        await message.answer("📄 **حالا فایل مانگا رو بفرست:**")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_manga_file"
        await message.answer("📄 **حالا فایل مانگا رو بفرست:**")

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

# ===== لیست مانگا =====
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

# ===== حذف مانگا =====
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

# ===== ویرایش مانگا =====
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
            user_states[message.from_user.id] = {"state": "edit_manga_data", "manga_id": manga_id, "manga": manga}
            await message.answer(
                f"📝 **ویرایش مانگا «{manga[1]}»**\n\n"
                f"برای ویرایش، اطلاعات جدید رو به ترتیب بفرست:\n"
                f"`عنوان|نویسنده|ژانر|توضیحات`"
            )
        else:
            await message.answer("❌ مانگا پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "edit_manga_data")
async def edit_manga_save(message: types.Message):
    data = user_states[message.from_user.id]
    manga_id = data.get("manga_id")
    manga = data.get("manga")
    
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
        cover_file_id=manga[5],
        file_id=manga[6],
        file_name=manga[7],
        file_size=manga[8]
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **مانگا ویرایش شد!**")

# ========================================
# ========================================
# ===== مدیریت مانهوا (همانند مانگا) =====
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

# ===== افزودن مانهوا =====
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
    await message.answer("✍️ **نویسنده مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_author")
async def get_manhwa_author(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["author"] = ""
    else:
        user_states[message.from_user.id]["author"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manhwa_genre"
    await message.answer("📂 **ژانر مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_genre")
async def get_manhwa_genre(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["genre"] = ""
    else:
        user_states[message.from_user.id]["genre"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manhwa_description"
    await message.answer("📝 **توضیحات مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_description")
async def get_manhwa_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_manhwa_cover"
    await message.answer("🖼 **جلد مانهوا رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_manhwa_cover")
async def get_manhwa_cover(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["cover"] = ""
        user_states[message.from_user.id]["state"] = "waiting_manhwa_file"
        await message.answer("📄 **حالا فایل مانهوا رو بفرست:**")
        return
    if message.photo:
        user_states[message.from_user.id]["cover"] = message.photo[-1].file_id
        user_states[message.from_user.id]["state"] = "waiting_manhwa_file"
        await message.answer("📄 **حالا فایل مانهوا رو بفرست:**")

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

# ===== لیست مانهوا =====
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

# ===== حذف مانهوا =====
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

# ===== ویرایش مانهوا =====
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
            user_states[message.from_user.id] = {"state": "edit_manhwa_data", "manhwa_id": manhwa_id, "manhwa": manhwa}
            await message.answer(
                f"📝 **ویرایش مانهوا «{manhwa[1]}»**\n\n"
                f"برای ویرایش، اطلاعات جدید رو به ترتیب بفرست:\n"
                f"`عنوان|نویسنده|ژانر|توضیحات`"
            )
        else:
            await message.answer("❌ مانهوا پیدا نشد!")
    except:
        await message.answer("❌ لطفاً یک عدد معتبر بفرست!")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "edit_manhwa_data")
async def edit_manhwa_save(message: types.Message):
    data = user_states[message.from_user.id]
    manhwa_id = data.get("manhwa_id")
    manhwa = data.get("manhwa")
    
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
        cover_file_id=manhwa[5],
        file_id=manhwa[6],
        file_name=manhwa[7],
        file_size=manhwa[8]
    )
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **مانهوا ویرایش شد!**")

# ========================================
# ========================================
# ===== بقیه قابلیت‌ها (مدیریت کانال، بنر، کاربران، آمار، رمز فایل، نظرات، بروزرسانی، بکاپ) =====
# ========================================
# ========================================

# ===== مدیریت کانال‌ها =====
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

# ===== مدیریت بنر =====
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
    await call.message.edit_text("📝 **بنر رو بفرست**\n\n• متن\n• عکس\n• ویدیو\n• فایل")

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

@router.callback_query(lambda c: c.data == "delete_banner")
async def delete_banner_confirm(call: types.CallbackQuery):
    delete_banner()
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

# ===== مدیریت کاربران =====
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

# ===== آمار پیشرفته =====
@router.message(lambda m: m.text == "📊 آمار پیشرفته" and m.from_user.id == ADMIN_ID)
async def advanced_stats(message: types.Message):
    books = get_all_books()
    manga_list = get_all_manga()
    manhwa_list = get_all_manhwa()
    channels = get_channels()
    users = get_user_count()
    
    await message.answer(
        f"📊 **آمار پیشرفته ربات:**\n\n"
        f"📁 **کتاب‌ها:** {len(books)} تا\n"
        f"📖 **مانگاها:** {len(manga_list)} تا\n"
        f"🎨 **مانهواها:** {len(manhwa_list)} تا\n"
        f"📢 **کانال‌ها:** {len(channels)} تا\n"
        f"👥 **کاربران:** {users} نفر"
    )

# ===== رمز فایل =====
@router.message(lambda m: m.text == "🔐 رمز فایل" and m.from_user.id == ADMIN_ID)
async def manage_password_files(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن فایل با رمز", callback_data="add_password_file")],
        [InlineKeyboardButton(text="📋 لیست فایل‌های رمزدار", callback_data="list_password_files")],
        [InlineKeyboardButton(text="🗑 حذف فایل رمزدار", callback_data="delete_password_file")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_panel")]
    ])
    await message.answer("🔐 **سیستم رمز فایل**", reply_markup=keyboard)

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

# ===== نظرات و پیشنهادات =====
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

# ===== بروزرسانی‌ها =====
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

# ===== بکاپ و بازیابی =====
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
# ===== برگشت به پنل =====
# ========================================
@router.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚙️ **پنل مدیریت**\n\n"
        "📊 از دکمه‌های زیر استفاده کن:",
        reply_markup=get_admin_keyboard()
)
