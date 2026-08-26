"""
Kontent generatori: har bir kanal uchun (aniqlangan yoki qo'lda belgilangan)
mavzuga mos matn va rasm yaratadi.
"""

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


def generate_caption(topic: str) -> str:
    prompt = (
        f"Sen Telegram kanal uchun kontent yozuvchisan. Bu kanal odatda "
        f"quyidagi mavzu(lar)da post qiladi: '{topic}'. "
        f"Shu mavzu doirasida qisqa, foydali va o'quvchini qiziqtiradigan yangi post yoz. "
        f"Talablar: o'zbek tilida, 4-8 qator, mos emojilar bilan, oxirida 2-3 ta hashtag. "
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


import json


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
