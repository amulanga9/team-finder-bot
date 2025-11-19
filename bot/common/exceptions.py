"""
Custom исключения для приложения.

Использование custom исключений позволяет:
1. Четко различать типы ошибок
2. Обрабатывать их специфическим образом
3. Упростить отладку и мониторинг
4. Соблюдать принцип Open/Closed (SOLID)
"""
from typing import Optional


class TeamFinderException(Exception):
    """Базовое исключение для всех ошибок приложения"""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(TeamFinderException):
    """Ошибка валидации входных данных"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR")


class UserNotFoundError(TeamFinderException):
    """Пользователь не найден"""

    def __init__(self, user_id: Optional[int] = None, telegram_id: Optional[int] = None):
        self.user_id = user_id
        self.telegram_id = telegram_id
        message = f"User not found: id={user_id}, telegram_id={telegram_id}"
        super().__init__(message, code="USER_NOT_FOUND")


class TeamNotFoundError(TeamFinderException):
    """Команда не найдена"""

    def __init__(self, team_id: int):
        self.team_id = team_id
        message = f"Team not found: id={team_id}"
        super().__init__(message, code="TEAM_NOT_FOUND")


class InvitationNotFoundError(TeamFinderException):
    """Приглашение не найдено"""

    def __init__(self, invitation_id: int):
        self.invitation_id = invitation_id
        message = f"Invitation not found: id={invitation_id}"
        super().__init__(message, code="INVITATION_NOT_FOUND")


class InvitationLimitExceededError(TeamFinderException):
    """Превышен лимит приглашений"""

    def __init__(self, current_count: int, max_count: int):
        self.current_count = current_count
        self.max_count = max_count
        message = f"Invitation limit exceeded: {current_count}/{max_count}"
        super().__init__(message, code="INVITATION_LIMIT_EXCEEDED")


class RateLimitExceededError(TeamFinderException):
    """Превышен лимит запросов (rate limiting)"""

    def __init__(self, user_id: int, requests_count: int):
        self.user_id = user_id
        self.requests_count = requests_count
        message = f"Rate limit exceeded for user {user_id}: {requests_count} requests"
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")


class DatabaseError(TeamFinderException):
    """Ошибка при работе с БД"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(message, code="DATABASE_ERROR")


class InvalidStateError(TeamFinderException):
    """Некорректное состояние FSM или данных"""

    def __init__(self, message: str, current_state: Optional[str] = None):
        self.current_state = current_state
        super().__init__(message, code="INVALID_STATE")
