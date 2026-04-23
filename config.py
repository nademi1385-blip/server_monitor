import os

# توکن ربات تلگرام
TELEGRAM_BOT_TOKEN = "توکن خود را اینجا قرار بدهید "
TELEGRAM_CHAT_ID = "آیدی چت خ.د را اینجا قرار بدهید"  # با @userinfobot پیدا کن

# تنظیمات مانیتورینگ
CPU_THRESHOLD = 80      # هشدار وقتی CPU از 80% بیشتر بشه
RAM_THRESHOLD = 80     # هشدار وقتی RAM از 80% بیشتر بشه
DISK_THRESHOLD = 85      # هشدار وقتی دیسک از 85% پر بشه
TEMP_THRESHOLD = 80      # هشدار وقتی دما از 80°C بیشتر بشه
PING_THRESHOLD = 200     # هشدار وقتی پینگ بیشتر از 200ms بشه
BATTERY_THRESHOLD = 20   # هشدار وقتی باتری زیر 20% برسه
CHECK_INTERVAL = 60      # چک کردن هر 60 ثانیه

# تنظیمات وب داشبورد
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
DEBUG_MODE = False

# پوشه‌ها
LOG_DIR = "logs"

# ساخت پوشه‌ها
os.makedirs(LOG_DIR, exist_ok=True)