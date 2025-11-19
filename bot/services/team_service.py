"""
Team Service - бизнес-логика для работы с командами.

Соблюдает принципы SOLID:
- Single Responsibility: только логика команд
- Dependency Inversion: зависит от абстракций
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.models import Team, TeamStatus
from common.validators import TextValidator, SkillsValidator
from common.exceptions import TeamNotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class TeamService:
    """Сервис для управления командами"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией БД.

        Args:
            session: AsyncSession для работы с БД
        """
        self.session = session

    async def create_team(
        self,
        team_name: str,
        leader_id: int,
        idea_description: Optional[str] = None,
        needed_skills: Optional[str] = None,
    ) -> Team:
        """
        Создать новую команду с валидацией.

        Args:
            team_name: Название команды
            leader_id: ID лидера команды
            idea_description: Описание идеи (опционально)
            needed_skills: Нужные навыки (опционально)

        Returns:
            Team: созданная команда

        Raises:
            ValidationError: если данные не прошли валидацию
        """
        # Валидация названия
        validated_name = TextValidator.validate_team_name(team_name)

        # Валидация описания
        validated_description = TextValidator.validate_description(idea_description)

        try:
            team = await crud.create_team(
                session=self.session,
                team_name=validated_name,
                leader_id=leader_id,
                idea_description=validated_description,
                needed_skills=needed_skills,
            )
            logger.info(f"Team created: {team.id} ({team.team_name})")
            return team

        except Exception as e:
            logger.error(f"Failed to create team: {e}", exc_info=True)
            raise

    async def get_team_by_id(self, team_id: int) -> Team:
        """
        Получить команду по ID.

        Args:
            team_id: ID команды

        Returns:
            Team: найденная команда

        Raises:
            TeamNotFoundError: если команда не найдена
        """
        team = await crud.get_team_by_id(self.session, team_id)
        if not team:
            raise TeamNotFoundError(team_id=team_id)
        return team

    async def get_teams_by_leader(self, leader_id: int) -> List[Team]:
        """
        Получить все команды пользователя.

        Args:
            leader_id: ID лидера

        Returns:
            List[Team]: список команд
        """
        return await crud.get_teams_by_leader(self.session, leader_id)

    async def update_team_status(self, team_id: int, status: TeamStatus) -> None:
        """
        Обновить статус команды.

        Args:
            team_id: ID команды
            status: Новый статус

        Raises:
            TeamNotFoundError: если команда не найдена
        """
        # Проверяем существование команды
        await self.get_team_by_id(team_id)

        await crud.update_team_status(self.session, team_id, status)
        logger.info(f"Team {team_id} status updated to {status.value}")

    async def get_team_stats(self, team_id: int) -> dict:
        """
        Получить статистику команды.

        Args:
            team_id: ID команды

        Returns:
            dict: статистика команды

        Raises:
            TeamNotFoundError: если команда не найдена
        """
        stats = await crud.get_team_stats(self.session, team_id)
        if not stats:
            raise TeamNotFoundError(team_id=team_id)
        return stats
