from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID, GEMINI_API_KEY
from database import *
import json
import aiohttp
import asyncio

router = Router()
user_states = {}

# ========================================
# ========================================
# ===== شخصیت‌های جیمینای =====
# ========================================
# ========================================

PERSONALITIES = {
    "کیوت": {
        "emoji": "🌸",
        "prompt": "با لحن شیرین، صمیمی و دلنشین پاسخ بده. از کلمات محبت‌آمیز استفاده کن. بجای چرا بگو چراااا! بجای چیشد بگو چیشدد! 😊",
        "description": "شیرین و صمیمی"
    },
    "مغرور": {
        "emoji": "🦁",
        "prompt": "با لحن مغرور و برتر پاسخ بده. انگار که همه چیز رو میدونی. از کلمات قاطع استفاده کن.",
        "description": "با برتری و قاطعیت"
    },
    "بامزه": {
        "emoji": "😂",
        "prompt": "با لحن شوخ و طنز پاسخ بده. از جوک و لطیفه استفاده کن.",
        "description": "شوخ و طنز"
    },
    "خجالتی": {
        "emoji": "😳",
        "prompt": "با لحن خجالتی و کم‌رو پاسخ بده. انگار که خجالت میکشی. از کلمات نرم استفاده کن.",
        "description": "کم‌رو و نرم"
    },
    "باهوش": {
        "emoji": "🧠",
        "prompt": "با لحن علمی و دقیق پاسخ بده. از کلمات تخصصی استفاده کن.",
        "description": "علمی و دقیق"
    },
    "دارک": {
        "emoji": "🌙",
        "prompt": "با لحن تاریک و مرموز پاسخ بده. انگار که رازهایی داری.",
        "description": "تاریک و مرموز"
    }
}

# ========================================
# ========================================
# ===== چت با جیمینای (نسخه اصلاح شده) =====
# ========================================
# ========================================

async def chat_with_gemini(message, personality="کیوت"):
    """چت با مدل Gemini - کاربران فقط پاسخ ربات را می‌بینند"""

    if not GEMINI_API_KEY:
        await message.answer(
            "🌸 سرویس چت فعلاً در دسترس نیست. بعداً دوباره امتحان کن."
        )
        return

    personality_data = PERSONALITIES.get(
        personality,
        PERSONALITIES["کیوت"]
    )

    prompt = f"""
{personality_data['prompt']}

به فارسی و طبیعی جواب بده.
پاسخ‌ها دوستانه، روان و نسبتاً کوتاه باشند.
نام سرویس، مدل، API یا شرکت سازنده را در پاسخ مطرح نکن.
اگر کاربر پرسید چه کسی هستی، خودت را «دستیار ربات» معرفی کن.

پیام کاربر:
{message.text}
"""

    thinking_msg = await message.answer("🌸 یک لحظه...")

    # مدل‌های فعلی پیشنهادی
    models = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]

    try:
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:

            for model in models:

                try:
                    url = (
                        "https://generativelanguage.googleapis.com/"
                        f"v1beta/models/{model}:generateContent"
                    )

                    payload = {
                        "contents": [
                            {
                                "role": "user",
                                "parts": [
                                    {
                                        "text": prompt
                                    }
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.8,
                            "topP": 0.95,
                            "maxOutputTokens": 800
                        }
                    }

                    headers = {
                        "Content-Type": "application/json",
                        "x-goog-api-key": GEMINI_API_KEY
                    }

                    async with session.post(
                        url,
                        json=payload,
                        headers=headers
                    ) as response:

                        response_text = await response.text()

                        if response.status == 200:

                            try:
                                data = json.loads(response_text)
                            except json.JSONDecodeError:
                                continue

                            candidates = data.get("candidates", [])

                            if not candidates:
                                continue

                            content = candidates[0].get(
                                "content",
                                {}
                            )

                            parts = content.get("parts", [])

                            result = ""

                            for part in parts:
                                if part.get("text"):
                                    result += part["text"]

                            result = result.strip()

                            if result:

                                try:
                                    await thinking_msg.delete()
                                except:
                                    pass

                                await message.answer(result)
                                return

                        else:
                            print(
                                f"Gemini error [{model}] "
                                f"{response.status}: "
                                f"{response_text[:500]}"
                            )

                except asyncio.TimeoutError:
                    print(f"Timeout on {model}")
                    continue

                except aiohttp.ClientError as e:
                    print(f"Connection error on {model}: {e}")
                    continue

                except Exception as e:
                    print(f"Model error [{model}]: {e}")
                    continue

        try:
            await thinking_msg.delete()
        except:
            pass

        await message.answer(
            "🌸 سرویس چت فعلاً در دسترس نیست. "
            "چند لحظه دیگه دوباره امتحان کن."
        )

    except Exception as e:

        print(f"❌ Gemini fatal error: {e}")

        try:
            await thinking_msg.delete()
        except:
            pass

        await message.answer(
            "🌸 یه مشکلی پیش اومد. بعداً دوباره امتحان کن."
        )

# ========================================
# ========================================
# ===== کیبورد منوی کاربر =====
# ========================================
# ========================================

def user_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 کتاب‌ها")],
            [KeyboardButton(text="📖 مانگا")],
            [KeyboardButton(text="🎨 مانهوا")],
            [KeyboardButton(text="📱 معرفی مانهوا")],
            [KeyboardButton(text="💬 چت")],
            [KeyboardButton(text="💬 نظر و پیشنهاد")],
            [KeyboardButton(text="⭐ امتیاز به ربات")],
        ],
        resize_keyboard=True
    )

# ========================================
# ========================================
# ===== کیبورد انتخاب شخصیت =====
# ========================================
# ========================================

def personality_keyboard():
    buttons = []
    for name, data in PERSONALITIES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{data['emoji']} {name}",
            callback_data=f"personality_{name}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
# ===== کتاب‌ها (لیست) =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📚 کتاب‌ها")
async def list_books_user(message: types.Message):
    books = get_all_books()
    if not books:
        await message.answer("❌ هیچ کتابی موجود نیست!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖 {book[1]}", callback_data=f"book_{book[0]}")] for book in books[:10]
    ])
    
    await message.answer(
        "📚 **لیست کتاب‌ها:**\n\n"
        "یک کتاب رو انتخاب کن:",
        reply_markup=keyboard
    )

@router.message(lambda m: m.text == "📖 مانگا")
async def list_manga_user(message: types.Message):
    manga_list = get_all_manga()
    if not manga_list:
        await message.answer("❌ هیچ مانگایی موجود نیست!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖 {manga[1]}", callback_data=f"manga_{manga[0]}")] for manga in manga_list[:10]
    ])
    
    await message.answer(
        "📖 **لیست مانگاها:**\n\n"
        "یک مانگا رو انتخاب کن:",
        reply_markup=keyboard
    )

@router.message(lambda m: m.text == "🎨 مانهوا")
async def list_manhwa_user(message: types.Message):
    manhwa_list = get_all_manhwa()
    if not manhwa_list:
        await message.answer("❌ هیچ مانهوایی موجود نیست!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎨 {manhwa[1]}", callback_data=f"manhwa_{manhwa[0]}")] for manhwa in manhwa_list[:10]
    ])
    
    await message.answer(
        "🎨 **لیست مانهواها:**\n\n"
        "یک مانهوا رو انتخاب کن:",
        reply_markup=keyboard
    )

# ========================================
# ========================================
# ===== معرفی مانهوا =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "📱 معرفی مانهوا")
async def list_manhwa_intro_user(message: types.Message):
    intro_list = get_all_manhwa_intro()
    if not intro_list:
        await message.answer("❌ هیچ معرفی مانهوایی موجود نیست!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎨 {intro[1]}", callback_data=f"intro_{intro[0]}")] for intro in intro_list[:10]
    ])
    
    await message.answer(
        "📱 **معرفی مانهواها:**\n\n"
        "یک مانهوا رو برای معرفی انتخاب کن:",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data.startswith("intro_"))
async def show_manhwa_intro(call: types.CallbackQuery):
    intro_id = int(call.data.replace("intro_", ""))
    intro = get_manhwa_intro(intro_id)
    
    if not intro:
        await call.answer("❌ معرفی پیدا نشد!")
        return
    
    _, title, description, genre, cover_file_id, link = intro
    
    text = f"🎨 **معرفی مانهوا: {title}**\n\n"
    if genre:
        text += f"📂 **ژانر:** {genre}\n\n"
    if description:
        text += f"📝 {description}\n\n"
    if link:
        text += f"🔗 **لینک:** {link}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 مشاهده", url=link)] if link else [],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_intro")]
    ])
    
    if cover_file_id:
        await call.message.answer_photo(cover_file_id, caption=text, reply_markup=keyboard)
    else:
        await call.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "back_to_intro")
async def back_to_intro(call: types.CallbackQuery):
    await list_manhwa_intro_user(call.message)

# ========================================
# ========================================
# ===== نمایش و دریافت چپترها =====
# ========================================
# ========================================

@router.callback_query(lambda c: c.data.startswith("book_") or c.data.startswith("manga_") or c.data.startswith("manhwa_"))
async def show_chapters(call: types.CallbackQuery):
    data = call.data.split("_")
    item_type = data[0]
    item_id = int(data[1])
    
    if item_type == "book":
        item = get_book(item_id)
        title = item[1]
        caption = f"📖 **{title}**\n\nبرای دریافت فایل روی دکمه زیر کلیک کن:"
    elif item_type == "manga":
        item = get_manga(item_id)
        title = item[1]
        caption = f"📖 **{title}**\n\nبرای دریافت فایل روی دکمه زیر کلیک کن:"
    elif item_type == "manhwa":
        item = get_manhwa(item_id)
        title = item[1]
        caption = f"🎨 **{title}**\n\nبرای دریافت فایل روی دکمه زیر کلیک کن:"
    else:
        await call.answer("❌ پیدا نشد!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 دریافت فایل", callback_data=f"download_{item_type}_{item_id}")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"back_to_{item_type}s")]
    ])
    
    await call.message.edit_text(caption, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("download_"))
async def download_item(call: types.CallbackQuery):
    data = call.data.replace("download_", "").split("_")
    item_type = data[0]
    item_id = int(data[1])
    
    if item_type == "book":
        item = get_book(item_id)
    elif item_type == "manga":
        item = get_manga(item_id)
    elif item_type == "manhwa":
        item = get_manhwa(item_id)
    else:
        await call.answer("❌ پیدا نشد!")
        return
    
    if not item:
        await call.answer("❌ پیدا نشد!")
        return
    
    _, title, author, description, genre, cover_file_id, file_id, file_name, downloads = item
    
    if item_type == "book":
        increment_download(item_id)
    elif item_type == "manga":
        increment_download(item_id)
    elif item_type == "manhwa":
        increment_download(item_id)
    
    await send_banner(call.message)
    await call.message.answer_document(
        file_id,
        caption=f"📖 **{title}**\n\n✅ دانلود شد!"
    )
    await call.answer("✅ دانلود شروع شد!")

@router.callback_query(lambda c: c.data.startswith("back_to_"))
async def back_to_list(call: types.CallbackQuery):
    item_type = call.data.replace("back_to_", "")
    if item_type == "books":
        await list_books_user(call.message)
    elif item_type == "mangas":
        await list_manga_user(call.message)
    elif item_type == "manhwas":
        await list_manhwa_user(call.message)

# ========================================
# ========================================
# ===== چت (منوی کاربر) =====
# ========================================
# ========================================

@router.message(lambda m: m.text == "💬 چت")
async def chat_start(message: types.Message):
    user_states[message.from_user.id] = {"state": "waiting_chat_personality"}
    await message.answer(
        "🌸 **انتخاب شخصیت:**\n\n"
        "یکی از شخصیت‌های زیر رو انتخاب کن:",
        reply_markup=personality_keyboard()
    )

@router.callback_query(lambda c: c.data.startswith("personality_"))
async def set_personality(call: types.CallbackQuery):
    personality = call.data.replace("personality_", "")
    user_states[call.from_user.id] = {
        "state": "waiting_chat_message",
        "personality": personality
    }
    
    emoji = PERSONALITIES.get(personality, {}).get("emoji", "🌸")
    await call.message.edit_text(
        f"{emoji} **شخصیت {personality} انتخاب شد!**\n\n"
        "حالا هر چی دوست داری بپرس! 😊\n"
        "برای بستن /cancel بفرست."
    )

@router.message(lambda m: m.text and user_states.get(m.from_user.id, {}).get("state") == "waiting_chat_message")
async def chat_response(message: types.Message):
    if message.text == "/cancel":
        user_states[message.from_user.id] = {}
        await message.answer("✅ چت بسته شد! 🌸")
        return
    
    personality = user_states[message.from_user.id].get("personality", "کیوت")
    await chat_with_gemini(message, personality)

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
            "🌸 به ربات خوش اومدی!",
            reply_markup=user_menu_keyboard()
        )
        return
    
    code = args[1]
    
    # ===== لینک کتاب =====
    if code.startswith("book_"):
        try:
            book_id = int(code.replace("book_", ""))
            channels = get_channels()
            if channels:
                with open("temp.json", "w") as f:
                    json.dump({"book_id": book_id, "type": "book"}, f)
                await message.answer(
                    "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
                    reply_markup=join_keyboard()
                )
                return
            await send_book(message, book_id)
        except ValueError:
            await message.answer("❌ لینک نامعتبر!")
    
    # ===== لینک مانگا =====
    elif code.startswith("manga_"):
        try:
            manga_id = int(code.replace("manga_", ""))
            channels = get_channels()
            if channels:
                with open("temp.json", "w") as f:
                    json.dump({"manga_id": manga_id, "type": "manga"}, f)
                await message.answer(
                    "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
                    reply_markup=join_keyboard()
                )
                return
            await send_manga(message, manga_id)
        except ValueError:
            await message.answer("❌ لینک نامعتبر!")
    
    # ===== لینک مانهوا =====
    elif code.startswith("manhwa_"):
        try:
            manhwa_id = int(code.replace("manhwa_", ""))
            channels = get_channels()
            if channels:
                with open("temp.json", "w") as f:
                    json.dump({"manhwa_id": manhwa_id, "type": "manhwa"}, f)
                await message.answer(
                    "🔒 **لطفاً در کانال‌های زیر عضو شوید:**",
                    reply_markup=join_keyboard()
                )
                return
            await send_manhwa(message, manhwa_id)
        except ValueError:
            await message.answer("❌ لینک نامعتبر!")
    
    # ===== لینک معرفی مانهوا =====
    elif code.startswith("intro_"):
        try:
            intro_id = int(code.replace("intro_", ""))
            intro = get_manhwa_intro(intro_id)
            if intro:
                _, title, description, genre, cover_file_id, link = intro
                text = f"🎨 **معرفی مانهوا: {title}**\n\n"
                if genre:
                    text += f"📂 **ژانر:** {genre}\n\n"
                if description:
                    text += f"📝 {description}\n\n"
                if link:
                    text += f"🔗 **لینک:** {link}"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 مشاهده", url=link)] if link else [],
                ])
                
                if cover_file_id:
                    await message.answer_photo(cover_file_id, caption=text, reply_markup=keyboard)
                else:
                    await message.answer(text, reply_markup=keyboard)
            else:
                await message.answer("❌ معرفی پیدا نشد!")
        except ValueError:
            await message.answer("❌ لینک نامعتبر!")
    else:
        await message.answer("❌ لینک نامعتبر!")

# ========================================
# ========================================
# ===== ارسال کتاب (برای لینک‌ها) =====
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
        item_type = data.get("type", "book")
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
    
    if item_type == "book" and book_id:
        await send_book(call.message, book_id)
    elif item_type == "manga" and manga_id:
        await send_manga(call.message, manga_id)
    elif item_type == "manhwa" and manhwa_id:
        await send_manhwa(call.message, manhwa_id)
