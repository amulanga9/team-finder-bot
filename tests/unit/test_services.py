"""
Unit tests для services.

Тестируем бизнес-логику сервисов.
"""
import pytest
from bot.services import UserService, TeamService, InvitationService, SearchService
from bot.database.models import UserType, User
from bot.common.exceptions import UserNotFoundError, ValidationError


@pytest.mark.unit
class TestUserService:
    """Тесты для UserService"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_session):
        """Создание пользователя с валидными данными"""
        service = UserService(test_session)

        user = await service.create_user(
            telegram_id=123456,
            name="John Doe",
            user_type=UserType.PARTICIPANT,
            username="johndoe",
        )

        assert user.id is not None
        assert user.telegram_id == 123456
        assert user.name == "John Doe"
        assert user.user_type == UserType.PARTICIPANT

    @pytest.mark.asyncio
    async def test_create_user_validates_name(self, test_session):
        """Создание пользователя с невалидным именем вызывает ошибку"""
        service = UserService(test_session)

        with pytest.raises(ValidationError):
            await service.create_user(
                telegram_id=123456,
                name="A",  # Слишком короткое
                user_type=UserType.PARTICIPANT,
            )

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_success(self, test_session):
        """Получение существующего пользователя"""
        service = UserService(test_session)

        # Создаем пользователя
        created_user = await service.create_user(
            telegram_id=123456,
            name="John Doe",
            user_type=UserType.PARTICIPANT,
        )

        # Получаем его
        found_user = await service.get_user_by_telegram_id(123456)

        assert found_user.id == created_user.id
        assert found_user.telegram_id == 123456

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_not_found(self, test_session):
        """Получение несуществующего пользователя вызывает ошибку"""
        service = UserService(test_session)

        with pytest.raises(UserNotFoundError):
            await service.get_user_by_telegram_id(999999)

    @pytest.mark.asyncio
    async def test_count_users(self, test_session):
        """Подсчет количества пользователей"""
        service = UserService(test_session)

        # Создаем несколько пользователей
        await service.create_user(123456, "User 1", UserType.PARTICIPANT)
        await service.create_user(123457, "User 2", UserType.COFOUNDER)
        await service.create_user(123458, "User 3", UserType.TEAM)

        count = await service.count_users()
        assert count == 3


@pytest.mark.unit
class TestSearchService:
    """Тесты для SearchService"""

    @pytest.mark.asyncio
    async def test_calculate_compatibility_different_skills(self, test_session):
        """Совместимость с разными навыками"""
        service = SearchService(test_session)

        user1 = User(
            telegram_id=1,
            name="User 1",
            user_type=UserType.COFOUNDER,
            primary_skill="Backend (Python/Go)",
        )
        user2 = User(
            telegram_id=2,
            name="User 2",
            user_type=UserType.COFOUNDER,
            primary_skill="Frontend (React)",
        )

        stars = service.calculate_compatibility(user1, user2)

        # Разные навыки = 4 звезды (базовые 2 + бонус 2)
        assert stars == 4

    @pytest.mark.asyncio
    async def test_calculate_compatibility_same_skills(self, test_session):
        """Совместимость с одинаковыми навыками"""
        service = SearchService(test_session)

        user1 = User(
            telegram_id=1,
            name="User 1",
            user_type=UserType.COFOUNDER,
            primary_skill="Backend (Python/Go)",
        )
        user2 = User(
            telegram_id=2,
            name="User 2",
            user_type=UserType.COFOUNDER,
            primary_skill="Backend (Python/Go)",
        )

        stars = service.calculate_compatibility(user1, user2)

        # Одинаковые навыки = 2 звезды (только базовые)
        assert stars == 2

    @pytest.mark.asyncio
    async def test_calculate_compatibility_similar_ideas(self, test_session):
        """Совместимость с похожими идеями"""
        service = SearchService(test_session)

        user1 = User(
            telegram_id=1,
            name="User 1",
            user_type=UserType.COFOUNDER,
            primary_skill="Backend (Python/Go)",
            idea_what="Платформа для образования студентов",
        )
        user2 = User(
            telegram_id=2,
            name="User 2",
            user_type=UserType.COFOUNDER,
            primary_skill="Frontend (React)",
            idea_what="Приложение для образования школьников",
        )

        stars = service.calculate_compatibility(user1, user2)

        # Разные навыки (4) + похожие идеи (1) = 5 звезд
        assert stars == 5
