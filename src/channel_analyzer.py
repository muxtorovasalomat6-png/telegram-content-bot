"""
Kanal tahlilchisi: ochiq (public) Telegram kanalining so'nggi postlarini
o'qib, Gemini yordamida qanday mavzularda yozilganini aniqlaydi.

Telegram Bot API kanal tarixini o'qishga ruxsat bermaydi, shuning uchun
ochiq kanallar uchun mavjud bo'lgan https://t.me/s/<username> ko'rinishidagi
ommaviy preview sahifasidan foydalanamiz (faqat public kanallar uchun ishlaydi).
"""

import re
import logging
from html import unescape

import httpx
from google import genai

from src import config

logger = logging.getLogger(__name__)

client = genai.Client(api_key=config.GEMINI_API_KEY)

_POST_TEXT_RE = re.compile(
    r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.DOTALL
)
_TAG_RE = re.compile(r"<[^>]+>")


def _extract_username(channel: str) -> str | None:
    """'@kanal', 'kanal', yoki 'https://t.me/kanal' dan username ajratib oladi."""
    channel = channel.strip()
    if channel.startswith("http"):
        match = re.search(r"t\.me/(?:s/)?([A-Za-z0-9_]+)", channel)
        return match.group(1) if match else None
    return channel.lstrip("@")


def fetch_recent_posts(channel: str, limit: int = 20) -> list[str]:
    """Public kanalning so'nggi post matnlarini qaytaradi. Yopiq kanal bo'lsa bo'sh ro'yxat."""
    username = _extract_username(channel)
    if not username:
        logger.warning(f"Kanal username aniqlanmadi: {channel}")
        return []

    url = f"https://t.me/s/{username}"
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
    except Exception:
        logger.exception(f"{url} manzilidan o'qib bo'lmadi (kanal yopiq yoki mavjud emas)")
        return []

    raw_texts = _POST_TEXT_RE.findall(resp.text)
    posts = []
    for raw in raw_texts[-limit:]:
        text = _TAG_RE.sub(" ", raw)
        text = unescape(text).strip()
        if text:
            posts.append(text)
    return posts


def analyze_topics(channel: str) -> str:
    """
    Kanalning so'nggi postlariga qarab, u qanday mavzu(lar)da yozishini
    qisqa tavsif ko'rinishida qaytaradi. Agar postlar topilmasa, umumiy
    tavsif qaytaradi.
    """
    posts = fetch_recent_posts(channel)

    if not posts:
        logger.info(f"'{channel}' uchun postlar topilmadi, umumiy mavzu ishlatiladi")
        return "foydali va qiziqarli umumiy ma'lumotlar"

    sample = "\n---\n".join(posts[:15])
    prompt = (
        "Quyida bitta Telegram kanalining so'nggi postlari keltirilgan. "
        "Ularga qarab, bu kanal asosan qaysi mavzu(lar)da post qilishini "
        "1-2 qisqa jumlada, o'zbek tilida tasvirlab ber. Faqat tavsifni yoz, "
        "boshqa izoh kerak emas.\n\n"
        f"{sample}"
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    topic_summary = response.text.strip()
    logger.info(f"'{channel}' uchun aniqlangan mavzu: {topic_summary}")
    return topic_summary
