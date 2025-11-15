"""Обработчики поиска teammates"""
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from database.db import async_session_maker
from database import crud
from database.models import UserType
from keyboards.inline import (
    get_cofounder_search_keyboard, get_participant_team_keyboard,
    get_search_empty_keyboard
)
from utils.texts import (
    # Для команд
    SEARCH_RESULTS_HEADER, SEARCH_NO_RESULTS, SEARCH_USER_CARD,
    USER_DETAIL, INVITATION_SENT, INVITATION_LIMIT_REACHED,
    BUTTON_INVITE, BUTTON_DETAIL, BUTTON_CHANGE_SKILLS, BUTTON_OK_WAIT,
    format_user_activity, get_activity_status, is_recommended,
    # Для соло-основателей
    COFOUNDER_SEARCH_CARD, COFOUNDER_SEARCH_EMPTY,
    COLLABORATION_REQUEST_SENT, COLLABORATION_REQUEST_RECEIVED,
    format_stars, get_compatibility_text, get_match_reason,
    # Для соискателей
    PARTICIPANT_TEAM_CARD, PARTICIPANT_SEARCH_EMPTY, PARTICIPANT_SEARCH_EMPTY_NO_TEAMS,
    TEAM_INTEREST_SENT, TEAM_INTEREST_RECEIVED
)

router = Router()
logger = logging.getLogger(__name__)

MAX_INVITATIONS_PER_DAY = 5

# Временное хранилище для результатов поиска (в продакшене использовать Redis или FSM)
search_results_cache = {}


@router.message(Command("search"))
async def cmd_search(message: Message):
    """Команда /search - поиск teammates (для всех типов пользователей)"""
    try:
        async with async_session_maker() as session:
            # Получаем пользователя
            user = await crud.get_user_by_telegram_id(session, message.from_user.id)

            if not user:
                await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
                return

            # Маршрутизация по типу пользователя
            if user.user_type == UserType.TEAM:
                await search_for_team(message, user, session)
            elif user.user_type == UserType.COFOUNDER:
                await search_for_cofounder(message, user, session)
            elif user.user_type == UserType.PARTICIPANT:
                await search_for_participant(message, user, session)

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await message.answer("❌ Произошла ошибка при поиске. Попробуйте еще раз.")


# ===== ПОИСК ДЛЯ КОМАНД =====

async def search_for_team(message: Message, user, session):
    """Поиск соискателей для команды"""
    # Получаем команду пользователя
    teams = await crud.get_teams_by_leader(session, user.id)

    if not teams:
        await message.answer(
            "❌ У вас нет команды.\n\n"
            "Сначала создайте команду с помощью /start"
        )
        return

    team = teams[0]

    if not team.needed_skills:
        await message.answer(
            "❌ Не указаны нужные навыки для команды.\n\n"
            "Обновите профиль команды."
        )
        return

    # Ищем пользователей
    found_users = await crud.find_users_by_skills(
        session,
        team.needed_skills,
        exclude_user_id=user.id
    )

    if not found_users:
        keyboard = [
            [InlineKeyboardButton(text=BUTTON_CHANGE_SKILLS, callback_data="change_skills")],
            [InlineKeyboardButton(text=BUTTON_OK_WAIT, callback_data="wait")]
        ]
        await message.answer(
            SEARCH_NO_RESULTS,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        return

    # Показываем результаты
    header = SEARCH_RESULTS_HEADER.format(
        count=len(found_users),
        skills=team.needed_skills
    )
    await message.answer(header)

    # Показываем каждого пользователя
    for found_user in found_users[:10]:
        await send_user_card(message, found_user, team.id)


async def send_user_card(message: Message, user, team_id: int):
    """Отправить карточку пользователя"""
    skills = user.primary_skill
    if user.additional_skills:
        skills += f" + {user.additional_skills}"

    last_active_str = format_user_activity(user.last_active)
    recommended = is_recommended(user.last_active)

    card_text = SEARCH_USER_CARD.format(
        name=user.name,
        recommended=recommended,
        skills=skills,
        last_active=last_active_str
    )

    keyboard = [
        [
            InlineKeyboardButton(text=BUTTON_INVITE, callback_data=f"invite_{user.id}_{team_id}"),
            InlineKeyboardButton(text=BUTTON_DETAIL, callback_data=f"detail_{user.id}")
        ]
    ]

    await message.answer(
        card_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


# ===== ПОИСК ДЛЯ СОЛО-ОСНОВАТЕЛЕЙ =====

async def search_for_cofounder(message: Message, user, session):
    """Поиск других соло-основателей для коллаборации"""
    # Ищем других соло-основателей с расчетом совместимости
    cofounders_with_stars = await crud.find_cofounders(session, user.id)

    if not cofounders_with_stars:
        await message.answer(
            COFOUNDER_SEARCH_EMPTY,
            reply_markup=get_search_empty_keyboard()
        )
        return

    # Сохраняем результаты в кэш для навигации
    cache_key = f"cofounder_search_{user.id}"
    search_results_cache[cache_key] = cofounders_with_stars

    # Показываем первого
    await show_cofounder_card(message, user, cofounders_with_stars, 0)


async def show_cofounder_card(message: Message, current_user, results: list, index: int):
    """Показать карточку соло-основателя"""
    if index >= len(results):
        await message.answer("Больше нет результатов! 🎉\n\nМожете начать поиск заново: /search")
        return

    cofounder, stars = results[index]

    # Формируем идею
    idea = cofounder.idea_what or "Идея в разработке"

    # Форматируем активность
    activity = format_user_activity(cofounder.last_active)

    # Определяем причину совпадения
    match_reason = get_match_reason(
        current_user.primary_skill,
        cofounder.primary_skill,
        same_idea=False  # TODO: проверить похожесть идей
    )

    card_text = COFOUNDER_SEARCH_CARD.format(
        name=cofounder.name,
        activity=activity,
        skill=cofounder.primary_skill or "Не указан",
        idea=idea,
        stars_display=format_stars(stars),
        compatibility_text=get_compatibility_text(stars),
        match_reason=match_reason
    )

    keyboard = get_cofounder_search_keyboard(cofounder.id, index)

    await message.answer(card_text, reply_markup=keyboard)


# ===== ПОИСК ДЛЯ СОИСКАТЕЛЕЙ =====

async def search_for_participant(message: Message, user, session):
    """Поиск команд для соискателя (Tinder-style)"""
    # Ищем команды, которым нужны навыки соискателя
    matching_teams = await crud.find_teams_for_participant(session, user.id)

    if not matching_teams:
        # Считаем сколько команд ищут основной навык
        skill = user.primary_skill or "этот навык"
        teams_count = await crud.count_teams_need_skill(session, skill)

        if teams_count > 0:
            await message.answer(
                PARTICIPANT_SEARCH_EMPTY.format(count=teams_count, skill=skill),
                reply_markup=get_search_empty_keyboard()
            )
        else:
            await message.answer(
                PARTICIPANT_SEARCH_EMPTY_NO_TEAMS,
                reply_markup=get_search_empty_keyboard()
            )
        return

    # Сохраняем результаты в кэш
    cache_key = f"participant_search_{user.id}"
    search_results_cache[cache_key] = matching_teams

    # Показываем первую команду
    await show_team_card(message, matching_teams, 0)


async def show_team_card(message: Message, teams: list, index: int):
    """Показать карточку команды (Tinder-style)"""
    if index >= len(teams):
        await message.answer("Больше нет команд! 🎉\n\nМожете начать поиск заново: /search")
        return

    team = teams[index]

    # Форматируем идею
    idea = team.idea_description if team.idea_description else "Описание отсутствует"

    card_text = PARTICIPANT_TEAM_CARD.format(
        team_name=team.team_name,
        idea=idea,
        needed_skills=team.needed_skills or "Не указаны"
    )

    keyboard = get_participant_team_keyboard(team.id, index)

    await message.answer(card_text, reply_markup=keyboard)


# ===== CALLBACK HANDLERS =====

@router.callback_query(F.data.startswith("detail_"))
async def show_user_detail(callback: CallbackQuery):
    """Показать детальную информацию о пользователе"""
    user_id = int(callback.data.split("_")[1])

    try:
        async with async_session_maker() as session:
            user = await crud.get_user_by_id(session, user_id)

            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            skills = user.primary_skill
            if user.additional_skills:
                skills += f", {user.additional_skills}"

            idea_parts = []
            if user.idea_what:
                idea_parts.append(f"Что: {user.idea_what}")
            if user.idea_who:
                idea_parts.append(f"Для кого: {user.idea_who}")
            idea = "\n".join(idea_parts) if idea_parts else "Не указано"

            last_active_str = format_user_activity(user.last_active)
            activity_status = get_activity_status(user.last_active)

            detail_text = USER_DETAIL.format(
                name=user.name,
                skills=skills,
                idea=idea,
                last_active=last_active_str,
                activity_status=activity_status
            )

            await callback.message.answer(detail_text, parse_mode="HTML")
            await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе деталей: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("invite_"))
async def send_invitation(callback: CallbackQuery):
    """Отправить приглашение пользователю (от команды)"""
    parts = callback.data.split("_")
    to_user_id = int(parts[1])
    team_id = int(parts[2])

    try:
        async with async_session_maker() as session:
            from_user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not from_user:
                await callback.answer("❌ Ошибка авторизации", show_alert=True)
                return

            can_invite = await crud.check_invitation_limit(session, from_user.id, MAX_INVITATIONS_PER_DAY)

            if not can_invite:
                count = await crud.count_invitations_today(session, from_user.id)
                await callback.answer(
                    INVITATION_LIMIT_REACHED.format(
                        limit=MAX_INVITATIONS_PER_DAY,
                        count=count
                    ),
                    show_alert=True
                )
                return

            to_user = await crud.get_user_by_id(session, to_user_id)

            if not to_user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            invitation = await crud.create_invitation(
                session=session,
                from_user_id=from_user.id,
                to_user_id=to_user.id,
                from_team_id=team_id
            )

            logger.info(f"Создано приглашение: {invitation.id} от {from_user.id} к {to_user.id}")

            await callback.message.answer(
                INVITATION_SENT.format(name=to_user.name)
            )

            await callback.answer("✅ Приглашение отправлено!")

    except Exception as e:
        logger.error(f"Ошибка при отправке приглашения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("send_collab_"))
async def send_collaboration_request(callback: CallbackQuery, bot: Bot):
    """Отправить запрос на коллаборацию (от соло к соло)"""
    parts = callback.data.split("_")
    to_user_id = int(parts[2])
    current_index = int(parts[3])

    try:
        async with async_session_maker() as session:
            from_user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not from_user:
                await callback.answer("❌ Ошибка авторизации", show_alert=True)
                return

            # Проверяем лимит
            can_invite = await crud.check_invitation_limit(session, from_user.id, MAX_INVITATIONS_PER_DAY)

            if not can_invite:
                count = await crud.count_invitations_today(session, from_user.id)
                await callback.answer(
                    f"⚠️ Лимит запросов на сегодня ({count}/{MAX_INVITATIONS_PER_DAY})",
                    show_alert=True
                )
                return

            to_user = await crud.get_user_by_id(session, to_user_id)

            if not to_user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            # Создаем приглашение (без team_id для коллаборации)
            invitation = await crud.create_invitation(
                session=session,
                from_user_id=from_user.id,
                to_user_id=to_user.id,
                from_team_id=None
            )

            # Уведомляем отправителя
            await callback.message.answer(
                COLLABORATION_REQUEST_SENT.format(name=to_user.name)
            )

            # Уведомляем получателя
            idea = from_user.idea_what or "Идея в разработке"
            if to_user.telegram_id:
                try:
                    await bot.send_message(
                        to_user.telegram_id,
                        COLLABORATION_REQUEST_RECEIVED.format(
                            name=from_user.name,
                            skill=from_user.primary_skill or "Не указан",
                            idea=idea
                        )
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление: {e}")

            await callback.answer("✅ Запрос отправлен!")

    except Exception as e:
        logger.error(f"Ошибка при отправке запроса: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("next_cofounder_"))
async def next_cofounder(callback: CallbackQuery):
    """Показать следующего соло-основателя"""
    current_index = int(callback.data.split("_")[2])
    next_index = current_index + 1

    try:
        async with async_session_maker() as session:
            from_user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not from_user:
                await callback.answer("❌ Ошибка", show_alert=True)
                return

            cache_key = f"cofounder_search_{from_user.id}"
            results = search_results_cache.get(cache_key, [])

            if not results:
                await callback.answer("❌ Результаты поиска устарели. Начните поиск заново: /search", show_alert=True)
                return

            # Удаляем предыдущее сообщение
            try:
                await callback.message.delete()
            except:
                pass

            # Показываем следующего
            await show_cofounder_card(callback.message, from_user, results, next_index)
            await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при переходе к следующему: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("interested_team_"))
async def interested_in_team(callback: CallbackQuery, bot: Bot):
    """Соискатель заинтересован в команде"""
    parts = callback.data.split("_")
    team_id = int(parts[2])
    current_index = int(parts[3])

    try:
        async with async_session_maker() as session:
            from_user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not from_user:
                await callback.answer("❌ Ошибка авторизации", show_alert=True)
                return

            team = await crud.get_team_by_id(session, team_id)

            if not team:
                await callback.answer("❌ Команда не найдена", show_alert=True)
                return

            # Создаем запрос от соискателя к команде
            invitation = await crud.create_invitation(
                session=session,
                from_user_id=from_user.id,
                to_user_id=team.leader_id,
                from_team_id=None
            )

            # Уведомляем соискателя
            await callback.message.answer(
                TEAM_INTEREST_SENT.format(team_name=team.team_name)
            )

            # Уведомляем лидера команды
            leader = await crud.get_user_by_id(session, team.leader_id)
            if leader and leader.telegram_id:
                skills = from_user.primary_skill
                if from_user.additional_skills:
                    skills += f", {from_user.additional_skills}"

                try:
                    await bot.send_message(
                        leader.telegram_id,
                        TEAM_INTEREST_RECEIVED.format(
                            name=from_user.name,
                            skills=skills
                        )
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление лидеру: {e}")

            await callback.answer("✅ Заявка отправлена!")

            # Показываем следующую команду
            await show_next_team(callback, current_index)

    except Exception as e:
        logger.error(f"Ошибка при отправке заявки: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("skip_team_"))
async def skip_team(callback: CallbackQuery):
    """Пропустить команду"""
    current_index = int(callback.data.split("_")[2])

    await callback.answer("Пропускаем...")
    await show_next_team(callback, current_index)


async def show_next_team(callback: CallbackQuery, current_index: int):
    """Показать следующую команду"""
    next_index = current_index + 1

    try:
        async with async_session_maker() as session:
            from_user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not from_user:
                return

            cache_key = f"participant_search_{from_user.id}"
            teams = search_results_cache.get(cache_key, [])

            if not teams:
                await callback.message.answer("❌ Результаты поиска устарели. Начните поиск заново: /search")
                return

            # Удаляем предыдущее сообщение
            try:
                await callback.message.delete()
            except:
                pass

            # Показываем следующую команду
            await show_team_card(callback.message, teams, next_index)

    except Exception as e:
        logger.error(f"Ошибка при показе следующей команды: {e}")


@router.callback_query(F.data == "change_skills")
async def change_skills(callback: CallbackQuery):
    """Изменить нужные навыки (TODO)"""
    await callback.answer("Функция будет добавлена позже", show_alert=True)


@router.callback_query(F.data == "wait_notify")
async def wait_notify(callback: CallbackQuery):
    """Подождать уведомлений"""
    await callback.answer("✅ Мы уведомим вас когда появятся новые результаты!")
    try:
        await callback.message.delete()
    except:
        pass
