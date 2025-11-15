import asyncio
import logging
import signal
import sys
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from database.db import init_db, close_db, create_tables
from middlewares import ThrottlingMiddleware
from tasks import start_background_tasks, stop_background_tasks
from handlers.start import router as start_router
from handlers.search import router as search_router
from handlers.invitations import router as invitations_router
from handlers.profile import router as profile_router
from handlers.team import router as team_router
from handlers.commands import router as commands_router


# ===== Настройка логирования =====
def setup_logging():
    """Настройка логирования с поддержкой файлов"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Базовая конфигурация (консоль)
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Опционально: логирование в файл
    if settings.LOG_TO_FILE:
        log_file = Path(settings.LOG_FILE_PATH)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

        logger.info(f"Логирование в файл: {log_file}")


logger = logging.getLogger(__name__)


# ===== Graceful Shutdown =====
class BotApplication:
    """Класс для управления жизненным циклом бота"""

    def __init__(self):
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.background_task: asyncio.Task | None = None
        self.is_shutting_down = False

    async def startup(self):
        """Инициализация всех компонентов при старте"""
        logger.info("🚀 Запуск бота...")

        # 1. Инициализация базы данных
        logger.info("Подключение к базе данных...")
        await init_db()

        # 2. Создание таблиц (если их нет)
        logger.info("Проверка таблиц в базе данных...")
        try:
            await create_tables()
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")
            raise

        # 3. Инициализация бота и диспетчера
        self.bot = Bot(token=settings.BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())

        # 4. Регистрация middleware
        logger.info("Регистрация middleware...")
        self.dp.message.middleware(
            ThrottlingMiddleware(
                rate_limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                time_window=60
            )
        )

        # 5. Регистрация роутеров (handlers)
        logger.info("Регистрация обработчиков...")
        self.dp.include_router(commands_router)  # /help, /cancel первыми
        self.dp.include_router(start_router)
        self.dp.include_router(search_router)
        self.dp.include_router(invitations_router)
        self.dp.include_router(profile_router)
        self.dp.include_router(team_router)

        # 6. Запуск фоновых задач
        logger.info("Запуск фоновых задач очистки...")
        self.background_task = start_background_tasks()

        logger.info("✅ Бот успешно запущен и готов к работе")

    async def shutdown(self):
        """Graceful shutdown всех компонентов"""
        if self.is_shutting_down:
            return

        self.is_shutting_down = True
        logger.info("🛑 Получен сигнал остановки. Graceful shutdown...")

        # 1. Остановка фоновых задач
        if self.background_task:
            logger.info("Остановка фоновых задач...")
            await stop_background_tasks(self.background_task)

        # 2. Закрытие бота
        if self.bot:
            logger.info("Закрытие соединений бота...")
            await self.bot.session.close()

        # 3. Закрытие базы данных
        logger.info("Закрытие подключения к БД...")
        await close_db()

        logger.info("✅ Бот успешно остановлен")

    async def run(self):
        """Главный цикл работы бота"""
        try:
            await self.startup()

            # Удаление вебхуков и запуск поллинга
            await self.bot.delete_webhook(drop_pending_updates=True)
            await self.dp.start_polling(self.bot)

        except asyncio.CancelledError:
            logger.info("Получен сигнал отмены")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()


# ===== Signal Handlers =====
async def handle_signal(app: BotApplication, sig: signal.Signals):
    """Обработчик системных сигналов для graceful shutdown"""
    logger.info(f"Получен сигнал {sig.name}")
    await app.shutdown()


async def main():
    """Главная функция запуска бота"""
    setup_logging()

    app = BotApplication()

    # Настройка обработчиков сигналов для graceful shutdown
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(handle_signal(app, s))
        )

    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}", exc_info=True)
        sys.exit(1)
