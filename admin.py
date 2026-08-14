from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database import *
import asyncio

router = Router()
user_states = {}

# ========================================
# ===== پنل ادمین =====
# ========================================
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 افزودن کتاب")],
            [KeyboardButton(text="📋 لیست کتاب‌ها")],
            [KeyboardButton(text="🗑 حذف کتاب")],
            [KeyboardButton(text="🔍 جستجوی کتاب")],
            [KeyboardButton(text="📢 مدیریت کانال‌ها")],
            [KeyboardButton(text="🎨 مدیریت بنر")],
            [KeyboardButton(text="📊 آمار")],
            [KeyboardButton(text="🔙 بستن پنل")]
        ],
        resize_keyboard=True
    )

@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ **پنل مدیریت**", reply_markup=get_admin_keyboard())

# ========================================
# ===== افزودن کتاب =====
# ========================================
@router.message(lambda m: m.text == "📚 افزودن کتاب" and m.from_user.id == ADMIN_ID)
async def add_book_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_title"}
    await message.answer("📝 **عنوان کتاب رو بفرست:**")

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
    user_states[message.from_user.id]["state"] = "waiting_description"
    await message.answer("📝 **توضیحات کتاب رو بفرست (اختیاری):**\n(برای رد شدن /skip بفرست)")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_description")
async def get_description(message: types.Message):
    if message.text == "/skip":
        user_states[message.from_user.id]["description"] = ""
    else:
        user_states[message.from_user.id]["description"] = message.text
    user_states[message.from_user.id]["state"] = "waiting_file"
    await message.answer("📄 **حالا فایل کتاب رو بفرست (PDF/ZIP):**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.document and user_states.get(m.from_user.id, {}).get("state") == "waiting_file")
async def get_file(message: types.Message):
    data = user_states[message.from_user.id]
    title = data.get("title")
    author = data.get("author", "")
    description = data.get("description", "")
    
    add_book(
        title=title,
        author=author,
        description=description,
        file_id=message.document.file_id,
        file_name=message.document.file_name or "",
        file_size=message.document.file_size or 0
    )
    
    user_states[message.from_user.id] = {}
    await message.answer(f"✅ **کتاب «{title}» با موفقیت اضافه شد!**")

# ========================================
# ===== لیست کتاب‌ها =====
# ========================================
@router.message(lambda m: m.text == "📋 لیست کتاب‌ها" and m.from_user.id == ADMIN_ID)
async def list_books(message: types.Message):
    books = get_all_books()
    if not books:
        await message.answer("❌ هیچ کتابی ثبت نشده!")
        return
    text = "📋 **لیست کتاب‌ها:**\n\n"
    for book in books[:10]:
        text += f"• `{book[0]}` - {book[1]} (دانلود: {book[6]})\n"
    if len(books) > 10:
        text += f"\n... و {len(books) - 10} کتاب دیگه"
    await message.answer(text)

# ========================================
# ===== حذف کتاب =====
# ========================================
@router.message(lambda m: m.text == "🗑 حذف کتاب" and m.from_user.id == ADMIN_ID)
async def delete_book_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_delete"}
    await message.answer("📝 **آیدی کتاب رو برای حذف بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_delete")
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

# ========================================
# ===== جستجوی کتاب =====
# ========================================
@router.message(lambda m: m.text == "🔍 جستجوی کتاب" and m.from_user.id == ADMIN_ID)
async def search_book_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_search"}
    await message.answer("🔍 **عبارت جستجو رو بفرست:**")

@router.message(lambda m: m.from_user.id == ADMIN_ID and user_states.get(m.from_user.id, {}).get("state") == "waiting_search")
async def search_book_confirm(message: types.Message):
    query = message.text
    results = search_books(query)
    if not results:
        await message.answer(f"❌ نتیجه‌ای برای «{query}» پیدا نشد!")
        return
    text = f"🔍 **نتایج جستجو برای «{query}»:**\n\n"
    for book in results[:5]:
        text += f"• `{book[0]}` - {book[1]} (دانلود: {book[6]})\n"
    if len(results) > 5:
        text += f"\n... و {len(results) - 5} نتیجه دیگه"
    await message.answer(text)
    user_states[message.from_user.id] = {}

# ========================================
# ===== مدیریت کانال‌ها =====
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
# ===== مدیریت بنر =====
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
    await call.message.edit_text("📝 **بنر رو بفرست**\n\n• متن\n• عکس\n• ویدیو")

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
    else:
        await message.answer("❌ نوع فایل پشتیبانی نمیشه!")
        return
    user_states[message.from_user.id] = {}

@router.callback_query(lambda c: c.data == "delete_banner")
async def delete_banner_confirm(call: types.CallbackQuery):
    delete_banner()
    await call.message.edit_text("✅ بنر حذف شد!")

# ========================================
# ===== آمار =====
# ========================================
@router.message(lambda m: m.text == "📊 آمار" and m.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    books = get_all_books()
    channels = get_channels()
    total_downloads = sum(book[6] for book in books)
    await message.answer(
        f"📊 **آمار ربات:**\n\n"
        f"📁 کتاب‌ها: {len(books)} تا\n"
        f"📥 دانلودها: {total_downloads} بار\n"
        f"📢 کانال‌ها: {len(channels)} تا"
    )

# ========================================
# ===== برگشت =====
# ========================================
@router.callback_query(lambda c: c.data == "back_to_panel")
async def back_to_panel(call: types.CallbackQuery):
    await call.message.edit_text("⚙️ **پنل مدیریت**", reply_markup=get_admin_keyboard())

@router.message(lambda m: m.text == "🔙 بستن پنل" and m.from_user.id == ADMIN_ID)
async def close_panel(message: types.Message):
    await message.answer("✅ پنل بسته شد!", reply_markup=types.ReplyKeyboardRemove())
