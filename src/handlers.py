"""
Faqat bot egasi (OWNER_ID) uchun ishlaydigan boshqaruv paneli.
Boshqa har qanday foydalanuvchidan kelgan xabarlar butunlay e'tiborsiz qoldiriladi.
"""

import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src import config, state

logger = logging.getLogger(__name__)

router = Router()


def _owner_only(user_id: int) -> bool:
    return config.OWNER_ID != 0 and user_id == config.OWNER_ID


def _panel_keyboard() -> InlineKeyboardMarkup:
    if state.is_running():
        toggle_btn = InlineKeyboardButton(text="⏸ To'xtatish", callback_data="bot_stop")
    else:
        toggle_btn = InlineKeyboardButton(text="▶️ Ishga tushirish", callback_data="bot_start")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [toggle_btn],
            [InlineKeyboardButton(text="📊 Holat", callback_data="bot_status")],
        ]
    )


def _status_text() -> str:
    holat = "🟢 Ishlayapti" if state.is_running() else "🔴 To'xtatilgan"
    kanallar = "\n".join(f"• {c.target}" for c in config.CHANNELS) or "— hech qanday kanal sozlanmagan —"
    return (
        f"<b>Bot holati:</b> {holat}\n\n"
        f"<b>Ulangan kanallar:</b>\n{kanallar}\n\n"
        f"Kuniga {config.MIN_POSTS_PER_DAY}-{config.MAX_POSTS_PER_DAY} ta post, "
        f"soat {config.ACTIVE_HOUR_START}:00-{config.ACTIVE_HOUR_END}:00 oralig'ida."
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not _owner_only(message.from_user.id):
        return  # boshqa hech kimga javob berilmaydi
    await message.answer(_status_text(), reply_markup=_panel_keyboard())


@router.callback_query(F.data == "bot_stop")
async def cb_stop(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    state.stop()
    await callback.message.edit_text(_status_text(), reply_markup=_panel_keyboard())
    await callback.answer("Bot to'xtatildi")


@router.callback_query(F.data == "bot_start")
async def cb_start(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    state.start()
    await callback.message.edit_text(_status_text(), reply_markup=_panel_keyboard())
    await callback.answer("Bot ishga tushirildi")


@router.callback_query(F.data == "bot_status")
async def cb_status(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    await callback.message.edit_text(_status_text(), reply_markup=_panel_keyboard())
    await callback.answer()


@router.message()
async def ignore_everything_else(message: Message):
    # Egasidan bo'lmagan yoki buyruq bo'lmagan har qanday xabar e'tiborsiz qoldiriladi.
    return
