import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "bot.db")
db = sqlite3.connect(DB_PATH, check_same_thread=False)
c = db.cursor()

# ===== جدول کتاب‌ها =====
c.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        description TEXT,
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

db.commit()

# ========================================
# ===== توابع کتاب =====
# ========================================
def add_book(title, author, description, file_id, file_name="", file_size=0):
    now = datetime.now().isoformat()
    c.execute("""
        INSERT INTO books (title, author, description, file_id, file_name, file_size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, author, description, file_id, file_name, file_size, now))
    db.commit()
    return c.lastrowid

def get_all_books():
    c.execute("SELECT id, title, author, description, file_id, file_name, downloads FROM books ORDER BY created_at DESC")
    return c.fetchall()

def get_book(book_id):
    c.execute("SELECT id, title, author, description, file_id, file_name FROM books WHERE id=?", (book_id,))
    return c.fetchone()

def delete_book(book_id):
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()

def increment_download(book_id):
    c.execute("UPDATE books SET downloads = downloads + 1 WHERE id=?", (book_id,))
    db.commit()

def search_books(query):
    c.execute("""
        SELECT id, title, author, description, file_id, file_name, downloads
        FROM books
        WHERE title LIKE ? OR author LIKE ? OR description LIKE ?
        ORDER BY created_at DESC
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))
    return c.fetchall()

# ========================================
# ===== توابع کانال‌ها =====
# ========================================
def add_channel(username):
    c.execute("INSERT OR IGNORE INTO channels VALUES (?)", (username,))
    db.commit()

def get_channels():
    c.execute("SELECT username FROM channels")
    return [row[0] for row in c.fetchall()]

def delete_channel(username):
    c.execute("DELETE FROM channels WHERE username=?", (username,))
    db.commit()

# ========================================
# ===== توابع بنر =====
# ========================================
def set_banner(banner_type, file_id=None, text=""):
    c.execute("DELETE FROM banner")
    c.execute("INSERT INTO banner VALUES (?,?,?)", (banner_type, file_id, text))
    db.commit()

def get_banner():
    c.execute("SELECT type, file_id, text FROM banner")
    row = c.fetchone()
    if row:
        return {"type": row[0], "file_id": row[1], "text": row[2] or ""}
    return {"type": "text", "file_id": None, "text": "📢 به ربات خوش اومدی!"}

def delete_banner():
    c.execute("DELETE FROM banner")
    db.commit()
