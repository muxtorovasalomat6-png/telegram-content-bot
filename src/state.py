"""Botning global holati: postlar yuborilishi yoqilgan/o'chirilgan."""

_is_running = True


def is_running() -> bool:
    return _is_running


def start():
    global _is_running
    _is_running = True


def stop():
    global _is_running
    _is_running = False
