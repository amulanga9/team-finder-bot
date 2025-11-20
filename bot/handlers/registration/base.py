"""
Базовая логика для всех типов регистрации.

Содержит общие функции, константы и утилиты.
Следует принципу DRY (Don't Repeat Yourself).
"""
import logging
import traceback
from typing import Optional
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.models import UserType
from database import crud

logger = logging.getLogger(__name__)

# Константы
COLD_START_THRESHOLD = 10


async def save_user_and_check_cold_start(
    telegram_id: int,
    name: str,
    user_type: UserType,
    username: Optional[str] = None,
    primary_skill: Optional[str] = None,
    additional_skills: Optional[str] = None,
    idea_what: Optional[str] = None,
    idea_who: Optional[str] = None,
) -> tuple[object, int, bool]:
    """
    Сохранить пользователя в БД и проверить холодный старт.

    Returns:
        tuple: (user, total_users, is_new_user)

    Raises:
        Exception: При ошибке сохранения в БД
    """
    user_type_name = user_type.value if hasattr(user_type, 'value') else str(user_type)
    logger.info(f"[{user_type_name.upper()}] Начало сохранения пользователя {telegram_id}")

    async with get_db() as session:
        # Проверяем, существует ли пользователь
        existing_user = await crud.get_user_by_telegram_id(session, telegram_id)
        is_new_user = existing_user is None

        if existing_user:
            # Обновляем существующего пользователя
            logger.info(f"[{user_type_name.upper()}] Пользователь уже существует, обновляем данные")
            user = await crud.update_user(
                session=session,
                telegram_id=telegram_id,
                username=username,
                name=name,
                user_type=user_type,
                primary_skill=primary_skill,
                additional_skills=additional_skills,
                idea_what=idea_what,
                idea_who=idea_who,
            )
            logger.info(f"[{user_type_name.upper()}] ✅ Профиль обновлен: {user.id} ({user.name})")
        else:
            # Создаем нового пользователя
            logger.info(f"[{user_type_name.upper()}] Создаем нового пользователя")
            user = await crud.create_user(
                session=session,
                telegram_id=telegram_id,
                username=username,
                name=name,
                user_type=user_type,
                primary_skill=primary_skill,
                additional_skills=additional_skills,
                idea_what=idea_what,
                idea_who=idea_who,
            )
            logger.info(f"[{user_type_name.upper()}] ✅ Пользователь создан: {user.id} ({user.name})")

        # Проверяем холодный старт
        total_users = await crud.count_users(session)
        logger.info(f"[{user_type_name.upper()}] Всего пользователей: {total_users}")

    return user, total_users, is_new_user


async def save_team_and_check_cold_start(
    telegram_id: int,
    username: Optional[str],
    full_name: str,
    team_name: str,
    idea_description: Optional[str],
    needed_skills: str,
) -> tuple[object, object, int]:
    """
    Сохранить команду и её лидера в БД.

    Returns:
        tuple: (user, team, total_users)

    Raises:
        Exception: При ошибке сохранения в БД
    """
    logger.info(f"[TEAM] Начало регистрации команды '{team_name}' от пользователя {telegram_id}")

    async with get_db() as session:
        # Проверяем, существует ли пользователь
        user = await crud.get_user_by_telegram_id(session, telegram_id)

        if not user:
            # Создаем нового пользователя-лидера команды
            user = await crud.create_user(
                session=session,
                telegram_id=telegram_id,
                username=username,
                name=full_name,
                user_type=UserType.TEAM
            )
            logger.info(f"[TEAM] ✅ Создан лидер команды: {user.id} ({user.name})")

        # Создаем команду
        team = await crud.create_team(
            session=session,
            team_name=team_name,
            leader_id=user.id,
            idea_description=idea_description,
            needed_skills=needed_skills
        )
        logger.info(f"[TEAM] ✅ Команда создана: {team.id} ({team.team_name})")

        # Проверяем холодный старт
        total_users = await crud.count_users(session)
        logger.info(f"[TEAM] Всего пользователей: {total_users}")

    return user, team, total_users


def log_registration_error(user_type: str, error: Exception) -> None:
    """
    Логировать ошибку регистрации с полным traceback.

    Args:
        user_type: Тип пользователя (TEAM, COFOUNDER, SEEKER)
        error: Исключение
    """
    logger.error(f"[{user_type.upper()}] ❌ Ошибка при сохранении: {error}")
    logger.error(f"[{user_type.upper()}] ❌ Полный traceback:\n{traceback.format_exc()}")


async def clear_state_safe(state: FSMContext) -> None:
    """
    Безопасно очистить FSM state с логированием.

    Args:
        state: FSM контекст
    """
    try:
        await state.clear()
        logger.debug("FSM state успешно очищен")
    except Exception as e:
        logger.warning(f"Не удалось очистить FSM state: {e}")
