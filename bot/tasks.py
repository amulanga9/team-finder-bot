"""
Фоновые задачи для автоматической очистки и обслуживания БД.

Задачи запускаются в отдельных asyncio task и выполняются периодически.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from database.models import Invitation, InvitationStatus, User
from config import settings

logger = logging.getLogger(__name__)


async def cleanup_expired_invitations() -> int:
    """
    Пометить истекшие приглашения как EXPIRED.

    Приглашения истекают через CLEANUP_EXPIRED_INVITATIONS_HOURS часов.

    Returns:
        Количество обработанных приглашений
    """
    try:
        async with get_db() as session:
            now = datetime.utcnow()

            # Находим приглашения со статусом PENDING и истекшим expires_at
            stmt = (
                update(Invitation)
                .where(
                    and_(
                        Invitation.status == InvitationStatus.PENDING,
                        Invitation.expires_at < now
                    )
                )
                .values(status=InvitationStatus.EXPIRED)
            )

            result = await session.execute(stmt)
            count = result.rowcount

            if count > 0:
                logger.info(f"Помечено {count} приглашений как истекшие")

            return count

    except Exception as e:
        logger.error(f"Ошибка при очистке истекших приглашений: {e}", exc_info=True)
        return 0


async def cleanup_inactive_users() -> int:
    """
    Пометить неактивных пользователей как "не ищет" (is_searching=False).

    Пользователи считаются неактивными, если last_active >
    CLEANUP_INACTIVE_USERS_DAYS дней назад.

    Returns:
        Количество обработанных пользователей
    """
    try:
        async with get_db() as session:
            threshold = datetime.utcnow() - timedelta(
                days=settings.CLEANUP_INACTIVE_USERS_DAYS
            )

            # Находим активных пользователей с устаревшим last_active
            stmt = (
                update(User)
                .where(
                    and_(
                        User.is_searching == True,
                        User.last_active < threshold,
                        User.deleted_at.is_(None)
                    )
                )
                .values(is_searching=False)
            )

            result = await session.execute(stmt)
            count = result.rowcount

            if count > 0:
                logger.info(
                    f"Помечено {count} неактивных пользователей "
                    f"(последняя активность > {settings.CLEANUP_INACTIVE_USERS_DAYS} дней)"
                )

            return count

    except Exception as e:
        logger.error(f"Ошибка при очистке неактивных пользователей: {e}", exc_info=True)
        return 0


async def cleanup_task_runner():
    """
    Главная функция для запуска фоновых задач очистки.

    Запускается в отдельном asyncio.Task при старте бота.
    Выполняется каждые CLEANUP_INTERVAL_MINUTES минут.
    """
    interval = settings.CLEANUP_INTERVAL_MINUTES * 60  # Минуты -> секунды

    logger.info(
        f"Запущена фоновая задача очистки БД. "
        f"Интервал: {settings.CLEANUP_INTERVAL_MINUTES} минут"
    )

    while True:
        try:
            logger.info("Запуск фоновой очистки БД...")

            # Запускаем обе задачи параллельно
            expired_count, inactive_count = await asyncio.gather(
                cleanup_expired_invitations(),
                cleanup_inactive_users(),
                return_exceptions=False
            )

            logger.info(
                f"Фоновая очистка завершена: "
                f"{expired_count} истекших приглашений, "
                f"{inactive_count} неактивных пользователей"
            )

        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче очистки: {e}", exc_info=True)

        # Ждем до следующего запуска
        await asyncio.sleep(interval)


def start_background_tasks() -> asyncio.Task:
    """
    Запустить все фоновые задачи.

    Вызывается при старте бота в main.py.

    Returns:
        asyncio.Task для отслеживания и graceful shutdown
    """
    task = asyncio.create_task(cleanup_task_runner())
    logger.info("Фоновые задачи запущены")
    return task


async def stop_background_tasks(task: asyncio.Task):
    """
    Остановить фоновые задачи (graceful shutdown).

    Args:
        task: Task, возвращенный start_background_tasks()
    """
    logger.info("Остановка фоновых задач...")
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        logger.info("Фоновые задачи остановлены")
