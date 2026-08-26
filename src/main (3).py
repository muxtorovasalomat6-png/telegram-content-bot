import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src import config
from src.scheduler import start_scheduler
from src.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    config.validate_config()

    bot = Bot(
        token=config.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    me = await bot.get_me()
    logger.info(f"Bot ishga tushdi: @{me.username}")

    # Postlarni fon rejimida yuboruvchi scheduler
    start_scheduler(bot)

    # Faqat bot egasi bilan /start orqali muloqot qilish uchun polling.
    # Boshqa foydalanuvchilarning xabarlariga handlers.py ichida javob berilmaydi.
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
