import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import os

# ========================================
# ===== تایپیست فارسی =====
# ========================================
async def type_persian_text(text, output_path, font_name="Vazir", font_size=20):
    """تایپ متن فارسی با فونت زیبا"""
    try:
        # اصلاح متن برای نمایش درست
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        
        # پیدا کردن فونت
        font_paths = [
            f"fonts/{font_name}.ttf",
            f"/usr/share/fonts/truetype/{font_name}.ttf",
            f"C:/Windows/Fonts/{font_name}.ttf"
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        
        if not font:
            # فونت پیش‌فرض
            font = ImageFont.load_default()
        
        # محاسبه اندازه متن
        img_width = 800
        img_height = 600
        
        # ایجاد تصویر
        image = Image.new('RGB', (img_width, img_height), color='white')
        draw = ImageDraw.Draw(image)
        
        # نوشتن متن (راست‌چین)
        x = img_width - 50
        y = 50
        
        # شکستن متن به خطوط
        lines = text.split('\n')
        for line in lines:
            reshaped = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped)
            bbox = draw.textbbox((0, 0), bidi_line, font=font)
            line_width = bbox[2] - bbox[0]
            draw.text((x - line_width, y), bidi_line, font=font, fill='black')
            y += font_size + 10
        
        # ذخیره
        image.save(output_path)
        return output_path
    except Exception as e:
        print(f"❌ خطا در تایپیست: {e}")
        return None

# ========================================
# ===== فونت‌های موجود =====
# ========================================
def get_available_fonts():
    fonts = {
        "Vazir": "وزیر",
        "IranSans": "ایران‌سنس",
        "Nazanin": "نازنین",
        "Yekan": "یکان",
        "Mitra": "میترا",
        "Lotus": "لوتوس",
        "Zar": "زر",
        "Traffic": "ترافیک"
    }
    return fonts
