"""
Middleware для rate limiting (защита от спама и DDoS).

Использует простой in-memory TTLCache для отслеживания запросов.
В production лучше использовать Redis.
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from cachetools import TTLCache
import time
import logging

logger = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов от пользователя.

    Защищает от:
    - Спама (слишком много сообщений)
    - Случайного flood (например, баг в клиенте)
    - DoS атак (хотя Telegram уже фильтрует большую часть)

    Лимиты настраиваются через config.py
    """

    def __init__(self, rate_limit: int = 20, time_window: int = 60):
        """
        Args:
            rate_limit: Максимум запросов в time_window (по умолчанию 20)
            time_window: Временное окно в секундах (по умолчанию 60)
        """
        super().__init__()
        self.rate_limit = rate_limit
        self.time_window = time_window

        # TTLCache автоматически удаляет старые записи
        # maxsize=10000 - храним информацию о 10000 пользователях
        self.cache: TTLCache = TTLCache(maxsize=10000, ttl=time_window)

        logger.info(
            f"Инициализирован ThrottlingMiddleware: "
            f"{rate_limit} запросов / {time_window} секунд"
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка каждого входящего сообщения.

        Логика:
        1. Получаем user_id
        2. Проверяем количество запросов за время time_window
        3. Если превышен лимит - игнорируем (или отправляем предупреждение)
        4. Если ОК - пропускаем дальше
        """

        # Проверяем только Message события (не CallbackQuery и т.д.)
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            # Нет user_id - пропускаем (странная ситуация)
            return await handler(event, data)

        # Проверяем текущее количество запросов
        current_count = self.cache.get(user_id, 0)

        if current_count >= self.rate_limit:
            # Превышен лимит!
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{current_count} requests in {self.time_window}s"
            )

            # Опционально: отправить предупреждение пользователю (первый раз)
            if current_count == self.rate_limit:
                try:
                    await event.answer(
                        "⚠️ Вы отправляете слишком много запросов. "
                        f"Пожалуйста, подождите {self.time_window} секунд."
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить предупреждение: {e}")

            # НЕ вызываем handler - блокируем запрос
            return

        # Обновляем счетчик запросов
        self.cache[user_id] = current_count + 1

        # Пропускаем запрос дальше
        return await handler(event, data)

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику использования (для мониторинга)"""
        return {
            "cached_users": len(self.cache),
            "rate_limit": self.rate_limit,
            "time_window": self.time_window,
            "cache_info": {
                "maxsize": self.cache.maxsize,
                "currsize": self.cache.currsize,
            }
        }
