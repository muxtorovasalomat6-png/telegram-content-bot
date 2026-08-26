"""Botning global holati: postlar yuborilishi yoqilgan/o'chirilgan, va joriy kanallar ro'yxati."""

from src import config

_is_running = True

# Runtime'da o'zgaradigan kanallar ro'yxati (dastlab config.CHANNELS dan nusxalanadi).
# DIQQAT: bu faqat xotirada saqlanadi — Railway qayta deploy qilinsa,
# ro'yxat yana CHANNELS muhit o'zgaruvchisidagi holatga qaytadi.
_channels: list[config.ChannelConfig] = list(config.CHANNELS)


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
