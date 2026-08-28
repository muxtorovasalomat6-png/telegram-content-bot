"""
Kontent generatori: har bir kanal uchun (aniqlangan yoki qo'lda belgilangan)
mavzuga mos matn va rasm yaratadi.
"""

import json
import logging

from google import genai
from google.genai import types

from src import config

logger = logging.getLogger(__name__)

client = genai.Client(api_key=config.GEMINI_API_KEY)

TEXT_MODEL = "gemini-3.6-flash"
IMAGE_MODEL = "gemini-3.1-flash-image"

# auto_topic=False va fixed_topic ham berilmagan hollarda ishlatiladigan zaxira mavzular
FALLBACK_TOPICS = [
    "foydali kundalik maslahatlar",
    "sog'lom turmush tarzi",
    "shaxsiy rivojlanish",
    "zamonaviy texnologiyalar",
]

# Asosiy mavzu (masalan "kiberxavfsizlik") uchun aniq kichik mavzular (subtopic) ro'yxati.
# Kalit — asosiy mavzu nomi bilan bir xil bo'lishi shart emas, faqat mos kelishi kerak.
SUBTOPIC_POOLS: dict[str, list[str]] = {
    "kiberxavfsizlik": [
        "Ikki bosqichli tasdiqlash (2FA) nima va nega kerak",
        "Kuchli parol qanday tuzilishi kerak",
        "Fishing (aldov xatlar) qanday aniqlanadi",
        "Ijtimoiy tarmoqlarda shaxsiy ma'lumotlarni himoya qilish",
        "Ochiq Wi-Fi tarmoqlaridan foydalanish xavfi",
        "Telefon va kompyuterni zararli dasturlardan himoya qilish",
        "Bank kartasi ma'lumotlarini internetda himoya qilish",
        "Bolalar internetda xavfsizligi",
        "Parol menejerlaridan foydalanish foydalari",
        "Internetda shaxsni o'g'irlash (identity theft) qanday oldini olish mumkin",
        "Kiberjinoyatchilik nima va uning turlari",
        "Internetda javobgarlik: nima yozish mumkin, nima mumkin emas",
        "Ijtimoiy muhandislik (social engineering) firibgarligi",
        "Dasturiy ta'minotni yangilab turish nega muhim",
        "Bolalar va o'smirlar uchun kiberbulling (onlayn tahdid)dan himoya",
    ],
}


def generate_caption(topic: str) -> str:
    prompt = (
        f"Sen professional Telegram kanal uchun kontent yozuvchisan. Bu kanal odatda "
        f"quyidagi mavzu(lar)da post qiladi: '{topic}'. "
        f"Shu mavzu doirasida chuqurroq, foydali va o'quvchini qiziqtiradigan yangi post yoz. "
        f"Talablar:\n"
        f"- O'zbek tilida\n"
        f"- Kamida 8-12 qator (juda qisqa bo'lmasin, mavzuni yetarlicha ochib ber)\n"
        f"- Jozibali sarlavha bilan boshlansin (masalan qalin matn yoki emoji bilan)\n"
        f"- 2-4 ta aniq maslahat yoki fakt keltir (ro'yxat yoki alohida qatorlar bilan)\n"
        f"- Mos joylarda emojilar ishlat\n"
        f"- Oxirida qisqa xulosa yoki chaqiriq (call-to-action) yoz\n"
        f"- Eng oxirida 2-3 ta tegishli hashtag qo'y\n"
        f"Faqat post matnini qaytar, boshqa izoh yozma."
    )
    response = client.models.generate_content(model=TEXT_MODEL, contents=prompt)
    return response.text.strip()


def generate_image(topic: str) -> bytes | None:
    prompt = (
        f"Create a clean, modern, professional social-media graphic related to: {topic}. "
        f"Style: minimalistic, flat design, high contrast, no watermark, no text errors. "
        f"The image should visually represent the topic in an engaging way."
    )
    try:
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data
    except Exception:
        logger.exception("Rasm generatsiyasida xatolik yuz berdi")
    return None


def generate_poll(topic: str) -> dict | None:
    """
    Mavzuga mos so'rovnoma (poll) yaratadi: bitta savol + 2-4 ta variant.
    Muvaffaqiyatsiz bo'lsa None qaytaradi.
    """
    prompt = (
        f"'{topic}' mavzusida Telegram so'rovnomasi (poll) uchun bitta qiziqarli "
        f"savol va 2-4 ta qisqa javob varianti yoz. O'zbek tilida. "
        f"FAQAT quyidagi JSON formatida javob ber, boshqa hech narsa yozma:\n"
        f'{{"question": "...", "options": ["...", "..."]}}'
    )
    try:
        response = client.models.generate_content(model=TEXT_MODEL, contents=prompt)
        text = response.text.strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        if data.get("question") and len(data.get("options", [])) >= 2:
            return {"question": data["question"], "options": data["options"][:10]}
    except Exception:
        logger.exception("So'rovnoma generatsiyasida xatolik yuz berdi")
    return None


def generate_post(topic: str) -> tuple[str, bytes | None]:
    caption = generate_caption(topic)
    image_bytes = generate_image(topic)
    return caption, image_bytes
