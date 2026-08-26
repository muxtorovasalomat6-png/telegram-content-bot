import asyncio
import logging

from aiogram import Bot

from src import config
from src.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    config.validate_config()

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

    me = await bot.get_me()
    logger.info(f"Bot ishga tushdi: @{me.username}")

    # MUHIM: bu botda hech qanday xabar handler'i yo'q — u foydalanuvchi
    # yozgan xabarlarga umuman javob bermaydi. Faqat scheduler orqali,
    # o'zi belgilagan tasodifiy vaqtlarda kanal/guruhga post yuboradi.
    start_scheduler(bot)

    # Dastur doim ishlab tursin (scheduler background'da postlarni yuboraveradi)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
