"""
Faqat bot egasi (OWNER_ID) uchun ishlaydigan boshqaruv paneli.
Boshqa har qanday foydalanuvchidan kelgan xabarlar butunlay e'tiborsiz qoldiriladi.
"""

import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src import config
from src import state as bot_state
from src.scheduler import get_today_schedule, cancel_job, cancel_all_for_channel, schedule_one, now_tz

logger = logging.getLogger(__name__)

router = Router()


class AddTime(StatesGroup):
    waiting_for_time = State()
    waiting_for_channel = State()


def _owner_only(user_id: int) -> bool:
    return config.OWNER_ID != 0 and user_id == config.OWNER_ID


def _main_keyboard() -> InlineKeyboardMarkup:
    if bot_state.is_running():
        toggle_btn = InlineKeyboardButton(text="⏸ To'xtatish", callback_data="bot_stop")
    else:
        toggle_btn = InlineKeyboardButton(text="▶️ Ishga tushirish", callback_data="bot_start")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [toggle_btn],
            [InlineKeyboardButton(text="📋 Kanallar", callback_data="show_channels")],
            [InlineKeyboardButton(text="🕐 Bugungi jadval", callback_data="show_schedule")],
            [InlineKeyboardButton(text="📊 Holat", callback_data="bot_status")],
        ]
    )


def _status_text() -> str:
    holat = "🟢 Ishlayapti" if bot_state.is_running() else "🔴 To'xtatilgan"
    kanallar = "\n".join(f"• {c.target}" for c in bot_state.get_channels()) or "— hech qanday kanal yo'q —"
    return (
        f"<b>Bot holati:</b> {holat}\n\n"
        f"<b>Ulangan kanallar:</b>\n{kanallar}\n\n"
        f"Kuniga {config.MIN_POSTS_PER_DAY}-{config.MAX_POSTS_PER_DAY} ta post, "
        f"soat {config.ACTIVE_HOUR_START}:00-{config.ACTIVE_HOUR_END}:00 oralig'ida."
    )


def _channels_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for c in bot_state.get_channels():
        rows.append([InlineKeyboardButton(text=f"❌ {c.target}", callback_data=f"rmchan:{c.target}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _schedule_keyboard() -> InlineKeyboardMarkup:
    schedule = get_today_schedule()
    rows = []
    for target, items in schedule.items():
        rows.append([InlineKeyboardButton(text=f"— {target} —", callback_data="noop")])
        for job_id, t in items:
            rows.append([
                InlineKeyboardButton(
                    text=f"❌ {t.strftime('%H:%M')}", callback_data=f"rmtime:{job_id}"
                )
            ])
    rows.append([InlineKeyboardButton(text="➕ Vaqt qo'shish", callback_data="addtime")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _schedule_text() -> str:
    schedule = get_today_schedule()
    if not schedule:
        return "<b>Bugungi jadval</b>\n\nHozircha rejalashtirilgan post yo'q."
    lines = ["<b>Bugungi jadval:</b>\n"]
    for target, items in schedule.items():
        times = ", ".join(t.strftime("%H:%M") for _, t in items)
        lines.append(f"• {target}: {times}")
    return "\n".join(lines)


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not _owner_only(message.from_user.id):
        return
    await message.answer(_status_text(), reply_markup=_main_keyboard())


@router.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    await callback.message.edit_text(_status_text(), reply_markup=_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "bot_stop")
async def cb_stop(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    bot_state.stop()
    await callback.message.edit_text(_status_text(), reply_markup=_main_keyboard())
    await callback.answer("Bot to'xtatildi")


@router.callback_query(F.data == "bot_start")
async def cb_start(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    bot_state.start()
    await callback.message.edit_text(_status_text(), reply_markup=_main_keyboard())
    await callback.answer("Bot ishga tushirildi")


@router.callback_query(F.data == "bot_status")
async def cb_status(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    await callback.message.edit_text(_status_text(), reply_markup=_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "show_channels")
async def cb_show_channels(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    await callback.message.edit_text(
        "<b>Ulangan kanallar</b>\n\n❌ bosib, kerakli kanalni butunlay uzib tashlashingiz mumkin.",
        reply_markup=_channels_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rmchan:"))
async def cb_remove_channel(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    target = callback.data.split(":", 1)[1]
    bot_state.remove_channel(target)
    cancel_all_for_channel(target)
    await callback.message.edit_text(
        f"✅ {target} kanali uzib tashlandi.\n\n<b>Ulangan kanallar</b>",
        reply_markup=_channels_keyboard(),
    )
    await callback.answer("Kanal uzildi")


@router.callback_query(F.data == "show_schedule")
async def cb_show_schedule(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    await callback.message.edit_text(_schedule_text(), reply_markup=_schedule_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("rmtime:"))
async def cb_remove_time(callback: CallbackQuery):
    if not _owner_only(callback.from_user.id):
        return
    job_id = callback.data.split(":", 1)[1]
    cancel_job(job_id)
    await callback.message.edit_text(_schedule_text(), reply_markup=_schedule_keyboard())
    await callback.answer("Vaqt o'chirildi")


@router.callback_query(F.data == "addtime")
async def cb_add_time_start(callback: CallbackQuery, state: FSMContext):
    if not _owner_only(callback.from_user.id):
        return
    channels = bot_state.get_channels()
    if not channels:
        await callback.answer("Hech qanday kanal yo'q", show_alert=True)
        return
    if len(channels) == 1:
        await state.update_data(target=channels[0].target)
        await state.set_state(AddTime.waiting_for_time)
        await callback.message.edit_text(
            f"{channels[0].target} uchun vaqtni HH:MM ko'rinishida yozing (masalan 18:30):"
        )
        await callback.answer()
        return

    rows = [
        [InlineKeyboardButton(text=c.target, callback_data=f"addtime_chan:{c.target}")]
        for c in channels
    ]
    await state.set_state(AddTime.waiting_for_channel)
    await callback.message.edit_text(
        "Qaysi kanal uchun vaqt qo'shamiz?", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("addtime_chan:"), StateFilter(AddTime.waiting_for_channel))
async def cb_add_time_channel_chosen(callback: CallbackQuery, state: FSMContext):
    if not _owner_only(callback.from_user.id):
        return
    target = callback.data.split(":", 1)[1]
    await state.update_data(target=target)
    await state.set_state(AddTime.waiting_for_time)
    await callback.message.edit_text(f"{target} uchun vaqtni HH:MM ko'rinishida yozing (masalan 18:30):")
    await callback.answer()


@router.message(StateFilter(AddTime.waiting_for_time))
async def msg_add_time_value(message: Message, state: FSMContext):
    if not _owner_only(message.from_user.id):
        return

    text = message.text.strip()
    try:
        hour, minute = map(int, text.split(":"))
        assert 0 <= hour <= 23 and 0 <= minute <= 59
    except Exception:
        await message.answer("Noto'g'ri format. Iltimos HH:MM ko'rinishida yozing (masalan 09:15).")
        return

    data = await state.get_data()
    target = data["target"]

    now = now_tz()
    run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if run_time <= now:
        run_time += timedelta(days=1)

    schedule_one(target, run_time)
    await state.clear()
    await message.answer(
        f"✅ {target} uchun {run_time.strftime('%d.%m %H:%M')} vaqtga post qo'shildi.",
        reply_markup=_main_keyboard(),
    )


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


@router.message()
async def ignore_everything_else(message: Message):
    # Egasidan bo'lmagan yoki boshqa holatga tegishli bo'lmagan xabarlar e'tiborsiz qoldiriladi.
    return
