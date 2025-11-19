"""
User Service - бизнес-логика для работы с пользователями.

Соблюдает принципы SOLID:
- Single Responsibility: только логика пользователей
- Dependency Inversion: зависит от абстракций (AsyncSession)
- Open/Closed: легко расширяется новыми методами
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.models import User, UserType
from common.validators import TextValidator
from common.exceptions import UserNotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для управления пользователями"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией БД.

        Args:
            session: AsyncSession для работы с БД
        """
        self.session = session

    async def create_user(
        self,
        telegram_id: int,
        name: str,
        user_type: UserType,
        username: Optional[str] = None,
        primary_skill: Optional[str] = None,
        additional_skills: Optional[str] = None,
        idea_what: Optional[str] = None,
        idea_who: Optional[str] = None,
    ) -> User:
        """
        Создать нового пользователя с валидацией.

        Args:
            telegram_id: Telegram ID пользователя
            name: Имя пользователя
            user_type: Тип пользователя (TEAM/COFOUNDER/PARTICIPANT)
            username: Telegram username (опционально)
            primary_skill: Основной навык (опционально)
            additional_skills: Дополнительные навыки (опционально)
            idea_what: Описание идеи (опционально)
            idea_who: Целевая аудитория (опционально)

        Returns:
            User: созданный пользователь

        Raises:
            ValidationError: если данные не прошли валидацию
        """
        # Валидация имени
        validated_name = TextValidator.validate_name(name)

        # Валидация описаний (если есть)
        validated_idea_what = TextValidator.validate_description(idea_what)
        validated_idea_who = TextValidator.validate_description(idea_who)

        try:
            user = await crud.create_user(
                session=self.session,
                telegram_id=telegram_id,
                name=validated_name,
                user_type=user_type,
                username=username,
                primary_skill=primary_skill,
                additional_skills=additional_skills,
                idea_what=validated_idea_what,
                idea_who=validated_idea_who,
            )
            logger.info(f"User created: {user.id} ({user.name}, type={user_type.value})")
            return user

        except Exception as e:
            logger.error(f"Failed to create user: {e}", exc_info=True)
            raise

    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        """
        Получить пользователя по Telegram ID.

        Args:
            telegram_id: Telegram ID

        Returns:
            User: найденный пользователь

        Raises:
            UserNotFoundError: если пользователь не найден
        """
        user = await crud.get_user_by_telegram_id(self.session, telegram_id)
        if not user:
            raise UserNotFoundError(telegram_id=telegram_id)
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        """
        Получить пользователя по ID.

        Args:
            user_id: ID пользователя

        Returns:
            User: найденный пользователь

        Raises:
            UserNotFoundError: если пользователь не найден
        """
        user = await crud.get_user_by_id(self.session, user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user

    async def update_last_active(self, user_id: int) -> None:
        """
        Обновить время последней активности пользователя.

        Args:
            user_id: ID пользователя
        """
        await crud.update_user_last_active(self.session, user_id)
        logger.debug(f"Updated last_active for user {user_id}")

    async def get_user_stats(self, user_id: int) -> dict:
        """
        Получить статистику пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            dict: статистика пользователя

        Raises:
            UserNotFoundError: если пользователь не найден
        """
        stats = await crud.get_user_stats(self.session, user_id)
        if not stats:
            raise UserNotFoundError(user_id=user_id)
        return stats

    async def count_users(self) -> int:
        """
        Подсчитать общее количество пользователей.

        Returns:
            int: количество пользователей
        """
        return await crud.count_users(self.session)
