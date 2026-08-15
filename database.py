# database.py

import os
import shutil
import sqlite3
from datetime import datetime


# ========================================
# ⚙️ تنظیمات دیتابیس
# ========================================

DB_PATH = os.getenv("DB_PATH", "bot.db")
BACKUP_PATH = f"{DB_PATH}.backup"


# ========================================
# 🔌 اتصال به دیتابیس
# ========================================

db = sqlite3.connect(
    DB_PATH,
    check_same_thread=False
)

db.row_factory = sqlite3.Row

c = db.cursor()


# ========================================
# 🛠 ساخت جدول‌ها
# ========================================

# ----------------------------------------
# 📚 کتاب‌ها
# ----------------------------------------

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
    file_size INTEGER DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    created_at TEXT
)
""")


# ----------------------------------------
# 📢 کانال‌های اجباری
# ----------------------------------------

c.execute("""
CREATE TABLE IF NOT EXISTS channels (
    username TEXT PRIMARY KEY
)
""")


# ----------------------------------------
# 🎨 بنر
# ----------------------------------------

c.execute("""
CREATE TABLE IF NOT EXISTS banner (
    type TEXT DEFAULT 'text',
    file_id TEXT,
    text TEXT
)
""")


# ----------------------------------------
# 👥 کاربران
# ----------------------------------------

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    join_date TEXT
)
""")


# ----------------------------------------
# 🔐 فایل‌های رمزدار
# ----------------------------------------

c.execute("""
CREATE TABLE IF NOT EXISTS password_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    password TEXT NOT NULL UNIQUE,
    file_id TEXT NOT NULL,
    file_type TEXT DEFAULT 'document',
    caption TEXT,
    created_at TEXT
)
""")


# ----------------------------------------
# 👨‍💻 فعالیت ادمین‌ها
# ----------------------------------------

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


# ========================================
# 🧹 ابزار داخلی
# ========================================

def now():
    return datetime.now().isoformat()


# ========================================
# 📚 توابع کتاب‌ها
# ========================================

def add_book(
    title,
    author="",
    description="",
    genre="",
    cover_file_id="",
    file_id="",
    file_name="",
    file_size=0
):
    """افزودن کتاب"""

    c.execute("""
        INSERT INTO books (
            title,
            author,
            description,
            genre,
            cover_file_id,
            file_id,
            file_name,
            file_size,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        author,
        description,
        genre,
        cover_file_id,
        file_id,
        file_name,
        file_size,
        now()
    ))

    db.commit()

    return c.lastrowid


def get_all_books():
    """دریافت تمام کتاب‌ها"""

    c.execute("""
        SELECT
            id,
            title,
            author,
            description,
            genre,
            cover_file_id,
            file_id,
            file_name,
            downloads
        FROM books
        ORDER BY created_at DESC
    """)

    return [tuple(row) for row in c.fetchall()]


def get_book(book_id):
    """دریافت یک کتاب"""

    c.execute("""
        SELECT
            id,
            title,
            author,
            description,
            genre,
            cover_file_id,
            file_id,
            file_name,
            downloads
        FROM books
        WHERE id = ?
    """, (book_id,))

    row = c.fetchone()

    return tuple(row) if row else None


def delete_book(book_id):
    """حذف کتاب"""

    c.execute(
        "DELETE FROM books WHERE id = ?",
        (book_id,)
    )

    db.commit()

    return c.rowcount > 0


def increment_download(book_id):
    """افزایش تعداد دانلود"""

    c.execute("""
        UPDATE books
        SET downloads = downloads + 1
        WHERE id = ?
    """, (book_id,))

    db.commit()

    return c.rowcount > 0


def search_books(query):
    """جستجو در کتاب‌ها"""

    pattern = f"%{query}%"

    c.execute("""
        SELECT
            id,
            title,
            author,
            description,
            genre,
            cover_file_id,
            file_id,
            file_name,
            downloads
        FROM books
        WHERE
            title LIKE ?
            OR author LIKE ?
            OR description LIKE ?
            OR genre LIKE ?
        ORDER BY created_at DESC
    """, (
        pattern,
        pattern,
        pattern,
        pattern
    ))

    return [tuple(row) for row in c.fetchall()]


def get_books_by_genre(genre):
    """دریافت کتاب‌های یک ژانر"""

    c.execute("""
        SELECT
            id,
            title,
            author,
            description,
            genre,
            cover_file_id,
            file_id,
            file_name,
            downloads
        FROM books
        WHERE genre = ?
        ORDER BY created_at DESC
    """, (genre,))

    return [tuple(row) for row in c.fetchall()]


def get_book_count():
    """تعداد کتاب‌ها"""

    c.execute(
        "SELECT COUNT(*) FROM books"
    )

    return c.fetchone()[0]


def get_total_downloads():
    """کل دانلودها"""

    c.execute(
        "SELECT COALESCE(SUM(downloads), 0) FROM books"
    )

    return c.fetchone()[0]


def get_popular_books(limit=5):
    """کتاب‌های محبوب"""

    c.execute("""
        SELECT
            id,
            title,
            author,
            description,
            genre,
            cover_file_id,
            file_id,
            file_name,
            downloads
        FROM books
        ORDER BY downloads DESC
        LIMIT ?
    """, (limit,))

    return [tuple(row) for row in c.fetchall()]


# ========================================
# 📢 کانال‌ها
# ========================================

def add_channel(username):
    """افزودن کانال"""

    username = username.strip().replace("@", "")

    if not username:
        return False

    c.execute("""
        INSERT OR IGNORE INTO channels (username)
        VALUES (?)
    """, (username,))

    db.commit()

    return True


def get_channels():
    """لیست کانال‌ها"""

    c.execute("""
        SELECT username
        FROM channels
        ORDER BY username
    """)

    return [
        row[0]
        for row in c.fetchall()
    ]


def delete_channel(username):
    """حذف کانال"""

    username = username.strip().replace("@", "")

    c.execute("""
        DELETE FROM channels
        WHERE username = ?
    """, (username,))

    db.commit()

    return c.rowcount > 0


def get_channels_count():
    """تعداد کانال‌ها"""

    c.execute(
        "SELECT COUNT(*) FROM channels"
    )

    return c.fetchone()[0]


# ========================================
# 🎨 بنر
# ========================================

def set_banner(
    banner_type,
    file_id=None,
    text=""
):
    """تنظیم بنر"""

    c.execute(
        "DELETE FROM banner"
    )

    c.execute("""
        INSERT INTO banner (
            type,
            file_id,
            text
        )
        VALUES (?, ?, ?)
    """, (
        banner_type,
        file_id,
        text
    ))

    db.commit()

    return True


def get_banner():
    """دریافت بنر"""

    c.execute("""
        SELECT type, file_id, text
        FROM banner
        LIMIT 1
    """)

    row = c.fetchone()

    if row:
        return {
            "type": row[0],
            "file_id": row[1],
            "text": row[2] or ""
        }

    return {
        "type": "text",
        "file_id": None,
        "text": "📚 به ربات کتاب خوش آمدید!"
    }


def delete_banner():
    """حذف بنر"""

    c.execute(
        "DELETE FROM banner"
    )

    db.commit()

    return True


# ========================================
# 👥 کاربران
# ========================================

def add_user(
    user_id,
    username="",
    full_name=""
):
    """ثبت یا بروزرسانی کاربر"""

    current = now()

    c.execute("""
        INSERT INTO users (
            user_id,
            username,
            full_name,
            join_date
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
    """, (
        user_id,
        username,
        full_name,
        current
    ))

    db.commit()

    return True


def get_all_users():
    """تمام کاربران"""

    c.execute("""
        SELECT
            user_id,
            username,
            full_name,
            join_date
        FROM users
        ORDER BY join_date DESC
    """)

    return [
        tuple(row)
        for row in c.fetchall()
    ]


def get_user_count():
    """تعداد کاربران"""

    c.execute(
        "SELECT COUNT(*) FROM users"
    )

    return c.fetchone()[0]


def get_user(user_id):
    """دریافت کاربر"""

    c.execute("""
        SELECT
            user_id,
            username,
            full_name,
            join_date
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    row = c.fetchone()

    return tuple(row) if row else None


# ========================================
# 🔐 فایل‌های رمزدار
# ========================================

def add_password_file(
    name,
    password,
    file_id,
    file_type="document",
    caption=""
):
    """افزودن فایل رمزدار"""

    try:

        c.execute("""
            INSERT INTO password_files (
                name,
                password,
                file_id,
                file_type,
                caption,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            password,
            file_id,
            file_type,
            caption,
            now()
        ))

        db.commit()

        return c.lastrowid

    except sqlite3.IntegrityError:
        return None


def get_password_file_by_code(code):
    """دریافت فایل با رمز"""

    c.execute("""
        SELECT
            id,
            name,
            file_id,
            file_type,
            caption
        FROM password_files
        WHERE password = ?
    """, (code,))

    row = c.fetchone()

    return tuple(row) if row else None


def get_all_password_files():
    """تمام فایل‌های رمزدار"""

    c.execute("""
        SELECT
            id,
            name,
            password,
            file_type
        FROM password_files
        ORDER BY created_at DESC
    """)

    return [
        tuple(row)
        for row in c.fetchall()
    ]


def delete_password_file(file_id):
    """حذف فایل رمزدار"""

    c.execute("""
        DELETE FROM password_files
        WHERE id = ?
    """, (file_id,))

    db.commit()

    return c.rowcount > 0


def get_password_file_count():
    """تعداد فایل‌های رمزدار"""

    c.execute(
        "SELECT COUNT(*) FROM password_files"
    )

    return c.fetchone()[0]


# ========================================
# 👨‍💻 فعالیت ادمین
# ========================================

def add_admin_activity(
    admin_id,
    action,
    details=""
):
    """ثبت فعالیت ادمین"""

    c.execute("""
        INSERT INTO admin_activities (
            admin_id,
            action,
            details,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        admin_id,
        action,
        details,
        now()
    ))

    db.commit()

    return True


def get_admin_activities(
    admin_id=None,
    limit=20
):
    """دریافت فعالیت‌های ادمین"""

    if admin_id:

        c.execute("""
            SELECT
                id,
                action,
                details,
                created_at
            FROM admin_activities
            WHERE admin_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (
            admin_id,
            limit
        ))

    else:

        c.execute("""
            SELECT
                id,
                admin_id,
                action,
                details,
                created_at
            FROM admin_activities
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    return [
        tuple(row)
        for row in c.fetchall()
    ]


# ========================================
# 💾 بکاپ
# ========================================

def backup_db():
    """گرفتن بکاپ از دیتابیس"""

    try:

        db.commit()

        if not os.path.exists(DB_PATH):
            return False

        shutil.copy2(
            DB_PATH,
            BACKUP_PATH
        )

        return True

    except Exception as e:

        print(
            f"❌ Backup error: {e}"
        )

        return False


# ========================================
# ♻️ Restore
# ========================================

def restore_db():
    """
    بازیابی بکاپ.

    بعد از Restore بهتر است ربات Restart شود،
    چون فایل دیتابیس جایگزین می‌شود.
    """

    try:

        if not os.path.exists(BACKUP_PATH):
            return False

        db.commit()

        # بستن اتصال فعلی
        db.close()

        shutil.copy2(
            BACKUP_PATH,
            DB_PATH
        )

        return True

    except Exception as e:

        print(
            f"❌ Restore error: {e}"
        )

        return False


# ========================================
# 🧹 پاک کردن تمام اطلاعات
# ========================================

def clear_all_data():
    """پاک کردن تمام داده‌ها"""

    tables = [
        "books",
        "channels",
        "banner",
        "users",
        "password_files",
        "admin_activities"
    ]

    for table in tables:
        c.execute(
            f"DELETE FROM {table}"
        )

    db.commit()

    return True


# ========================================
# 📊 آمار دیتابیس
# ========================================

def get_db_stats():
    """آمار کامل دیتابیس"""

    return {
        "books": get_book_count(),
        "channels": get_channels_count(),
        "users": get_user_count(),
        "total_downloads": get_total_downloads(),
        "password_files": get_password_file_count()
    }


# ========================================
# 🔄 بستن دیتابیس
# ========================================

def close_db():
    """بستن اتصال دیتابیس"""

    try:
        db.commit()
        db.close()
        return True

    except Exception:
        return False


# ========================================
# 🚀 وضعیت دیتابیس
# ========================================

print(
    "✅ Database loaded successfully!"
)

print(
    f"📁 Database: {DB_PATH}"
)
