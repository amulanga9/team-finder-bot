"""Base handler utilities"""
import logging
from functools import wraps
from typing import Callable

from aiogram.types import Message, CallbackQuery
from bot.utils.i18n import get_text
from bot.database.models import Language


logger = logging.getLogger(__name__)


def handle_errors(handler: Callable):
    """
    Decorator to handle errors in handlers

    Usage:
        @handle_errors
        async def my_handler(message: Message):
            ...
    """

    @wraps(handler)
    async def wrapper(*args, **kwargs):
        try:
            return await handler(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {handler.__name__}: {e}",
                exc_info=True,
                extra={"handler": handler.__name__},
            )

            # Get message object
            message_obj = None
            for arg in args:
                if isinstance(arg, (Message, CallbackQuery)):
                    message_obj = (
                        arg if isinstance(arg, Message) else arg.message
                    )
                    break

            if message_obj:
                error_text = get_text("error_try_again", Language.RU)
                if isinstance(args[0], CallbackQuery):
                    await args[0].answer(error_text, show_alert=True)
                else:
                    await message_obj.answer(error_text)

    return wrapper


async def safe_answer(
    message: Message, text: str, show_alert: bool = False, **kwargs
) -> None:
    """
    Safely send message with error handling

    Args:
        message: Message or CallbackQuery
        text: Text to send
        show_alert: Show as alert (for callbacks)
        **kwargs: Additional arguments for answer()
    """
    try:
        await message.answer(text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")


async def safe_edit(message: Message, text: str, **kwargs) -> None:
    """Safely edit message with error handling"""
    try:
        await message.edit_text(text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
