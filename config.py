import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8255361263))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # کلید جیمینای (اختیاری)
