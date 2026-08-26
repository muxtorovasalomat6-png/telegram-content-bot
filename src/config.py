import os
import json
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Faqat shu Telegram foydalanuvchi ID'i botni tugmalar orqali boshqara oladi.
# @userinfobot orqali o'z ID'ingizni oling.
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

MIN_POSTS_PER_DAY = int(os.environ.get("MIN_POSTS_PER_DAY", "3"))
MAX_POSTS_PER_DAY = int(os.environ.get("MAX_POSTS_PER_DAY", "7"))
ACTIVE_HOUR_START = int(os.environ.get("ACTIVE_HOUR_START", "9"))
ACTIVE_HOUR_END = int(os.environ.get("ACTIVE_HOUR_END", "22"))


@dataclass
class ChannelConfig:
    # Post yuboriladigan kanal/guruh (masalan @mening_kanalim yoki -100123...)
    target: str
    # Mavzuni aniqlash uchun tahlil qilinadigan ochiq kanal (odatda target bilan bir xil).
    # Agar berilmasa, tahlil qilinmaydi va random umumiy mavzulardan foydalaniladi.
    analyze_source: str | None = None
    # True bo'lsa, har kuni kanal qayta tahlil qilinadi va mavzu yangilanadi.
    auto_topic: bool = True
    # auto_topic=False bo'lsa, shu qo'lda belgilangan mavzu ishlatiladi.
    fixed_topic: str | None = None


def _load_channels() -> list[ChannelConfig]:
    """
    CHANNELS muhit o'zgaruvchisidan JSON ro'yxatni o'qiydi. Masalan:
    [
      {"target": "@xavfsizlikuz_channel", "auto_topic": false, "fixed_topic": "kiberxavfsizlik"},
      {"target": "@ikkinchi_kanal", "analyze_source": "@ikkinchi_kanal", "auto_topic": true}
    ]

    Agar CHANNELS berilmagan bo'lsa, eski TARGET_CHAT_ID o'zgaruvchisi bilan
    orqaga moslik (backward compatibility) ta'minlanadi.
    """
    raw = os.environ.get("CHANNELS", "").strip()
    if raw:
        try:
            data = json.loads(raw)
            return [ChannelConfig(**item) for item in data]
        except Exception as e:
            raise RuntimeError(f"CHANNELS o'zgaruvchisini o'qishda xatolik: {e}")

    # Orqaga moslik: eski bitta-kanal sozlamasi
    legacy_target = os.environ.get("TARGET_CHAT_ID", "")
    if legacy_target:
        return [ChannelConfig(target=legacy_target, analyze_source=None, auto_topic=False, fixed_topic=None)]

    return []


CHANNELS: list[ChannelConfig] = _load_channels()

REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "OWNER_ID": str(OWNER_ID) if OWNER_ID else "",
}


def validate_config():
    missing = [name for name, value in REQUIRED_VARS.items() if not value]
    if missing:
        raise RuntimeError(
            f"Quyidagi muhit o'zgaruvchilari o'rnatilmagan: {', '.join(missing)}. "
            "Railway loyihasida Variables bo'limiga qo'shing."
        )
    if not CHANNELS:
        raise RuntimeError(
            "Hech qanday kanal sozlanmagan. CHANNELS (JSON) yoki TARGET_CHAT_ID ni o'rnating."
        )
