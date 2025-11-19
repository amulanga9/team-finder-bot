"""
Invitation Service - бизнес-логика для работы с приглашениями.

Соблюдает принципы SOLID и DRY.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.models import Invitation, InvitationStatus, User
from common.validators import InvitationValidator
from common.exceptions import (
    InvitationNotFoundError,
    InvitationLimitExceededError,
    ValidationError,
)
from common.constants import MAX_INVITATIONS_PER_DAY
from config import settings
import logging

logger = logging.getLogger(__name__)


class InvitationService:
    """Сервис для управления приглашениями"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией БД.

        Args:
            session: AsyncSession для работы с БД
        """
        self.session = session

    async def create_invitation(
        self,
        from_user_id: int,
        to_user_id: int,
        from_team_id: Optional[int] = None,
        message: Optional[str] = None,
    ) -> Invitation:
        """
        Создать приглашение с валидацией и проверкой лимитов.

        Args:
            from_user_id: ID отправителя
            to_user_id: ID получателя
            from_team_id: ID команды (опционально)
            message: Сообщение (опционально)

        Returns:
            Invitation: созданное приглашение

        Raises:
            ValidationError: если валидация не прошла
            InvitationLimitExceededError: если превышен лимит
        """
        # Валидация: нельзя приглашать самого себя
        InvitationValidator.validate_self_invitation(from_user_id, to_user_id)

        # Проверка лимита приглашений
        await self._check_invitation_limit(from_user_id)

        try:
            # Устанавливаем срок истечения (72 часа по умолчанию)
            expires_at = datetime.utcnow() + timedelta(
                hours=settings.CLEANUP_EXPIRED_INVITATIONS_HOURS
            )

            invitation = await crud.create_invitation(
                session=self.session,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                from_team_id=from_team_id,
                message=message,
            )

            # Обновляем expires_at (crud не поддерживает этот параметр пока)
            invitation.expires_at = expires_at
            await self.session.commit()
            await self.session.refresh(invitation)

            logger.info(
                f"Invitation created: {invitation.id} "
                f"(from={from_user_id} to={to_user_id})"
            )
            return invitation

        except Exception as e:
            logger.error(f"Failed to create invitation: {e}", exc_info=True)
            raise

    async def _check_invitation_limit(self, from_user_id: int) -> None:
        """
        Проверить лимит приглашений для пользователя.

        Args:
            from_user_id: ID пользователя

        Raises:
            InvitationLimitExceededError: если лимит превышен
        """
        count = await crud.count_invitations_today(self.session, from_user_id)
        max_count = settings.RATE_LIMIT_DAILY_INVITATIONS

        if not await crud.check_invitation_limit(self.session, from_user_id, max_count):
            raise InvitationLimitExceededError(count, max_count)

    async def get_invitation_by_id(self, invitation_id: int) -> Invitation:
        """
        Получить приглашение по ID.

        Args:
            invitation_id: ID приглашения

        Returns:
            Invitation: найденное приглашение

        Raises:
            InvitationNotFoundError: если приглашение не найдено
        """
        invitation = await crud.get_invitation_by_id(self.session, invitation_id)
        if not invitation:
            raise InvitationNotFoundError(invitation_id=invitation_id)
        return invitation

    async def get_received_invitations(
        self, user_id: int, status: Optional[InvitationStatus] = None
    ) -> List[Invitation]:
        """
        Получить полученные приглашения пользователя.

        Args:
            user_id: ID пользователя
            status: Статус приглашения (опционально)

        Returns:
            List[Invitation]: список приглашений
        """
        return await crud.get_received_invitations(self.session, user_id, status)

    async def get_sent_invitations(
        self, user_id: int, status: Optional[InvitationStatus] = None
    ) -> List[Invitation]:
        """
        Получить отправленные приглашения пользователя.

        Args:
            user_id: ID пользователя
            status: Статус приглашения (опционально)

        Returns:
            List[Invitation]: список приглашений
        """
        return await crud.get_sent_invitations(self.session, user_id, status)

    async def accept_invitation(self, invitation_id: int) -> Invitation:
        """
        Принять приглашение.

        Args:
            invitation_id: ID приглашения

        Returns:
            Invitation: обновленное приглашение

        Raises:
            InvitationNotFoundError: если приглашение не найдено
        """
        # Проверяем существование
        invitation = await self.get_invitation_by_id(invitation_id)

        # Обновляем статус
        await crud.update_invitation_status(
            self.session, invitation_id, InvitationStatus.ACCEPTED
        )

        logger.info(f"Invitation {invitation_id} accepted")

        # Возвращаем обновленное приглашение
        return await self.get_invitation_by_id(invitation_id)

    async def reject_invitation(self, invitation_id: int) -> Invitation:
        """
        Отклонить приглашение.

        Args:
            invitation_id: ID приглашения

        Returns:
            Invitation: обновленное приглашение

        Raises:
            InvitationNotFoundError: если приглашение не найдено
        """
        # Проверяем существование
        invitation = await self.get_invitation_by_id(invitation_id)

        # Обновляем статус
        await crud.update_invitation_status(
            self.session, invitation_id, InvitationStatus.REJECTED
        )

        logger.info(f"Invitation {invitation_id} rejected")

        # Возвращаем обновленное приглашение
        return await self.get_invitation_by_id(invitation_id)

    async def mark_as_viewed(self, invitation_id: int) -> None:
        """
        Отметить приглашение как просмотренное.

        Args:
            invitation_id: ID приглашения

        Raises:
            InvitationNotFoundError: если приглашение не найдено
        """
        # Проверяем существование
        await self.get_invitation_by_id(invitation_id)

        await crud.mark_invitation_viewed(self.session, invitation_id)
        logger.debug(f"Invitation {invitation_id} marked as viewed")

    async def count_invitations_today(self, from_user_id: int) -> int:
        """
        Подсчитать количество приглашений отправленных сегодня.

        Args:
            from_user_id: ID отправителя

        Returns:
            int: количество приглашений
        """
        return await crud.count_invitations_today(self.session, from_user_id)
