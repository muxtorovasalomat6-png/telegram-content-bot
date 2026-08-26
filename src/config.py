import os
from dotenv import load_dotenv

load_dotenv()

# Bu qiymatlar hech qachon kodga yozilmaydi — faqat Railway'ning
# Environment Variables bo'limidan o'qiladi.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Post yuboriladigan kanal yoki guruh ID/username (masalan: @mening_kanalim yoki -1001234567890)
TARGET_CHAT_ID = os.environ.get("TARGET_CHAT_ID", "")

# Kuniga nechta post yuborish (min-max)
MIN_POSTS_PER_DAY = int(os.environ.get("MIN_POSTS_PER_DAY", "3"))
MAX_POSTS_PER_DAY = int(os.environ.get("MAX_POSTS_PER_DAY", "7"))

# Postlar qaysi soatlar oralig'ida yuborilishi mumkin (0-23)
ACTIVE_HOUR_START = int(os.environ.get("ACTIVE_HOUR_START", "9"))
ACTIVE_HOUR_END = int(os.environ.get("ACTIVE_HOUR_END", "22"))

REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "TARGET_CHAT_ID": TARGET_CHAT_ID,
}


def validate_config():
    missing = [name for name, value in REQUIRED_VARS.items() if not value]
    if missing:
        raise RuntimeError(
            f"Quyidagi muhit o'zgaruvchilari o'rnatilmagan: {', '.join(missing)}. "
            "Railway loyihasida Variables bo'limiga qo'shing."
        )
