# handlers.py

import json
import os

from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import *


router = Router()

# وضعیت‌های موقت کاربران
user_states = {}

# فایل موقت برای نگهداری لینک کتاب
TEMP_FILE = "temp.json"


# ========================================
# 🔒 عضویت اجباری
# ========================================

def join_keyboard():
    """ساخت کیبورد عضویت اجباری"""

    channels = get_channels()
    buttons = []

    for channel in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 عضویت در @{channel}",
                url=f"https://t.me/{channel}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="✅ عضو شدم",
            callback_data="check_mem"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


async def check_user_membership(bot, user_id):
    """بررسی عضویت کاربر در تمام کانال‌های اجباری"""

    channels = get_channels()

    if not channels:
        return True, None

    for channel in channels:
        try:
            member = await bot.get_chat_member(
                f"@{channel}",
                user_id
            )

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:
                return False, channel

        except Exception:
            return False, channel

    return True, None


# ========================================
# 🎨 ارسال بنر
# ========================================

async def send_banner(message: types.Message):
    """ارسال بنر فعلی"""

    banner = get_banner()

    if banner["type"] == "photo" and banner["file_id"]:
        await message.answer_photo(
            banner["file_id"],
            caption=banner["text"] or ""
        )

    elif banner["type"] == "video" and banner["file_id"]:
        await message.answer_video(
            banner["file_id"],
            caption=banner["text"] or ""
        )

    elif banner["type"] == "document" and banner["file_id"]:
        await message.answer_document(
            banner["file_id"],
            caption=banner["text"] or ""
        )

    else:
        await message.answer(
            banner["text"] or "📚 به ربات کتاب خوش آمدید!"
        )


# ========================================
# 📖 ارسال اطلاعات کتاب
# ========================================

async def send_book(message: types.Message, book_id: int):
    """نمایش اطلاعات کتاب و دکمه دانلود"""

    book = get_book(book_id)

    if not book:
        await message.answer(
            "❌ کتاب پیدا نشد!"
        )
        return

    (
        book_id,
        title,
        author,
        description,
        genre,
        cover_file_id,
        file_id,
        file_name,
        downloads
    ) = book

    text = f"📖 <b>{title}</b>\n\n"

    if author:
        text += f"✍️ <b>نویسنده:</b> {author}\n"

    if genre:
        text += f"📂 <b>ژانر:</b> {genre}\n"

    text += f"📥 <b>دانلودها:</b> {downloads} بار\n"

    if file_name:
        text += f"📄 <b>فایل:</b> {file_name}\n"

    if description:
        text += (
            f"\n📝 <b>توضیحات:</b>\n"
            f"{description}\n"
        )

    text += "\n👇 برای دریافت فایل روی دکمه زیر بزن."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 دریافت فایل",
                    callback_data=f"download_{book_id}"
                )
            ]
        ]
    )

    if cover_file_id:
        await message.answer_photo(
            cover_file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


# ========================================
# 📥 دانلود کتاب
# ========================================

@router.callback_query(
    lambda call: call.data and call.data.startswith("download_")
)
async def download_book(call: types.CallbackQuery):

    try:
        book_id = int(
            call.data.replace("download_", "")
        )
    except ValueError:
        await call.answer(
            "❌ شناسه کتاب نامعتبر است!",
            show_alert=True
        )
        return

    book = get_book(book_id)

    if not book:
        await call.answer(
            "❌ کتاب پیدا نشد!",
            show_alert=True
        )
        return

    (
        _,
        title,
        author,
        description,
        genre,
        cover_file_id,
        file_id,
        file_name,
        downloads
    ) = book

    # افزایش دانلود
    increment_download(book_id)

    caption = (
        f"📖 <b>{title}</b>\n\n"
        "✅ فایل با موفقیت ارسال شد."
    )

    try:
        await call.message.answer_document(
            file_id,
            caption=caption,
            parse_mode="HTML"
        )

        await call.answer(
            "✅ دانلود شروع شد!"
        )

    except Exception:
        await call.answer(
            "❌ ارسال فایل با خطا مواجه شد.",
            show_alert=True
        )


# ========================================
# 🔐 فایل‌های رمزدار
# ========================================

@router.message(
    lambda message:
        message.text
        and not message.text.startswith("/")
)
async def handle_password_file(message: types.Message):

    code = message.text.strip()

    file_info = get_password_file_by_code(code)

    if not file_info:
        return

    (
        file_id,
        name,
        file_type,
        caption
    ) = (
        file_info[2],
        file_info[1],
        file_info[3],
        file_info[4]
    )

    final_caption = (
        f"🔐 <b>{name}</b>\n\n"
        f"{caption or ''}"
    )

    try:

        if file_type == "photo":

            await message.answer_photo(
                file_id,
                caption=final_caption,
                parse_mode="HTML"
            )

        elif file_type == "video":

            await message.answer_video(
                file_id,
                caption=final_caption,
                parse_mode="HTML"
            )

        else:

            await message.answer_document(
                file_id,
                caption=final_caption,
                parse_mode="HTML"
            )

    except Exception:
        await message.answer(
            "❌ خطا در ارسال فایل!"
        )


# ========================================
# 🚀 /start
# ========================================

@router.message(CommandStart())
async def start(message: types.Message):

    # ثبت کاربر
    add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or ""
    )

    args = message.text.split()

    # ====================================
    # Start معمولی
    # ====================================

    if len(args) == 1:

        await send_banner(message)

        await message.answer(
            f"👋 <b>سلام {message.from_user.first_name}!</b>\n\n"
            "📚 به ربات مدیریت کتاب خوش اومدی.\n\n"
            "🔎 برای دریافت کتاب از لینک اختصاصی استفاده کن.",
            parse_mode="HTML"
        )

        return

    # ====================================
    # Start با کد
    # ====================================

    code = args[1]

    if not code.startswith("book_"):

        await message.answer(
            "❌ لینک نامعتبر!"
        )
        return

    try:

        book_id = int(
            code.replace("book_", "")
        )

    except ValueError:

        await message.answer(
            "❌ لینک نامعتبر!"
        )
        return

    # بررسی وجود کتاب
    book = get_book(book_id)

    if not book:

        await message.answer(
            "❌ این کتاب دیگر وجود ندارد!"
        )
        return

    # ====================================
    # عضویت اجباری
    # ====================================

    is_member, channel = await check_user_membership(
        message.bot,
        message.from_user.id
    )

    if not is_member:

        try:
            with open(
                TEMP_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    {
                        "user_id": message.from_user.id,
                        "book_id": book_id
                    },
                    f
                )

        except Exception:
            pass

        await message.answer(
            "🔒 <b>عضویت اجباری</b>\n\n"
            "برای دریافت این کتاب ابتدا در کانال‌های زیر عضو شو.\n"
            "بعد از عضویت روی «✅ عضو شدم» بزن.",
            reply_markup=join_keyboard(),
            parse_mode="HTML"
        )

        return

    # ====================================
    # ارسال کتاب
    # ====================================

    await send_book(
        message,
        book_id
    )


# ========================================
# ✅ بررسی عضویت
# ========================================

@router.callback_query(
    lambda call: call.data == "check_mem"
)
async def check_mem(call: types.CallbackQuery):

    is_member, channel = await check_user_membership(
        call.bot,
        call.from_user.id
    )

    if not is_member:

        await call.answer(
            f"❌ هنوز در @{channel} عضو نشدی!",
            show_alert=True
        )

        return

    # دریافت کتاب ذخیره‌شده
    book_id = None

    try:

        with open(
            TEMP_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if data.get("user_id") == call.from_user.id:
            book_id = data.get("book_id")

    except Exception:
        pass

    if not book_id:

        await call.answer(
            "❌ لینک کتاب پیدا نشد. دوباره لینک را باز کن.",
            show_alert=True
        )

        return

    # پاک کردن اطلاعات موقت
    try:
        os.remove(TEMP_FILE)
    except Exception:
        pass

    await call.answer(
        "✅ عضویت شما تأیید شد!"
    )

    try:
        await call.message.delete()
    except Exception:
        pass

    await send_book(
        call.message,
        book_id
    )


# ========================================
# 🔄 دستور لغو وضعیت‌های ادمین/کاربر
# ========================================

@router.message(
    lambda message:
        message.text == "/cancel"
)
async def cancel_state(message: types.Message):

    if message.from_user.id in user_states:

        user_states[message.from_user.id] = {}

        await message.answer(
            "✅ عملیات لغو شد."
        )


# ========================================
# ❌ خطای عمومی این Router
# ========================================

# این بخش عمداً خالی نگه داشته شده تا
# Exception Handler اصلی در main.py مدیریت شود.
