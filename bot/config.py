from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    Настройки приложения с валидацией через Pydantic.

    Переменные загружаются из:
    1. Переменных окружения
    2. .env файла
    3. Значений по умолчанию
    """

    # ===== Telegram Bot =====
    BOT_TOKEN: str = Field(
        ...,
        description="Telegram Bot Token от @BotFather",
        min_length=30
    )

    # ===== Database =====
    DB_HOST: str = Field(default="localhost", description="PostgreSQL хост")
    DB_PORT: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL порт")
    DB_NAME: str = Field(default="teammates_bot", min_length=1, description="Имя базы данных")
    DB_USER: str = Field(default="postgres", min_length=1, description="Пользователь БД")
    DB_PASSWORD: str = Field(..., min_length=1, description="Пароль БД")
    DATABASE_URL: Optional[str] = Field(default=None, description="Полный URL БД (опционально)")

    # ===== Application Settings =====
    DEBUG: bool = Field(default=False, description="Режим отладки")
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    LOG_TO_FILE: bool = Field(default=False, description="Писать логи в файл")
    LOG_FILE_PATH: str = Field(default="logs/bot.log", description="Путь к файлу логов")

    # ===== Rate Limiting =====
    RATE_LIMIT_DAILY_INVITATIONS: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Лимит приглашений в день"
    )
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Лимит запросов в минуту на пользователя"
    )

    # ===== Cleanup Settings =====
    CLEANUP_EXPIRED_INVITATIONS_HOURS: int = Field(
        default=72,
        ge=1,
        description="Время жизни приглашений (часы)"
    )
    CLEANUP_INACTIVE_USERS_DAYS: int = Field(
        default=30,
        ge=1,
        description="Время неактивности для архивации (дни)"
    )
    CLEANUP_INTERVAL_MINUTES: int = Field(
        default=60,
        ge=5,
        description="Интервал запуска фоновой очистки (минуты)"
    )

    # Конфигурация Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Игнорировать неизвестные переменные
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str], info) -> str:
        """Автоматически собрать DATABASE_URL если не указан"""
        if isinstance(v, str) and v:
            return v

        # Получаем значения из info.data (другие поля)
        data = info.data
        return (
            f"postgresql+asyncpg://{data.get('DB_USER')}:{data.get('DB_PASSWORD')}"
            f"@{data.get('DB_HOST')}:{data.get('DB_PORT')}/{data.get('DB_NAME')}"
        )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Проверить корректность уровня логирования"""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL должен быть одним из: {allowed}")
        return v.upper()


# Создаем глобальный экземпляр настроек
settings = Settings()
