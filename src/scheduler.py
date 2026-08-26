import random
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import BufferedInputFile

from src import config, state
from src.content_generator import generate_post, FALLBACK_TOPICS
from src.channel_analyzer import analyze_topics

logger = logging.getLogger(__name__)

# Har bir kanalning joriy mavzusi shu yerda keshlanadi (kunlik yangilanadi)
_topic_cache: dict[str, str] = {}


def _resolve_topic(channel: config.ChannelConfig) -> str:
    if not channel.auto_topic:
        return channel.fixed_topic or random.choice(FALLBACK_TOPICS)

    cached = _topic_cache.get(channel.target)
    if cached:
        return cached

    source = channel.analyze_source or channel.target
    topic = analyze_topics(source)
    _topic_cache[channel.target] = topic
    return topic


def _refresh_topic(channel: config.ChannelConfig):
    """Kanal mavzusini majburan qayta tahlil qiladi (kuniga bir marta chaqiriladi)."""
    if not channel.auto_topic:
        return
    source = channel.analyze_source or channel.target
    _topic_cache[channel.target] = analyze_topics(source)


async def send_post(bot: Bot, channel: config.ChannelConfig):
    """Bitta post yaratib, shu kanalga yuboradi (agar bot to'xtatilmagan bo'lsa)."""
    if not state.is_running():
        logger.info(f"[{channel.target}] Bot to'xtatilgan, post o'tkazib yuborildi.")
        return
    try:
        topic = _resolve_topic(channel)
        caption, image_bytes = generate_post(topic)

        if image_bytes:
            photo = BufferedInputFile(image_bytes, filename="post.png")
            await bot.send_photo(chat_id=channel.target, photo=photo, caption=caption)
        else:
            await bot.send_message(chat_id=channel.target, text=caption)

        logger.info(f"[{channel.target}] Post muvaffaqiyatli yuborildi.")
    except Exception:
        logger.exception(f"[{channel.target}] Post yuborishda xatolik yuz berdi")


def _random_times_for_today(now: datetime) -> list[datetime]:
    count = random.randint(config.MIN_POSTS_PER_DAY, config.MAX_POSTS_PER_DAY)

    day_start = now.replace(hour=config.ACTIVE_HOUR_START, minute=0, second=0, microsecond=0)
    day_end = now.replace(hour=config.ACTIVE_HOUR_END, minute=0, second=0, microsecond=0)

    window_start = max(now, day_start)
    if window_start >= day_end:
        return []

    total_seconds = int((day_end - window_start).total_seconds())
    offsets = sorted(random.sample(range(total_seconds), min(count, total_seconds)))
    return [window_start + timedelta(seconds=offset) for offset in offsets]


def _schedule_channel_day(scheduler: AsyncIOScheduler, bot: Bot, channel: config.ChannelConfig, now: datetime):
    _refresh_topic(channel)

    times = _random_times_for_today(now)
    for t in times:
        scheduler.add_job(send_post, "date", run_date=t, args=[bot, channel])

    logger.info(
        f"[{channel.target}] Bugun uchun {len(times)} ta post rejalashtirildi: "
        f"{[t.strftime('%H:%M') for t in times]}"
    )


def _schedule_next_day(scheduler: AsyncIOScheduler, bot: Bot):
    tomorrow_start = (datetime.now() + timedelta(days=1)).replace(
        hour=0, minute=1, second=0, microsecond=0
    )

    async def plan_tomorrow():
        for channel in config.CHANNELS:
            _schedule_channel_day(scheduler, bot, channel, datetime.now())
        _schedule_next_day(scheduler, bot)

    scheduler.add_job(plan_tomorrow, "date", run_date=tomorrow_start)


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    now = datetime.now()

    for channel in config.CHANNELS:
        _schedule_channel_day(scheduler, bot, channel, now)

    _schedule_next_day(scheduler, bot)
    scheduler.start()
    return scheduler
