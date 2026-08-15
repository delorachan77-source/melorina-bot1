import sqlite3
import os
from datetime import datetime

# ========================================
# ===== تنظیم مسیر دیتابیس =====
# ========================================
DB_PATH = os.getenv("DB_PATH", "bot.db")

# ========================================
# ===== اتصال به دیتابیس =====
# ========================================
db = sqlite3.connect(DB_PATH, check_same_thread=False)
c = db.cursor()

# ========================================
# ===== ساخت جدول‌ها =====
# ========================================

# ===== جدول کتاب‌ها (با فیلدهای جدید: ژانر و جلد) =====
c.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        description TEXT,
        genre TEXT,
        cover_file_id TEXT,
        file_id TEXT NOT NULL,
        file_name TEXT,
        file_size INTEGER,
        downloads INTEGER DEFAULT 0,
        created_at TEXT
    )
""")

# ===== جدول کانال‌های اجباری =====
c.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY
    )
""")

# ===== جدول بنر =====
c.execute("""
    CREATE TABLE IF NOT EXISTS banner (
        type TEXT DEFAULT 'text',
        file_id TEXT,
        text TEXT
    )
""")

# ===== جدول کاربران =====
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        join_date TEXT
    )
""")

# ===== جدول رمز فایل (جدید) =====
c.execute("""
    CREATE TABLE IF NOT EXISTS password_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        file_id TEXT NOT NULL,
        file_type TEXT DEFAULT 'document',
        caption TEXT,
        created_at TEXT
    )
""")

# ===== جدول فعالیت ادمین‌ها (جدید) =====
c.execute("""
    CREATE TABLE IF NOT EXISTS admin_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        details TEXT,
        created_at TEXT
    )
""")

db.commit()
print("✅ دیتابیس با فیلدهای جدید راه‌اندازی شد!")

# ========================================
# ========================================
# ===== توابع کتاب‌ها =====
# ========================================
# ========================================

def add_book(title, author, description, genre, cover_file_id, file_id, file_name="", file_size=0):
    """افزودن کتاب جدید با جلد و ژانر"""
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO books (title, author, description, genre, cover_file_id, file_id, file_name, file_size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, author, description, genre, cover_file_id, file_id, file_name, file_size, now))
    db.commit()
    return c.lastrowid

def get_all_books():
    """دریافت لیست همه کتاب‌ها با اطلاعات کامل"""
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        ORDER BY created_at DESC
    """)
    return c.fetchall()

def get_book(book_id):
    """دریافت اطلاعات کامل یک کتاب با آیدی"""
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        WHERE id=?
    """, (book_id,))
    return c.fetchone()

def delete_book(book_id):
    """حذف کتاب با آیدی"""
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()
    return True

def increment_download(book_id):
    """افزایش تعداد دانلود کتاب"""
    c.execute("UPDATE books SET downloads = downloads + 1 WHERE id=?", (book_id,))
    db.commit()
    return True

def search_books(query):
    """جستجوی کتاب‌ها در عنوان، نویسنده، توضیحات و ژانر"""
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        WHERE title LIKE ? OR author LIKE ? OR description LIKE ? OR genre LIKE ?
        ORDER BY created_at DESC
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
    return c.fetchall()

def get_books_by_genre(genre):
    """دریافت کتاب‌های یک ژانر خاص"""
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        WHERE genre = ?
        ORDER BY created_at DESC
    """, (genre,))
    return c.fetchall()

def get_book_count():
    """تعداد کل کتاب‌ها"""
    c.execute("SELECT COUNT(*) FROM books")
    return c.fetchone()[0]

def get_total_downloads():
    """تعداد کل دانلودها"""
    c.execute("SELECT SUM(downloads) FROM books")
    result = c.fetchone()[0]
    return result if result else 0

def get_popular_books(limit=5):
    """دریافت کتاب‌های پربازدید"""
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        ORDER BY downloads DESC
        LIMIT ?
    """, (limit,))
    return c.fetchall()

# ========================================
# ========================================
# ===== توابع کانال‌ها =====
# ========================================
# ========================================

def add_channel(username):
    """افزودن کانال به لیست عضویت اجباری"""
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()
    return True

def get_channels():
    """دریافت لیست کانال‌های اجباری"""
    c.execute("SELECT username FROM channels")
    return [row[0] for row in c.fetchall()]

def delete_channel(username):
    """حذف کانال از لیست عضویت اجباری"""
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()
    return True

def get_channels_count():
    """تعداد کانال‌های اجباری"""
    c.execute("SELECT COUNT(*) FROM channels")
    return c.fetchone()[0]

# ========================================
# ========================================
# ===== توابع بنر =====
# ========================================
# ========================================

def set_banner(banner_type, file_id=None, text=""):
    """تنظیم بنر جدید (جایگزین بنر قبلی)"""
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?,?,?)", (banner_type, file_id, text))
    db.commit()
    return True

def get_banner():
    """دریافت بنر فعلی"""
    c.execute("SELECT type, file_id, text FROM banner")
    row = c.fetchone()
    if row:
        return {"type": row[0], "file_id": row[1], "text": row[2] or ""}
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner():
    """حذف بنر فعلی"""
    c.execute("DELETE FROM banner")
    db.commit()
    return True

# ========================================
# ========================================
# ===== توابع کاربران =====
# ========================================
# ========================================

def add_user(user_id, username="", full_name=""):
    """ثبت کاربر جدید در دیتابیس"""
    now = datetime.now().isoformat()
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, username, full_name, join_date)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, full_name, now))
    db.commit()
    return True

def get_all_users():
    """دریافت لیست همه کاربران"""
    c.execute("SELECT user_id, username, full_name, join_date FROM users")
    return c.fetchall()

def get_user_count():
    """تعداد کل کاربران"""
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

def get_user(user_id):
    """دریافت اطلاعات یک کاربر"""
    c.execute("SELECT user_id, username, full_name, join_date FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

# ========================================
# ========================================
# ===== توابع رمز فایل (جدید) =====
# ========================================
# ========================================

def add_password_file(name, password, file_id, file_type="document", caption=""):
    """افزودن فایل با رمز"""
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO password_files (name, password, file_id, file_type, caption, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, password, file_id, file_type, caption, now))
    db.commit()
    return c.lastrowid

def get_password_file_by_code(code):
    """دریافت فایل با رمز"""
    c.execute("SELECT id, name, file_id, file_type, caption FROM password_files WHERE password=?", (code,))
    return c.fetchone()

def get_all_password_files():
    """دریافت لیست همه فایل‌های رمزدار"""
    c.execute("SELECT id, name, password, file_type FROM password_files ORDER BY created_at DESC")
    return c.fetchall()

def delete_password_file(file_id):
    """حذف فایل رمزدار"""
    c.execute("DELETE FROM password_files WHERE id=?", (file_id,))
    db.commit()

# ========================================
# ========================================
# ===== توابع فعالیت ادمین‌ها (جدید) =====
# ========================================
# ========================================

def add_admin_activity(admin_id, action, details=""):
    """ثبت فعالیت ادمین"""
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO admin_activities (admin_id, action, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (admin_id, action, details, now))
    db.commit()

def get_admin_activities(admin_id=None, limit=20):
    """دریافت فعالیت‌های ادمین"""
    if admin_id:
        c.execute("""
            SELECT id, action, details, created_at FROM admin_activities
            WHERE admin_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (admin_id, limit))
    else:
        c.execute("""
            SELECT id, admin_id, action, details, created_at FROM admin_activities
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
    return c.fetchall()

# ========================================
# ========================================
# ===== توابع کمکی =====
# ========================================
# ========================================

def backup_db():
    """گرفتن بکاپ از دیتابیس"""
    import shutil
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, f"{DB_PATH}.backup")
        return True
    return False

def restore_db():
    """بازیابی دیتابیس از بکاپ"""
    import shutil
    if os.path.exists(f"{DB_PATH}.backup"):
        shutil.copy(f"{DB_PATH}.backup", DB_PATH)
        return True
    return False

def clear_all_data():
    """پاک کردن همه داده‌ها (فقط برای مدیریت)"""
    c.execute("DELETE FROM books")
    c.execute("DELETE FROM channels")
    c.execute("DELETE FROM banner")
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM password_files")
    c.execute("DELETE FROM admin_activities")
    db.commit()
    return True

def get_db_stats():
    """دریافت آمار کامل دیتابیس"""
    return {
        "books": get_book_count(),
        "channels": get_channels_count(),
        "users": get_user_count(),
        "total_downloads": get_total_downloads(),
        "password_files": len(get_all_password_files())
    }

print("✅ تمام توابع دیتابیس بارگذاری شدند!")
print(f"📁 مسیر دیتابیس: {DB_PATH}")
