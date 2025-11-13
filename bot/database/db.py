from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from database.models import Base
from config import settings
import logging

logger = logging.getLogger(__name__)

# Глобальные переменные для движка и фабрики сессий
engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    Инициализация подключения к БД.
    ОБЯЗАТЕЛЬНО вызвать при старте приложения!
    """
    global engine, AsyncSessionLocal

    logger.info("Инициализация подключения к базе данных...")

    # Создаем асинхронный движок с пулом соединений
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=10,  # Количество постоянных соединений
        max_overflow=20,  # Дополнительные соединения при пиковой нагрузке
        pool_pre_ping=True,  # Проверка соединения перед использованием
        pool_recycle=3600,  # Пересоздание соединений каждый час
    )

    # Создаем фабрику сессий
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    logger.info("Подключение к базе данных успешно инициализировано")


async def close_db() -> None:
    """
    Закрытие подключения к БД.
    ОБЯЗАТЕЛЬНО вызвать при остановке приложения!
    """
    global engine

    if engine is None:
        return

    logger.info("Закрытие подключения к базе данных...")
    await engine.dispose()
    logger.info("Подключение к базе данных закрыто")


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД с АВТОМАТИЧЕСКИМ cleanup.

    Использование:
        async with get_db() as session:
            user = await session.get(User, user_id)
            # session автоматически закроется после выхода из блока

    Фичи:
    - Автоматический commit при успехе
    - Автоматический rollback при ошибке
    - ОБЯЗАТЕЛЬНОЕ закрытие сессии в finally (предотвращает memory leak!)
    """
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Database not initialized! Call init_db() first in main.py startup"
        )

    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка в транзакции БД: {e}", exc_info=True)
        raise
    finally:
        await session.close()


async def create_tables() -> None:
    """Создать все таблицы в БД"""
    if engine is None:
        raise RuntimeError("Database not initialized! Call init_db() first")

    logger.info("Создание таблиц в базе данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы успешно созданы")


async def drop_tables() -> None:
    """Удалить все таблицы из БД (для разработки)"""
    if engine is None:
        raise RuntimeError("Database not initialized! Call init_db() first")

    logger.warning("ВНИМАНИЕ: Удаление всех таблиц из БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Таблицы удалены")
