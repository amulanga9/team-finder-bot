import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from database.db import create_tables
from handlers.start import router as start_router
from handlers.search import router as search_router
from handlers.invitations import router as invitations_router


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Создание таблиц в БД
    logger.info("Создание таблиц в базе данных...")
    try:
        await create_tables()
        logger.info("Таблицы успешно созданы")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        return

    # Регистрация роутеров (handlers)
    dp.include_router(start_router)
    dp.include_router(search_router)
    dp.include_router(invitations_router)
    # dp.include_router(profile_router)  # TODO

    logger.info("Бот успешно запущен")

    try:
        # Удаление вебхуков и запуск поллинга
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
