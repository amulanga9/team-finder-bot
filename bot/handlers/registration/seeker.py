"""
Регистрация соискателя (SEEKER/PARTICIPANT).

Чистый, простой код без дублирования.
Вся общая логика вынесена в base.py.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.models import UserType
from utils.states import SeekerRegistration
from utils.texts import (
    SEEKER_NAME_REQUEST, SEEKER_NAME_ERROR,
    SEEKER_SKILLS_REQUEST, SEEKER_SKILLS_ERROR,
    SEEKER_REGISTRATION_COMPLETE, COLD_START_MESSAGE,
    SKILLS_DESCRIPTIONS, format_selected_skills
)
from keyboards.inline import (
    get_limited_skills_keyboard,
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


@router.callback_query(F.data == "type_participant")
async def start_seeker_registration(callback: CallbackQuery, state: FSMContext):
    """Начало регистрации соискателя"""
    await callback.answer()
    await callback.message.edit_text(SEEKER_NAME_REQUEST, parse_mode="HTML")
    await state.set_state(SeekerRegistration.waiting_for_name)


@router.message(SeekerRegistration.waiting_for_name)
async def process_seeker_name(message: Message, state: FSMContext):
    """Обработка имени"""
    name = message.text.strip()

    # Валидация
    if len(name) < 2 or len(name) > 50:
        await message.answer(SEEKER_NAME_ERROR)
        return

    await state.update_data(name=name)
    await message.answer(
        SEEKER_SKILLS_REQUEST,
        reply_markup=get_limited_skills_keyboard()
    )
    await state.update_data(selected_skills=[])
    await state.set_state(SeekerRegistration.waiting_for_skills)


@router.callback_query(F.data.startswith("limited_skill_"), SeekerRegistration.waiting_for_skills)
async def toggle_seeker_skill(callback: CallbackQuery, state: FSMContext):
    """Переключение навыка (макс 3)"""
    skill_key = callback.data.replace("limited_skill_", "")
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Переключаем
    if skill_key in selected_skills:
        selected_skills.remove(skill_key)
    else:
        # Проверяем лимит
        if len(selected_skills) >= 3:
            await callback.answer("⚠️ Можно выбрать максимум 3 навыка!", show_alert=True)
            return
        selected_skills.append(skill_key)

    await state.update_data(selected_skills=selected_skills)
    await callback.message.edit_reply_markup(
        reply_markup=get_limited_skills_keyboard(selected_skills)
    )
    await callback.answer()


@router.callback_query(F.data == "limited_skills_done", SeekerRegistration.waiting_for_skills)
async def finish_seeker_registration(callback: CallbackQuery, state: FSMContext):
    """Завершение регистрации соискателя"""
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Валидация (1-3 навыка)
    if len(selected_skills) < 1 or len(selected_skills) > 3:
        await callback.answer(SEEKER_SKILLS_ERROR, show_alert=True)
        return

    name = data.get("name")

    # Форматируем навыки
    primary_skill = SKILLS_DESCRIPTIONS.get(selected_skills[0], {}).get("name", selected_skills[0])
    additional_skills = format_selected_skills(selected_skills[1:]) if len(selected_skills) > 1 else None

    try:
        # Сохраняем через общую функцию
        user, total_users, is_new_user = await save_user_and_check_cold_start(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            name=name,
            user_type=UserType.PARTICIPANT,
            primary_skill=primary_skill,
            additional_skills=additional_skills
        )

        # Формируем сообщение
        final_message = SEEKER_REGISTRATION_COMPLETE.format(name=name)
        if total_users < COLD_START_THRESHOLD:
            final_message += COLD_START_MESSAGE

        await callback.message.edit_text(
            final_message,
            reply_markup=get_final_actions_keyboard(),
            parse_mode="HTML"
        )

        await clear_state_safe(state)

        # Показываем правильное сообщение
        if is_new_user:
            await callback.answer("✅ Профиль успешно создан!")
        else:
            await callback.answer("✅ Профиль успешно обновлен!")

    except Exception as e:
        log_registration_error("SEEKER", e)
        await callback.answer("❌ Произошла ошибка. Попробуйте еще раз.", show_alert=True)
