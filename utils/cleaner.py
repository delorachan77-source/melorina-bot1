import os
import fitz  # PyMuPDF
from PIL import Image
import io

# ========================================
# ===== کلینر PDF =====
# ========================================
async def clean_pdf(file_path):
    """پاک‌سازی و بهینه‌سازی PDF"""
    try:
        doc = fitz.open(file_path)
        output_path = file_path.replace(".pdf", "_cleaned.pdf")
        new_doc = fitz.open()
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # استخراج متن
            text = page.get_text()
            
            # پاک‌سازی صفحه (حذف حاشیه‌ها)
            rect = page.rect
            margin = 30
            clean_rect = fitz.Rect(
                rect.x0 + margin,
                rect.y0 + margin,
                rect.x1 - margin,
                rect.y1 - margin
            )
            
            # ایجاد صفحه جدید
            new_page = new_doc.new_page(width=rect.width, height=rect.height)
            
            # درج متن پاک‌سازی شده
            if text.strip():
                new_page.insert_text(
                    (50, 50),
                    text,
                    fontsize=11,
                    fontname="helv"
                )
        
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path
    except Exception as e:
        print(f"❌ خطا در کلینر PDF: {e}")
        return None

# ========================================
# ===== کلینر عکس =====
# ========================================
async def clean_image(file_path):
    """پاک‌سازی و بهینه‌سازی عکس"""
    try:
        image = Image.open(file_path)
        
        # کاهش حجم
        if image.width > 2000:
            ratio = 2000 / image.width
            new_size = (2000, int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # بهبود کیفیت
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # ذخیره با کیفیت بالا
        output_path = file_path.replace(".jpg", "_cleaned.jpg").replace(".png", "_cleaned.png")
        image.save(output_path, quality=95, optimize=True)
        return output_path
    except Exception as e:
        print(f"❌ خطا در کلینر عکس: {e}")
        return None

# ========================================
# ===== تشخیص نوع فایل =====
# ========================================
def get_file_type(file_path):
    if file_path.endswith(".pdf"):
        return "pdf"
    elif file_path.endswith((".jpg", ".jpeg", ".png", ".gif")):
        return "image"
    elif file_path.endswith((".mp4", ".avi", ".mkv")):
        return "video"
    elif file_path.endswith((".zip", ".rar")):
        return "archive"
    else:
        return "other"
