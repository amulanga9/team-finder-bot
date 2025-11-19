"""
Search Service - алгоритмы поиска и совместимости.

Соблюдает принципы SOLID:
- Single Responsibility: только логика поиска
- Open/Closed: легко добавлять новые алгоритмы
"""
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.models import User, Team, UserType
from common.constants import (
    BASE_COMPATIBILITY_STARS,
    DIFFERENT_SKILLS_BONUS,
    SAME_IDEA_BONUS,
    MAX_COMPATIBILITY_STARS,
    IDEA_CATEGORIES,
)
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Сервис для поиска teammates и расчета совместимости"""

    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией БД.

        Args:
            session: AsyncSession для работы с БД
        """
        self.session = session

    async def find_users_by_skills(
        self, needed_skills: str, exclude_user_id: Optional[int] = None
    ) -> List[User]:
        """
        Найти пользователей по навыкам.

        Args:
            needed_skills: Строка с нужными навыками
            exclude_user_id: ID пользователя для исключения из поиска

        Returns:
            List[User]: список найденных пользователей
        """
        return await crud.find_users_by_skills(
            self.session, needed_skills, exclude_user_id
        )

    async def find_cofounders(self, user_id: int) -> List[Tuple[User, int]]:
        """
        Найти соло-основателей для коллаборации с расчетом совместимости.

        Args:
            user_id: ID текущего пользователя

        Returns:
            List[Tuple[User, int]]: список (пользователь, количество звезд)
        """
        cofounders_with_stars = await crud.find_cofounders(self.session, user_id)
        logger.info(f"Found {len(cofounders_with_stars)} cofounders for user {user_id}")
        return cofounders_with_stars

    async def find_teams_for_participant(self, participant_id: int) -> List[Team]:
        """
        Найти команды для соискателя.

        Args:
            participant_id: ID соискателя

        Returns:
            List[Team]: список подходящих команд
        """
        teams = await crud.find_teams_for_participant(self.session, participant_id)
        logger.info(f"Found {len(teams)} teams for participant {participant_id}")
        return teams

    def calculate_compatibility(self, user1: User, user2: User) -> int:
        """
        Рассчитать совместимость между двумя соло-основателями.

        Алгоритм:
        - Базовая совместимость: 2 звезды
        - Разные навыки (дополняют друг друга): +2 звезды
        - Похожие идеи (одна категория): +1 звезда
        - Максимум: 5 звезд

        Args:
            user1: Первый пользователь
            user2: Второй пользователь

        Returns:
            int: количество звезд (1-5)
        """
        stars = BASE_COMPATIBILITY_STARS

        # Проверяем навыки
        skill1 = (user1.primary_skill or "").strip().lower()
        skill2 = (user2.primary_skill or "").strip().lower()

        # Если навыки разные - это хорошо (дополняют друг друга)
        if skill1 and skill2 and skill1 != skill2:
            stars += DIFFERENT_SKILLS_BONUS

        # Проверяем похожесть идей
        if self._have_similar_ideas(user1, user2):
            stars += SAME_IDEA_BONUS

        # Ограничиваем максимумом
        stars = min(MAX_COMPATIBILITY_STARS, stars)

        return stars

    def _have_similar_ideas(self, user1: User, user2: User) -> bool:
        """
        Проверить, похожи ли идеи двух пользователей.

        Идеи считаются похожими, если они из одной категории
        (образование, финансы, здоровье и т.д.)

        Args:
            user1: Первый пользователь
            user2: Второй пользователь

        Returns:
            bool: True если идеи похожи
        """
        idea1_what = (user1.idea_what or "").lower()
        idea2_what = (user2.idea_what or "").lower()

        if not idea1_what or not idea2_what:
            return False

        # Определяем категорию первой идеи
        idea1_category = self._get_idea_category(idea1_what)
        idea2_category = self._get_idea_category(idea2_what)

        # Если обе идеи из одной категории - они похожи
        return (
            idea1_category is not None
            and idea2_category is not None
            and idea1_category == idea2_category
        )

    def _get_idea_category(self, idea_text: str) -> Optional[str]:
        """
        Определить категорию идеи по ключевым словам.

        Args:
            idea_text: Текст описания идеи

        Returns:
            Optional[str]: категория или None
        """
        idea_text = idea_text.lower()

        for category in IDEA_CATEGORIES:
            if category in idea_text:
                return category

        return None

    async def count_teams_need_skill(self, skill: str) -> int:
        """
        Подсчитать количество команд, которым нужен навык.

        Args:
            skill: Навык для поиска

        Returns:
            int: количество команд
        """
        return await crud.count_teams_need_skill(self.session, skill)
