"""
Обработчик команды /start и финальные действия.

Простой, чистый код - только старт бота.
Вся логика регистраций вынесена в handlers/registration/.
"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.texts import START_MESSAGE
from keyboards.inline import get_user_type_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    logger.info(f"[START] Пользователь {message.from_user.id} запустил бота")
    await message.answer(
        START_MESSAGE,
        reply_markup=get_user_type_keyboard()
    )


# ===== ФИНАЛЬНЫЕ ДЕЙСТВИЯ =====

@router.callback_query(F.data == "search_now")
async def search_now(callback: CallbackQuery):
    """Начать поиск teammates"""
    await callback.answer("Функция поиска будет добавлена позже", show_alert=True)
    logger.info(f"[START] Пользователь {callback.from_user.id} нажал 'Найти команду'")


@router.callback_query(F.data == "wait")
async def wait_action(callback: CallbackQuery):
    """Подождать с поиском"""
    await callback.answer()
    await callback.message.edit_text(
        "👌 Хорошо! Когда будешь готов, используй /search для поиска teammates."
    )
    logger.info(f"[START] Пользователь {callback.from_user.id} нажал 'Подожду'")
