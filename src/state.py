"""Botning global holati: postlar yuborilishi yoqilgan/o'chirilgan, va joriy kanallar ro'yxati."""

import random

from src import config

_is_running = True

# Runtime'da o'zgaradigan kanallar ro'yxati (dastlab config.CHANNELS dan nusxalanadi).
# DIQQAT: bu faqat xotirada saqlanadi — Railway qayta deploy qilinsa,
# ro'yxat yana CHANNELS muhit o'zgaruvchisidagi holatga qaytadi.
_channels: list[config.ChannelConfig] = list(config.CHANNELS)

# Har bir kanal uchun ishlatilgan aniq kichik mavzular (subtopic) ro'yxati.
# Shu orqali bir xil subtopic ketma-ket takrorlanmaydi.
_used_subtopics: dict[str, list[str]] = {}
_subtopic_queue: dict[str, list[str]] = {}


def is_running() -> bool:
    return _is_running


def start():
    global _is_running
    _is_running = True


def stop():
    global _is_running
    _is_running = False


def get_channels() -> list[config.ChannelConfig]:
    return _channels


def remove_channel(target: str):
    global _channels
    _channels = [c for c in _channels if c.target != target]


def pick_subtopic(target: str, pool: list[str]) -> str:
    """
    Berilgan pool (kichik mavzular ro'yxati)dan, oxirgi ishlatilganlarni
    takrorlamaydigan tarzda bittasini tanlaydi. Pool tugasa, qayta aralashtiradi.
    """
    queue = _subtopic_queue.get(target)
    if not queue:
        queue = list(pool)
        random.shuffle(queue)
        _subtopic_queue[target] = queue

    subtopic = _subtopic_queue[target].pop()
    return subtopic
