import random
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import BufferedInputFile

from src import config
from src.content_generator import generate_post

logger = logging.getLogger(__name__)


async def send_post(bot: Bot):
    """Bitta post yaratib, maqsadli kanal/guruhga yuboradi."""
    try:
        caption, image_bytes = generate_post()

        if image_bytes:
            photo = BufferedInputFile(image_bytes, filename="post.png")
            await bot.send_photo(
                chat_id=config.TARGET_CHAT_ID,
                photo=photo,
                caption=caption,
            )
        else:
            # Rasm generatsiya qilinmasa ham, matn postini yuboramiz
            await bot.send_message(chat_id=config.TARGET_CHAT_ID, text=caption)

        logger.info("Post muvaffaqiyatli yuborildi.")
    except Exception:
        logger.exception("Post yuborishda xatolik yuz berdi")


def _random_times_for_today(now: datetime) -> list[datetime]:
    """Bugungi qolgan vaqt ichida tasodifiy post vaqtlarini hisoblaydi."""
    count = random.randint(config.MIN_POSTS_PER_DAY, config.MAX_POSTS_PER_DAY)

    day_start = now.replace(
        hour=config.ACTIVE_HOUR_START, minute=0, second=0, microsecond=0
    )
    day_end = now.replace(
        hour=config.ACTIVE_HOUR_END, minute=0, second=0, microsecond=0
    )

    window_start = max(now, day_start)
    if window_start >= day_end:
        return []

    total_seconds = int((day_end - window_start).total_seconds())
    offsets = sorted(random.sample(range(total_seconds), min(count, total_seconds)))
    return [window_start + timedelta(seconds=offset) for offset in offsets]


def _schedule_day(scheduler: AsyncIOScheduler, bot: Bot, now: datetime):
    times = _random_times_for_today(now)
    for t in times:
        scheduler.add_job(send_post, "date", run_date=t, args=[bot])
    logger.info(f"Bugun uchun {len(times)} ta post rejalashtirildi: {[t.strftime('%H:%M') for t in times]}")


def _schedule_next_day(scheduler: AsyncIOScheduler, bot: Bot):
    """Har kuni yarim tunda ertangi kun uchun postlarni qayta rejalashtiradi."""
    tomorrow_start = (datetime.now() + timedelta(days=1)).replace(
        hour=0, minute=1, second=0, microsecond=0
    )

    async def plan_tomorrow():
        _schedule_day(scheduler, bot, datetime.now())
        _schedule_next_day(scheduler, bot)

    scheduler.add_job(plan_tomorrow, "date", run_date=tomorrow_start)


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    now = datetime.now()
    _schedule_day(scheduler, bot, now)
    _schedule_next_day(scheduler, bot)
    scheduler.start()
    return scheduler
