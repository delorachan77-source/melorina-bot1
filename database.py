import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "bot.db")
db = sqlite3.connect(DB_PATH, check_same_thread=False)
c = db.cursor()

# ===== جدول‌ها =====
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

c.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        username TEXT PRIMARY KEY
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS banner (
        type TEXT DEFAULT 'text',
        file_id TEXT,
        text TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        join_date TEXT
    )
""")

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

c.execute("""
    CREATE TABLE IF NOT EXISTS admin_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        details TEXT,
        created_at TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        date TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS robot_ratings (
        user_id INTEGER PRIMARY KEY,
        rating INTEGER,
        date TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        date TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
""")

db.commit()
print("✅ دیتابیس راه‌اندازی شد!")

# ========================================
# ===== توابع کتاب‌ها =====
# ========================================
def add_book(title, author, description, genre, cover_file_id, file_id, file_name="", file_size=0):
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO books (title, author, description, genre, cover_file_id, file_id, file_name, file_size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, author, description, genre, cover_file_id, file_id, file_name, file_size, now))
    db.commit()
    return c.lastrowid

def get_all_books():
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        ORDER BY created_at DESC
    """)
    return c.fetchall()

def get_book(book_id):
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        WHERE id=?
    """, (book_id,))
    return c.fetchone()

def delete_book(book_id):
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()
    return True

def increment_download(book_id):
    c.execute("UPDATE books SET downloads = downloads + 1 WHERE id=?", (book_id,))
    db.commit()
    return True

def search_books(query):
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        WHERE title LIKE ? OR author LIKE ? OR description LIKE ? OR genre LIKE ?
        ORDER BY created_at DESC
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
    return c.fetchall()

def get_books_by_genre(genre):
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        WHERE genre = ?
        ORDER BY created_at DESC
    """, (genre,))
    return c.fetchall()

def get_book_count():
    c.execute("SELECT COUNT(*) FROM books")
    return c.fetchone()[0]

def get_total_downloads():
    c.execute("SELECT SUM(downloads) FROM books")
    result = c.fetchone()[0]
    return result if result else 0

def get_popular_books(limit=5):
    c.execute("""
        SELECT id, title, author, description, genre, cover_file_id, file_id, file_name, downloads
        FROM books
        ORDER BY downloads DESC
        LIMIT ?
    """, (limit,))
    return c.fetchall()

# ========================================
# ===== توابع کانال‌ها =====
# ========================================
def add_channel(username):
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()
    return True

def get_channels():
    c.execute("SELECT username FROM channels")
    return [row[0] for row in c.fetchall()]

def delete_channel(username):
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()
    return True

def get_channels_count():
    c.execute("SELECT COUNT(*) FROM channels")
    return c.fetchone()[0]

# ========================================
# ===== توابع بنر =====
# ========================================
def set_banner(banner_type, file_id=None, text=""):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?,?,?)", (banner_type, file_id, text))
    db.commit()
    return True

def get_banner():
    c.execute("SELECT type, file_id, text FROM banner")
    row = c.fetchone()
    if row:
        return {"type": row[0], "file_id": row[1], "text": row[2] or ""}
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner():
    c.execute("DELETE FROM banner")
    db.commit()
    return True

# ========================================
# ===== توابع کاربران =====
# ========================================
def add_user(user_id, username="", full_name=""):
    now = datetime.now().isoformat()
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, username, full_name, join_date)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, full_name, now))
    db.commit()
    return True

def get_all_users():
    c.execute("SELECT user_id, username, full_name, join_date FROM users")
    return c.fetchall()

def get_user_count():
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

def get_user(user_id):
    c.execute("SELECT user_id, username, full_name, join_date FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

# ========================================
# ===== توابع رمز فایل =====
# ========================================
def add_password_file(name, password, file_id, file_type="document", caption=""):
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO password_files (name, password, file_id, file_type, caption, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, password, file_id, file_type, caption, now))
    db.commit()
    return c.lastrowid

def get_password_file_by_code(code):
    c.execute("SELECT id, name, file_id, file_type, caption FROM password_files WHERE password=?", (code,))
    return c.fetchone()

def get_all_password_files():
    c.execute("SELECT id, name, password, file_type FROM password_files ORDER BY created_at DESC")
    return c.fetchall()

def delete_password_file(file_id):
    c.execute("DELETE FROM password_files WHERE id=?", (file_id,))
    db.commit()

# ========================================
# ===== توابع فعالیت ادمین‌ها =====
# ========================================
def add_admin_activity(admin_id, action, details=""):
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO admin_activities (admin_id, action, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (admin_id, action, details, now))
    db.commit()

def get_admin_activities(admin_id=None, limit=20):
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
# ===== توابع نظرات =====
# ========================================
def add_feedback(user_id, message):
    now = datetime.now().isoformat()
    c.execute("INSERT INTO feedback (user_id, message, date) VALUES (?,?,?)", (user_id, message, now))
    db.commit()

def get_all_feedback():
    c.execute("SELECT id, user_id, message, date FROM feedback ORDER BY date DESC")
    return c.fetchall()

# ========================================
# ===== توابع امتیاز ربات =====
# ========================================
def add_robot_rating(user_id, rating):
    now = datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO robot_ratings VALUES (?,?,?)", (user_id, rating, now))
    db.commit()

def get_robot_ratings():
    c.execute("SELECT rating FROM robot_ratings")
    ratings = c.fetchall()
    if ratings:
        avg = sum(r[0] for r in ratings) / len(ratings)
        return {"avg": round(avg, 1), "count": len(ratings)}
    return {"avg": 0, "count": 0}

# ========================================
# ===== توابع بروزرسانی =====
# ========================================
def add_update(title, content):
    now = datetime.now().isoformat()
    c.execute("INSERT INTO updates (title, content, date) VALUES (?,?,?)", (title, content, now))
    db.commit()

def get_all_updates():
    c.execute("SELECT id, title, content, date FROM updates ORDER BY date DESC")
    return c.fetchall()

# ========================================
# ===== توابع تنظیمات =====
# ========================================
def set_setting(key, value):
    c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, value))
    db.commit()

def get_setting(key):
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    return row[0] if row else None

# ========================================
# ===== توابع کمکی =====
# ========================================
def backup_db():
    import shutil
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, f"{DB_PATH}.backup")
        return True
    return False

def restore_db():
    import shutil
    if os.path.exists(f"{DB_PATH}.backup"):
        shutil.copy(f"{DB_PATH}.backup", DB_PATH)
        return True
    return False

def clear_all_data():
    c.execute("DELETE FROM books")
    c.execute("DELETE FROM channels")
    c.execute("DELETE FROM banner")
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM password_files")
    c.execute("DELETE FROM admin_activities")
    c.execute("DELETE FROM feedback")
    c.execute("DELETE FROM robot_ratings")
    c.execute("DELETE FROM updates")
    c.execute("DELETE FROM settings")
    db.commit()
    return True

def get_db_stats():
    return {
        "books": get_book_count(),
        "channels": get_channels_count(),
        "users": get_user_count(),
        "total_downloads": get_total_downloads(),
        "password_files": len(get_all_password_files())
    }

print("✅ تمام توابع دیتابیس بارگذاری شدند!")
print(f"📁 مسیر دیتابیس: {DB_PATH}")
