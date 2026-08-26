"""
Kontent generatori: Gemini orqali turli mavzularda matn va rasm yaratadi.
Har safar tasodifiy mavzu tanlanadi — shu tarzda kanal "hamma yo'nalishda"
kontent bilan boyitiladi.
"""

import base64
import io
import random
import logging

from google import genai
from google.genai import types

from src import config

logger = logging.getLogger(__name__)

client = genai.Client(api_key=config.GEMINI_API_KEY)

# Bot shu mavzular ichidan tasodifiy tanlab, ularga oid post yaratadi.
# Ro'yxatni istalgan vaqtda kengaytirish yoki qisqartirish mumkin.
TOPICS = [
    "kiberxavfsizlik va shaxsiy ma'lumotlarni himoya qilish",
    "sog'lom turmush tarzi va sport",
    "moliyaviy savodxonlik va tejamkorlik",
    "shaxsiy rivojlanish va motivatsiya",
    "zamonaviy texnologiyalar va sun'iy intellekt",
    "ta'lim va o'z-o'zini rivojlantirish",
    "vaqtni boshqarish va samaradorlik",
    "sog'lom ovqatlanish",
    "kundalik foydali maslahatlar (life hacks)",
    "ish va martaba bo'yicha maslahatlar",
]

TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"


def pick_topic() -> str:
    return random.choice(TOPICS)


def generate_caption(topic: str) -> str:
    """Telegram post uchun qisqa, jozibali matn yaratadi (emoji bilan)."""
    prompt = (
        f"Sen Telegram kanal uchun kontent yozuvchisan. "
        f"'{topic}' mavzusida qisqa, foydali va o'quvchini qiziqtiradigan post yoz. "
        f"Talablar: o'zbek tilida, 4-8 qator, mos emojilar bilan, oxirida 2-3 ta hashtag. "
        f"Faqat post matnini qaytar, boshqa izoh yozma."
    )
    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
    )
    return response.text.strip()


def generate_image(topic: str, caption: str) -> bytes | None:
    """Mavzuga mos rasm generatsiya qiladi, PNG bayt ko'rinishida qaytaradi."""
    prompt = (
        f"Create a clean, modern, professional social-media graphic about: {topic}. "
        f"Style: minimalistic, flat design, high contrast, no watermark, no text errors. "
        f"The image should visually represent the topic in an engaging way."
    )
    try:
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data
    except Exception:
        logger.exception("Rasm generatsiyasida xatolik yuz berdi")
    return None


def generate_post() -> tuple[str, bytes | None]:
    """Bitta to'liq post (matn + rasm) yaratadi."""
    topic = pick_topic()
    caption = generate_caption(topic)
    image_bytes = generate_image(topic, caption)
    return caption, image_bytes
