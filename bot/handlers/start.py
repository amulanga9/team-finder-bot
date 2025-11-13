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
from utils.states import TeamRegistration, CofounderRegistration, SeekerRegistration
from utils.texts import (
    START_MESSAGE,
    # Team
    TEAM_NAME_REQUEST, TEAM_NAME_ERROR,
    TEAM_IDEA_REQUEST, TEAM_IDEA_ERROR, TEAM_SKILLS_REQUEST,
    TEAM_SKILLS_EMPTY, TEAM_REGISTRATION_COMPLETE,
    # Cofounder
    COFOUNDER_NAME_REQUEST, COFOUNDER_NAME_ERROR,
    COFOUNDER_SKILL_REQUEST, COFOUNDER_IDEA_WHAT_REQUEST,
    COFOUNDER_IDEA_WHAT_ERROR, COFOUNDER_IDEA_WHO_REQUEST,
    COFOUNDER_IDEA_WHO_ERROR, COFOUNDER_REGISTRATION_COMPLETE,
    # Seeker
    SEEKER_NAME_REQUEST, SEEKER_NAME_ERROR,
    SEEKER_SKILLS_REQUEST, SEEKER_SKILLS_ERROR,
    SEEKER_REGISTRATION_COMPLETE,
    # Other
    COLD_START_MESSAGE,
    format_selected_skills, SKILLS_DESCRIPTIONS
)
from keyboards.inline import (
    get_user_type_keyboard, get_skip_keyboard,
    get_skills_keyboard, get_single_skill_keyboard,
    get_limited_skills_keyboard, get_final_actions_keyboard
)

router = Router()
logger = logging.getLogger(__name__)

COLD_START_THRESHOLD = 10  # Порог для "холодного старта"


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    await message.answer(
        START_MESSAGE,
        reply_markup=get_user_type_keyboard()
    )


# ===== РЕГИСТРАЦИЯ КОМАНДЫ =====

@router.callback_query(F.data == "type_team")
async def process_type_team(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа 'Команда'"""
    await callback.answer()
    await callback.message.edit_text(TEAM_NAME_REQUEST, parse_mode="HTML")
    await state.set_state(TeamRegistration.waiting_for_team_name)


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
async def skip_team_idea_description(callback: CallbackQuery, state: FSMContext):
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
async def process_team_idea_description(message: Message, state: FSMContext):
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
async def toggle_team_skill(callback: CallbackQuery, state: FSMContext):
    """Переключение выбора навыка для команды"""
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
async def finish_team_skills_selection(callback: CallbackQuery, state: FSMContext):
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

            # Проверяем холодный старт
            total_users = await crud.count_users(session)

        # Формируем финальное сообщение
        final_message = TEAM_REGISTRATION_COMPLETE.format(team_name=team_name)
        if total_users < COLD_START_THRESHOLD:
            final_message += COLD_START_MESSAGE

        # Отправляем сообщение об успешной регистрации
        await callback.message.edit_text(
            final_message,
            reply_markup=get_final_actions_keyboard(),
            parse_mode="HTML"
        )

        # Очищаем состояние
        await state.clear()
        await callback.answer("✅ Команда успешно зарегистрирована!")

    except Exception as e:
        logger.error(f"Ошибка при сохранении команды: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте еще раз.", show_alert=True)


# ===== РЕГИСТРАЦИЯ СО-ФАУНДЕРА =====

@router.callback_query(F.data == "type_cofounder")
async def process_type_cofounder(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа 'Со-фаундер'"""
    await callback.answer()
    await callback.message.edit_text(COFOUNDER_NAME_REQUEST, parse_mode="HTML")
    await state.set_state(CofounderRegistration.waiting_for_name)


@router.message(CofounderRegistration.waiting_for_name)
async def process_cofounder_name(message: Message, state: FSMContext):
    """Обработка ввода имени со-фаундера"""
    name = message.text.strip()

    # Валидация имени
    if len(name) < 2 or len(name) > 50:
        await message.answer(COFOUNDER_NAME_ERROR)
        return

    # Сохраняем имя
    await state.update_data(name=name)

    # Запрашиваем основной навык
    await message.answer(
        COFOUNDER_SKILL_REQUEST,
        reply_markup=get_single_skill_keyboard()
    )
    await state.set_state(CofounderRegistration.waiting_for_skill)


@router.callback_query(F.data.startswith("single_skill_"), CofounderRegistration.waiting_for_skill)
async def process_cofounder_skill(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора основного навыка со-фаундера"""
    skill_key = callback.data.replace("single_skill_", "")

    # Сохраняем навык
    skill_name = SKILLS_DESCRIPTIONS.get(skill_key, {}).get("name", skill_key)
    await state.update_data(primary_skill=skill_name)

    # Запрашиваем описание идеи (что делает)
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

    # Сохраняем пустое описание
    await state.update_data(idea_what=None)

    # Запрашиваем описание 'для кого'
    await callback.message.edit_text(
        COFOUNDER_IDEA_WHO_REQUEST,
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CofounderRegistration.waiting_for_idea_who)


@router.message(CofounderRegistration.waiting_for_idea_what)
async def process_cofounder_idea_what(message: Message, state: FSMContext):
    """Обработка ввода 'что делает'"""
    idea_what = message.text.strip()

    # Валидация длины
    if len(idea_what) > 200:
        await message.answer(COFOUNDER_IDEA_WHAT_ERROR)
        return

    # Сохраняем описание
    await state.update_data(idea_what=idea_what)

    # Запрашиваем описание 'для кого'
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

    # Сохраняем данные
    await finish_cofounder_registration(callback.message, callback.from_user, state)


@router.message(CofounderRegistration.waiting_for_idea_who)
async def process_cofounder_idea_who(message: Message, state: FSMContext):
    """Обработка ввода 'для кого'"""
    idea_who = message.text.strip()

    # Валидация длины
    if len(idea_who) > 200:
        await message.answer(COFOUNDER_IDEA_WHO_ERROR)
        return

    # Сохраняем описание
    await state.update_data(idea_who=idea_who)

    # Завершаем регистрацию
    await finish_cofounder_registration(message, message.from_user, state)


async def finish_cofounder_registration(message: Message, user_data, state: FSMContext):
    """Завершение регистрации со-фаундера"""
    data = await state.get_data()

    name = data.get("name")
    primary_skill = data.get("primary_skill")
    idea_what = data.get("idea_what")
    idea_who = data.get("idea_who")

    try:
        # Сохраняем в БД
        async with async_session_maker() as session:
            # Создаем пользователя
            user = await crud.create_user(
                session=session,
                telegram_id=user_data.id,
                username=user_data.username,
                name=name,
                user_type=UserType.PARTICIPANT,  # Со-фаундер как участник
                primary_skill=primary_skill,
                idea_what=idea_what,
                idea_who=idea_who
            )
            logger.info(f"Создан со-фаундер: {user.id} ({user.name})")

            # Проверяем холодный старт
            total_users = await crud.count_users(session)

        # Формируем финальное сообщение
        final_message = COFOUNDER_REGISTRATION_COMPLETE.format(name=name)
        if total_users < COLD_START_THRESHOLD:
            final_message += COLD_START_MESSAGE

        # Отправляем сообщение
        await message.answer(
            final_message,
            reply_markup=get_final_actions_keyboard(),
            parse_mode="HTML"
        )

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при сохранении со-фаундера: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")


# ===== РЕГИСТРАЦИЯ СОИСКАТЕЛЯ =====

@router.callback_query(F.data == "type_participant")
async def process_type_participant(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа 'Соискатель'"""
    await callback.answer()
    await callback.message.edit_text(SEEKER_NAME_REQUEST, parse_mode="HTML")
    await state.set_state(SeekerRegistration.waiting_for_name)


@router.message(SeekerRegistration.waiting_for_name)
async def process_seeker_name(message: Message, state: FSMContext):
    """Обработка ввода имени соискателя"""
    name = message.text.strip()

    # Валидация имени
    if len(name) < 2 or len(name) > 50:
        await message.answer(SEEKER_NAME_ERROR)
        return

    # Сохраняем имя
    await state.update_data(name=name)

    # Запрашиваем навыки
    await message.answer(
        SEEKER_SKILLS_REQUEST,
        reply_markup=get_limited_skills_keyboard()
    )
    await state.update_data(selected_skills=[])
    await state.set_state(SeekerRegistration.waiting_for_skills)


@router.callback_query(F.data.startswith("limited_skill_"), SeekerRegistration.waiting_for_skills)
async def toggle_seeker_skill(callback: CallbackQuery, state: FSMContext):
    """Переключение выбора навыка для соискателя (1-3)"""
    skill_key = callback.data.replace("limited_skill_", "")

    # Получаем текущий список выбранных навыков
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Переключаем навык
    if skill_key in selected_skills:
        selected_skills.remove(skill_key)
    else:
        # Проверяем лимит (максимум 3)
        if len(selected_skills) >= 3:
            await callback.answer("⚠️ Можно выбрать максимум 3 навыка!", show_alert=True)
            return
        selected_skills.append(skill_key)

    # Обновляем состояние
    await state.update_data(selected_skills=selected_skills)

    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_limited_skills_keyboard(selected_skills)
    )
    await callback.answer()


@router.callback_query(F.data == "limited_skills_done", SeekerRegistration.waiting_for_skills)
async def finish_seeker_skills_selection(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора навыков соискателя"""
    data = await state.get_data()
    selected_skills = data.get("selected_skills", [])

    # Проверяем количество навыков (1-3)
    if len(selected_skills) < 1 or len(selected_skills) > 3:
        await callback.answer(SEEKER_SKILLS_ERROR, show_alert=True)
        return

    # Получаем данные
    name = data.get("name")

    # Форматируем навыки
    primary_skill = SKILLS_DESCRIPTIONS.get(selected_skills[0], {}).get("name", selected_skills[0])
    additional_skills = format_selected_skills(selected_skills[1:]) if len(selected_skills) > 1 else None

    try:
        # Сохраняем в БД
        async with async_session_maker() as session:
            # Создаем пользователя
            user = await crud.create_user(
                session=session,
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                name=name,
                user_type=UserType.PARTICIPANT,
                primary_skill=primary_skill,
                additional_skills=additional_skills
            )
            logger.info(f"Создан соискатель: {user.id} ({user.name})")

            # Проверяем холодный старт
            total_users = await crud.count_users(session)

        # Формируем финальное сообщение
        final_message = SEEKER_REGISTRATION_COMPLETE.format(name=name)
        if total_users < COLD_START_THRESHOLD:
            final_message += COLD_START_MESSAGE

        # Отправляем сообщение
        await callback.message.edit_text(
            final_message,
            reply_markup=get_final_actions_keyboard(),
            parse_mode="HTML"
        )

        # Очищаем состояние
        await state.clear()
        await callback.answer("✅ Профиль успешно создан!")

    except Exception as e:
        logger.error(f"Ошибка при сохранении соискателя: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте еще раз.", show_alert=True)


# ===== ФИНАЛЬНЫЕ ДЕЙСТВИЯ =====

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
