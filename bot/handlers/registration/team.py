"""
Регистрация команды (TEAM).

Чистый, простой код без дублирования.
Вся общая логика вынесена в base.py.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from utils.states import TeamRegistration
from utils.texts import (
    TEAM_NAME_REQUEST, TEAM_NAME_ERROR,
    TEAM_IDEA_REQUEST, TEAM_IDEA_ERROR,
    TEAM_SKILLS_REQUEST, TEAM_SKILLS_EMPTY,
    TEAM_REGISTRATION_COMPLETE, COLD_START_MESSAGE,
    format_selected_skills
)
from keyboards.inline import (
    get_skip_keyboard, get_skills_keyboard,
    get_final_actions_keyboard
)
from .base import (
    save_team_and_check_cold_start,
    log_registration_error,
    clear_state_safe,
    COLD_START_THRESHOLD
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "type_team")
async def start_team_registration(callback: CallbackQuery, state: FSMContext):
    """Начало регистрации команды"""
    await callback.answer()
    await callback.message.edit_text(TEAM_NAME_REQUEST, parse_mode="HTML")
    await state.set_state(TeamRegistration.waiting_for_team_name)


@router.message(TeamRegistration.waiting_for_team_name)
async def process_team_name(message: Message, state: FSMContext):
    """Обработка названия команды"""
    team_name = message.text.strip()

    # Валидация
    if len(team_name) < 3 or len(team_name) > 50:
        await message.answer(TEAM_NAME_ERROR)
        return

    await state.update_data(team_name=team_name)
    await message.answer(
        TEAM_IDEA_REQUEST,
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TeamRegistration.waiting_for_idea_description)


@router.callback_query(F.data == "skip", TeamRegistration.waiting_for_idea_description)
async def skip_team_idea(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания идеи"""
    await callback.answer()
    await state.update_data(idea_description=None)
    await callback.message.edit_text(
        TEAM_SKILLS_REQUEST,
        reply_markup=get_skills_keyboard()
    )
    await state.update_data(selected_skills=[])
    await state.set_state(TeamRegistration.waiting_for_skills_selection)


@router.message(TeamRegistration.waiting_for_idea_description)
async def process_team_idea(message: Message, state: FSMContext):
    """Обработка описания идеи"""
    idea_description = message.text.strip()

    # Валидация
    if len(idea_description) > 200:
        await message.answer(TEAM_IDEA_ERROR)
        return

    await state.update_data(idea_description=idea_description)
    await message.answer(
        TEAM_SKILLS_REQUEST,
        reply_markup=get_skills_keyboard()
    )
    await state.update_data(selected_skills=[])
    await state.set_state(TeamRegistration.waiting_for_skills_selection)


@router.callback_query(F.data.startswith("skill_"), TeamRegistration.waiting_for_skills_selection)
async def toggle_team_skill(callback: CallbackQuery, state: FSMContext):
    """Переключение навыка"""
    skill_key = callback.data.replace("skill_", "")
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Переключаем
    if skill_key in selected_skills:
        selected_skills.remove(skill_key)
    else:
        selected_skills.append(skill_key)

    await state.update_data(selected_skills=selected_skills)
    await callback.message.edit_reply_markup(
        reply_markup=get_skills_keyboard(selected_skills)
    )
    await callback.answer()


@router.callback_query(F.data == "skills_done", TeamRegistration.waiting_for_skills_selection)
async def finish_team_registration(callback: CallbackQuery, state: FSMContext):
    """Завершение регистрации команды"""
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Валидация
    if not selected_skills:
        await callback.answer(TEAM_SKILLS_EMPTY, show_alert=True)
        return

    team_name = data.get("team_name")
    idea_description = data.get("idea_description")
    needed_skills = format_selected_skills(selected_skills)

    try:
        # Сохраняем через общую функцию
        user, team, total_users = await save_team_and_check_cold_start(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
            team_name=team_name,
            idea_description=idea_description,
            needed_skills=needed_skills
        )

        # Формируем сообщение
        final_message = TEAM_REGISTRATION_COMPLETE.format(team_name=team_name)
        if total_users < COLD_START_THRESHOLD:
            final_message += COLD_START_MESSAGE

        await callback.message.edit_text(
            final_message,
            reply_markup=get_final_actions_keyboard(),
            parse_mode="HTML"
        )

        await clear_state_safe(state)
        await callback.answer("✅ Команда успешно зарегистрирована!")

    except Exception as e:
        log_registration_error("TEAM", e)
        await callback.answer("❌ Произошла ошибка. Попробуйте еще раз.", show_alert=True)
