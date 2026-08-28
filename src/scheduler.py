import random
import logging
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import BufferedInputFile

from src import config, state
from src.content_generator import generate_post, generate_poll, FALLBACK_TOPICS
from src.channel_analyzer import analyze_topics

logger = logging.getLogger(__name__)

TZ = ZoneInfo("Asia/Tashkent")


def now_tz() -> datetime:
    return datetime.now(TZ)

# Har bir kanalning joriy mavzusi shu yerda keshlanadi (kunlik yangilanadi)
_topic_cache: dict[str, str] = {}

# Bugungi rejalashtirilgan postlar: {job_id: {"target": str, "time": datetime}}
_today_jobs: dict[str, dict] = {}

_scheduler_ref: AsyncIOScheduler | None = None
_bot_ref: Bot | None = None

# Har 4-postdan biri (taxminan) so'rovnoma bo'ladi
POLL_CHANCE = 0.25


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
    if not channel.auto_topic:
        return
    source = channel.analyze_source or channel.target
    _topic_cache[channel.target] = analyze_topics(source)


async def send_post(bot: Bot, target: str, job_id: str | None = None):
    """Bitta post (yoki so'rovnoma) yaratib, shu kanalga yuboradi."""
    if job_id:
        _today_jobs.pop(job_id, None)

    if not state.is_running():
        logger.info(f"[{target}] Bot to'xtatilgan, post o'tkazib yuborildi.")
        return

    channel = next((c for c in state.get_channels() if c.target == target), None)
    if channel is None:
        logger.info(f"[{target}] Kanal ro'yxatdan o'chirilgan, post yuborilmadi.")
        return

    try:
        topic = _resolve_topic(channel)

        if random.random() < POLL_CHANCE:
            poll = generate_poll(topic)
            if poll:
                await bot.send_poll(
                    chat_id=channel.target,
                    question=poll["question"],
                    options=poll["options"],
                    is_anonymous=True,
                )
                logger.info(f"[{channel.target}] So'rovnoma muvaffaqiyatli yuborildi.")
                return

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


def schedule_one(target: str, run_time: datetime) -> str:
    """Bitta kanal uchun berilgan vaqtga post rejalashtiradi. Job ID qaytaradi."""
    job_id = str(uuid.uuid4())
    _scheduler_ref.add_job(
        send_post, "date", run_date=run_time, args=[_bot_ref, target, job_id], id=job_id
    )
    _today_jobs[job_id] = {"target": target, "time": run_time}
    return job_id


def cancel_job(job_id: str):
    try:
        _scheduler_ref.remove_job(job_id)
    except Exception:
        pass
    _today_jobs.pop(job_id, None)


def cancel_all_for_channel(target: str):
    for job_id, info in list(_today_jobs.items()):
        if info["target"] == target:
            cancel_job(job_id)


def get_today_schedule() -> dict[str, list[tuple[str, datetime]]]:
    """{target: [(job_id, time), ...]} ko'rinishida, vaqt bo'yicha saralangan."""
    result: dict[str, list[tuple[str, datetime]]] = {}
    for job_id, info in sorted(_today_jobs.items(), key=lambda kv: kv[1]["time"]):
        result.setdefault(info["target"], []).append((job_id, info["time"]))
    return result


def _schedule_channel_day(channel: config.ChannelConfig, now: datetime):
    _refresh_topic(channel)
    times = _random_times_for_today(now)
    for t in times:
        schedule_one(channel.target, t)
    logger.info(
        f"[{channel.target}] Bugun uchun {len(times)} ta post rejalashtirildi: "
        f"{[t.strftime('%H:%M') for t in times]}"
    )


def _schedule_next_day():
    tomorrow_start = (now_tz() + timedelta(days=1)).replace(
        hour=0, minute=1, second=0, microsecond=0
    )

    async def plan_tomorrow():
        for channel in state.get_channels():
            _schedule_channel_day(channel, now_tz())
        _schedule_next_day()

    _scheduler_ref.add_job(plan_tomorrow, "date", run_date=tomorrow_start)


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    global _scheduler_ref, _bot_ref
    _scheduler_ref = AsyncIOScheduler()
    _bot_ref = bot
    now = now_tz()

    for channel in state.get_channels():
        _schedule_channel_day(channel, now)

    _schedule_next_day()
    _scheduler_ref.start()
    return _scheduler_ref
