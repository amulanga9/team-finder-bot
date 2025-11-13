"""Обработчики команды /start и регистрации"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import async_session_maker
from database import crud
from database.models import UserType
from utils.states import TeamRegistration
from utils.texts import (
    START_MESSAGE, TEAM_NAME_REQUEST, TEAM_NAME_ERROR,
    TEAM_IDEA_REQUEST, TEAM_IDEA_ERROR, TEAM_SKILLS_REQUEST,
    TEAM_SKILLS_EMPTY, TEAM_REGISTRATION_COMPLETE,
    format_selected_skills
)
from keyboards.inline import (
    get_user_type_keyboard, get_skip_keyboard,
    get_skills_keyboard, get_final_actions_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    await message.answer(
        START_MESSAGE,
        reply_markup=get_user_type_keyboard()
    )


@router.callback_query(F.data == "type_team")
async def process_type_team(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа 'Команда'"""
    await callback.answer()
    await callback.message.edit_text(TEAM_NAME_REQUEST, parse_mode="HTML")
    await state.set_state(TeamRegistration.waiting_for_team_name)


@router.callback_query(F.data == "type_cofounder")
async def process_type_cofounder(callback: CallbackQuery):
    """Обработка выбора типа 'Со-фаундер' (TODO)"""
    await callback.answer("Эта функция будет добавлена позже", show_alert=True)


@router.callback_query(F.data == "type_participant")
async def process_type_participant(callback: CallbackQuery):
    """Обработка выбора типа 'Участник' (TODO)"""
    await callback.answer("Эта функция будет добавлена позже", show_alert=True)


@router.message(TeamRegistration.waiting_for_team_name)
async def process_team_name(message: Message, state: FSMContext):
    """Обработка ввода названия команды"""
    team_name = message.text.strip()

    # Валидация длины названия
    if len(team_name) < 3 or len(team_name) > 50:
        await message.answer(TEAM_NAME_ERROR)
        return

    # Сохраняем название команды в FSM
    await state.update_data(team_name=team_name)

    # Запрашиваем описание идеи
    await message.answer(
        TEAM_IDEA_REQUEST,
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TeamRegistration.waiting_for_idea_description)


@router.callback_query(F.data == "skip", TeamRegistration.waiting_for_idea_description)
async def skip_idea_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания идеи"""
    await callback.answer()

    # Сохраняем пустое описание
    await state.update_data(idea_description=None)

    # Переходим к выбору навыков
    await callback.message.edit_text(
        TEAM_SKILLS_REQUEST,
        reply_markup=get_skills_keyboard()
    )
    await state.update_data(selected_skills=[])
    await state.set_state(TeamRegistration.waiting_for_skills_selection)


@router.message(TeamRegistration.waiting_for_idea_description)
async def process_idea_description(message: Message, state: FSMContext):
    """Обработка ввода описания идеи"""
    idea_description = message.text.strip()

    # Валидация длины описания
    if len(idea_description) > 200:
        await message.answer(TEAM_IDEA_ERROR)
        return

    # Сохраняем описание идеи
    await state.update_data(idea_description=idea_description)

    # Переходим к выбору навыков
    await message.answer(
        TEAM_SKILLS_REQUEST,
        reply_markup=get_skills_keyboard()
    )
    await state.update_data(selected_skills=[])
    await state.set_state(TeamRegistration.waiting_for_skills_selection)


@router.callback_query(F.data.startswith("skill_"), TeamRegistration.waiting_for_skills_selection)
async def toggle_skill(callback: CallbackQuery, state: FSMContext):
    """Переключение выбора навыка"""
    skill_key = callback.data.replace("skill_", "")

    # Получаем текущий список выбранных навыков
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Переключаем навык
    if skill_key in selected_skills:
        selected_skills.remove(skill_key)
    else:
        selected_skills.append(skill_key)

    # Обновляем состояние
    await state.update_data(selected_skills=selected_skills)

    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_skills_keyboard(selected_skills)
    )
    await callback.answer()


@router.callback_query(F.data == "skills_done", TeamRegistration.waiting_for_skills_selection)
async def finish_skills_selection(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора навыков и сохранение команды"""
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Проверяем, что выбран хотя бы один навык
    if not selected_skills:
        await callback.answer(TEAM_SKILLS_EMPTY, show_alert=True)
        return

    # Получаем данные из FSM
    team_name = data.get("team_name")
    idea_description = data.get("idea_description")

    # Форматируем навыки для сохранения
    needed_skills = format_selected_skills(selected_skills)

    try:
        # Сохраняем в БД
        async with async_session_maker() as session:
            # Проверяем, существует ли пользователь
            user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not user:
                # Создаем нового пользователя-лидера команды
                user = await crud.create_user(
                    session=session,
                    telegram_id=callback.from_user.id,
                    username=callback.from_user.username,
                    name=callback.from_user.full_name,
                    user_type=UserType.TEAM
                )
                logger.info(f"Создан новый пользователь: {user.id} ({user.name})")

            # Создаем команду
            team = await crud.create_team(
                session=session,
                team_name=team_name,
                leader_id=user.id,
                idea_description=idea_description,
                needed_skills=needed_skills
            )
            logger.info(f"Создана команда: {team.id} ({team.team_name})")

        # Отправляем сообщение об успешной регистрации
        await callback.message.edit_text(
            TEAM_REGISTRATION_COMPLETE.format(team_name=team_name),
            reply_markup=get_final_actions_keyboard(),
            parse_mode="HTML"
        )

        # Очищаем состояние
        await state.clear()
        await callback.answer("✅ Команда успешно зарегистрирована!")

    except Exception as e:
        logger.error(f"Ошибка при сохранении команды: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте еще раз.", show_alert=True)


@router.callback_query(F.data == "search_now")
async def search_now(callback: CallbackQuery):
    """Начать поиск teammates (TODO)"""
    await callback.answer("Функция поиска будет добавлена позже", show_alert=True)


@router.callback_query(F.data == "wait")
async def wait_action(callback: CallbackQuery):
    """Подождать с поиском"""
    await callback.answer()
    await callback.message.edit_text(
        "👌 Хорошо! Когда будешь готов, используй /search для поиска teammates."
    )
