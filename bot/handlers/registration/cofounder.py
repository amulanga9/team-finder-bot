"""
Регистрация со-фаундера (COFOUNDER).

Чистый, простой код без дублирования.
Вся общая логика вынесена в base.py.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.models import UserType
from utils.states import CofounderRegistration
from utils.texts import (
    COFOUNDER_NAME_REQUEST, COFOUNDER_NAME_ERROR,
    COFOUNDER_SKILL_REQUEST, COFOUNDER_IDEA_WHAT_REQUEST,
    COFOUNDER_IDEA_WHAT_ERROR, COFOUNDER_IDEA_WHO_REQUEST,
    COFOUNDER_IDEA_WHO_ERROR, COFOUNDER_REGISTRATION_COMPLETE,
    COLD_START_MESSAGE, SKILLS_DESCRIPTIONS
)
from keyboards.inline import (
    get_single_skill_keyboard, get_skip_keyboard,
    get_final_actions_keyboard
)
from .base import (
    save_user_and_check_cold_start,
    log_registration_error,
    clear_state_safe,
    COLD_START_THRESHOLD
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "type_cofounder")
async def start_cofounder_registration(callback: CallbackQuery, state: FSMContext):
    """Начало регистрации со-фаундера"""
    await callback.answer()
    await callback.message.edit_text(COFOUNDER_NAME_REQUEST, parse_mode="HTML")
    await state.set_state(CofounderRegistration.waiting_for_name)


@router.message(CofounderRegistration.waiting_for_name)
async def process_cofounder_name(message: Message, state: FSMContext):
    """Обработка имени"""
    name = message.text.strip()

    # Валидация
    if len(name) < 2 or len(name) > 50:
        await message.answer(COFOUNDER_NAME_ERROR)
        return

    await state.update_data(name=name)
    await message.answer(
        COFOUNDER_SKILL_REQUEST,
        reply_markup=get_single_skill_keyboard()
    )
    await state.set_state(CofounderRegistration.waiting_for_skill)


@router.callback_query(F.data.startswith("single_skill_"), CofounderRegistration.waiting_for_skill)
async def process_cofounder_skill(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора навыка"""
    skill_key = callback.data.replace("single_skill_", "")
    skill_name = SKILLS_DESCRIPTIONS.get(skill_key, {}).get("name", skill_key)

    await state.update_data(primary_skill=skill_name)
    await callback.message.edit_text(
        COFOUNDER_IDEA_WHAT_REQUEST,
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CofounderRegistration.waiting_for_idea_what)
    await callback.answer()


@router.callback_query(F.data == "skip", CofounderRegistration.waiting_for_idea_what)
async def skip_cofounder_idea_what(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания 'что делает'"""
    await callback.answer()
    await state.update_data(idea_what=None)
    await callback.message.edit_text(
        COFOUNDER_IDEA_WHO_REQUEST,
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CofounderRegistration.waiting_for_idea_who)


@router.message(CofounderRegistration.waiting_for_idea_what)
async def process_cofounder_idea_what(message: Message, state: FSMContext):
    """Обработка 'что делает'"""
    idea_what = message.text.strip()

    # Валидация
    if len(idea_what) > 200:
        await message.answer(COFOUNDER_IDEA_WHAT_ERROR)
        return

    await state.update_data(idea_what=idea_what)
    await message.answer(
        COFOUNDER_IDEA_WHO_REQUEST,
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CofounderRegistration.waiting_for_idea_who)


@router.callback_query(F.data == "skip", CofounderRegistration.waiting_for_idea_who)
async def skip_cofounder_idea_who(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания 'для кого'"""
    await callback.answer()
    await state.update_data(idea_who=None)
    await finish_cofounder_registration(callback.message, callback.from_user, state)


@router.message(CofounderRegistration.waiting_for_idea_who)
async def process_cofounder_idea_who(message: Message, state: FSMContext):
    """Обработка 'для кого'"""
    idea_who = message.text.strip()

    # Валидация
    if len(idea_who) > 200:
        await message.answer(COFOUNDER_IDEA_WHO_ERROR)
        return

    await state.update_data(idea_who=idea_who)
    await finish_cofounder_registration(message, message.from_user, state)


async def finish_cofounder_registration(message: Message, user_data, state: FSMContext):
    """Завершение регистрации со-фаундера"""
    data = await state.get_data()

    name = data.get("name")
    primary_skill = data.get("primary_skill")
    idea_what = data.get("idea_what")
    idea_who = data.get("idea_who")

    try:
        # Сохраняем через общую функцию
        user, total_users = await save_user_and_check_cold_start(
            telegram_id=user_data.id,
            username=user_data.username,
            name=name,
            user_type=UserType.PARTICIPANT,  # Со-фаундер = участник
            primary_skill=primary_skill,
            idea_what=idea_what,
            idea_who=idea_who
        )

        # Формируем сообщение
        final_message = COFOUNDER_REGISTRATION_COMPLETE.format(name=name)
        if total_users < COLD_START_THRESHOLD:
            final_message += COLD_START_MESSAGE

        await message.answer(
            final_message,
            reply_markup=get_final_actions_keyboard(),
            parse_mode="HTML"
        )

        await clear_state_safe(state)

    except Exception as e:
        log_registration_error("COFOUNDER", e)
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")
