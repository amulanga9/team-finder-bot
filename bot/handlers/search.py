"""Обработчики поиска teammates"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from database.db import async_session_maker
from database import crud
from utils.texts import (
    SEARCH_RESULTS_HEADER, SEARCH_NO_RESULTS, SEARCH_USER_CARD,
    USER_DETAIL, INVITATION_SENT, INVITATION_LIMIT_REACHED,
    BUTTON_INVITE, BUTTON_DETAIL, BUTTON_CHANGE_SKILLS, BUTTON_OK_WAIT,
    format_user_activity, get_activity_status, is_recommended
)

router = Router()
logger = logging.getLogger(__name__)

MAX_INVITATIONS_PER_DAY = 5


@router.message(Command("search"))
async def cmd_search(message: Message):
    """Команда /search - поиск teammates"""
    try:
        async with async_session_maker() as session:
            # Получаем пользователя
            user = await crud.get_user_by_telegram_id(session, message.from_user.id)

            if not user:
                await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
                return

            # Получаем команду пользователя
            teams = await crud.get_teams_by_leader(session, user.id)

            if not teams:
                await message.answer(
                    "❌ У вас нет команды.\n\n"
                    "Сначала создайте команду с помощью /start"
                )
                return

            # Берем первую команду (пока поддерживаем только одну команду на пользователя)
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
                # Никого не нашли
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
            for found_user in found_users[:10]:  # Максимум 10 результатов
                await send_user_card(message, found_user, team.id)

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await message.answer("❌ Произошла ошибка при поиске. Попробуйте еще раз.")


async def send_user_card(message: Message, user, team_id: int):
    """Отправить карточку пользователя"""
    # Форматируем навыки
    skills = user.primary_skill
    if user.additional_skills:
        skills += f" + {user.additional_skills}"

    # Форматируем активность
    last_active_str = format_user_activity(user.last_active)
    recommended = is_recommended(user.last_active)

    # Текст карточки
    card_text = SEARCH_USER_CARD.format(
        name=user.name,
        recommended=recommended,
        skills=skills,
        last_active=last_active_str
    )

    # Кнопки
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

            # Форматируем навыки
            skills = user.primary_skill
            if user.additional_skills:
                skills += f", {user.additional_skills}"

            # Форматируем идею
            idea_parts = []
            if user.idea_what:
                idea_parts.append(f"Что: {user.idea_what}")
            if user.idea_who:
                idea_parts.append(f"Для кого: {user.idea_who}")
            idea = "\n".join(idea_parts) if idea_parts else "Не указано"

            # Форматируем активность
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
    """Отправить приглашение пользователю"""
    parts = callback.data.split("_")
    to_user_id = int(parts[1])
    team_id = int(parts[2])

    try:
        async with async_session_maker() as session:
            # Получаем отправителя
            from_user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not from_user:
                await callback.answer("❌ Ошибка авторизации", show_alert=True)
                return

            # Проверяем лимит
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

            # Получаем получателя
            to_user = await crud.get_user_by_id(session, to_user_id)

            if not to_user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            # Создаем приглашение
            invitation = await crud.create_invitation(
                session=session,
                from_user_id=from_user.id,
                to_user_id=to_user.id,
                from_team_id=team_id
            )

            logger.info(f"Создано приглашение: {invitation.id} от {from_user.id} к {to_user.id}")

            # Отправляем уведомление отправителю
            await callback.message.answer(
                INVITATION_SENT.format(name=to_user.name)
            )

            # TODO: Отправить уведомление получателю через бота
            # Это требует хранения bot instance или использования webhook

            await callback.answer("✅ Приглашение отправлено!")

    except Exception as e:
        logger.error(f"Ошибка при отправке приглашения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "change_skills")
async def change_skills(callback: CallbackQuery):
    """Изменить нужные навыки (TODO)"""
    await callback.answer("Функция будет добавлена позже", show_alert=True)
