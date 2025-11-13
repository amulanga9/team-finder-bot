"""Обработчики команды /profile"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database.db import async_session_maker
from database import crud
from database.models import UserType, InvitationStatus
from keyboards.inline import get_profile_keyboard, get_invitation_response_keyboard
from utils.texts import (
    PROFILE_PARTICIPANT, PROFILE_COFOUNDER, PROFILE_TEAM,
    SENT_REQUESTS_SECTION, RECEIVED_INVITATIONS_SECTION,
    NO_SENT_REQUESTS, NO_RECEIVED_INVITATIONS,
    COFOUNDER_REQUESTS_SECTION, COFOUNDER_TIP,
    format_invitation_status, format_request_status,
    get_profile_tip, get_activity_status
)

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Показать профиль пользователя"""
    async with async_session_maker() as session:
        # Получаем пользователя
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("❌ Вы не зарегистрированы. Используйте /start")
            return

        # Получаем статистику
        stats = await crud.get_user_stats(session, user.id)
        if not stats:
            await message.answer("❌ Ошибка получения статистики")
            return

        # Формируем профиль в зависимости от типа пользователя
        if user.user_type == UserType.PARTICIPANT:
            await show_participant_profile(message, stats, session)
        elif user.user_type == UserType.COFOUNDER:
            await show_cofounder_profile(message, stats, session)
        elif user.user_type == UserType.TEAM:
            await show_team_leader_profile(message, stats, session)


async def show_participant_profile(message: Message, stats: dict, session):
    """Показать профиль соискателя"""
    user = stats['user']
    days = stats['days_registered']
    sent_invitations = stats['sent_invitations']
    received_invitations = stats['received_invitations']

    # Формируем список навыков
    skills = []
    if user.primary_skill:
        skills.append(user.primary_skill)
    if user.additional_skills:
        skills.append(user.additional_skills)
    skills_text = ", ".join(skills) if skills else "Не указаны"

    # Статус активности
    status_line = f"🟢 Статус: {get_activity_status(user.last_active)}"

    # Основной текст профиля
    profile_text = PROFILE_PARTICIPANT.format(
        name=user.name,
        skills=skills_text,
        days=days,
        status_line=status_line
    )

    # Добавляем отправленные запросы
    if sent_invitations:
        requests_lines = []
        for inv in sent_invitations:
            # Получаем информацию о команде или пользователе
            if inv.from_team_id:
                team = await crud.get_team_by_id(session, inv.from_team_id)
                team_name = team.team_name if team else "Неизвестная команда"
                to_user = await crud.get_user_by_id(session, inv.to_user_id)
                to_username = to_user.username if to_user and to_user.username else None
            else:
                team_name = "Запрос"
                to_username = None

            status = format_invitation_status(inv, to_username)
            requests_lines.append(f"• {team_name} - {status}")

        requests_text = "\n".join(requests_lines[:5])  # Показываем до 5
        profile_text += SENT_REQUESTS_SECTION.format(requests=requests_text)
    else:
        profile_text += f"\n\n{NO_SENT_REQUESTS}"

    # Добавляем приглашения от команд
    pending_invitations = [inv for inv in received_invitations if inv.status == InvitationStatus.PENDING]
    if pending_invitations:
        inv_lines = []
        for inv in pending_invitations[:3]:  # Показываем до 3
            if inv.from_team_id:
                team = await crud.get_team_by_id(session, inv.from_team_id)
                team_name = team.team_name if team else "Неизвестная команда"
            else:
                from_user = await crud.get_user_by_id(session, inv.from_user_id)
                team_name = from_user.name if from_user else "Пользователь"

            inv_lines.append(f"• {team_name} - ⏳ Ждут ответа")

        inv_text = "\n".join(inv_lines)
        profile_text += RECEIVED_INVITATIONS_SECTION.format(invitations=inv_text)
    else:
        profile_text += f"\n\n{NO_RECEIVED_INVITATIONS}"

    # Отправляем профиль с клавиатурой
    keyboard = get_profile_keyboard("participant")
    await message.answer(profile_text, reply_markup=keyboard)

    # Если есть ожидающие приглашения, показываем их с кнопками
    if pending_invitations:
        for inv in pending_invitations[:3]:
            if inv.from_team_id:
                team = await crud.get_team_by_id(session, inv.from_team_id)
                team_name = team.team_name if team else "Неизвестная команда"
                team_idea = team.idea_description if team and team.idea_description else "Не указана"
            else:
                from_user = await crud.get_user_by_id(session, inv.from_user_id)
                team_name = from_user.name if from_user else "Пользователь"
                team_idea = "Личное приглашение"

            inv_text = f"<b>{team_name}</b>\n💡 {team_idea}"
            keyboard = get_invitation_response_keyboard(inv.id)
            await message.answer(inv_text, reply_markup=keyboard)


async def show_cofounder_profile(message: Message, stats: dict, session):
    """Показать профиль со-фаундера"""
    user = stats['user']
    days = stats['days_registered']
    sent_invitations = stats['sent_invitations']

    # Формируем идею
    idea_parts = []
    if user.idea_what:
        idea_parts.append(user.idea_what)
    if user.idea_who:
        idea_parts.append(f"для {user.idea_who}")
    idea_text = " ".join(idea_parts) if idea_parts else "Не указана"

    # Основной текст профиля
    profile_text = PROFILE_COFOUNDER.format(
        name=user.name,
        skill=user.primary_skill or "Не указан",
        idea=idea_text,
        days=days
    )

    # Добавляем запросы
    if sent_invitations:
        requests_lines = []
        for inv in sent_invitations:
            to_user = await crud.get_user_by_id(session, inv.to_user_id)
            to_name = to_user.name if to_user else "Пользователь"
            to_username = to_user.username if to_user and to_user.username else None

            status = format_request_status(inv, to_username)
            requests_lines.append(f"• {to_name} - {status}")

        requests_text = "\n".join(requests_lines[:5])
        profile_text += COFOUNDER_REQUESTS_SECTION.format(requests=requests_text)

        # Считаем неотвеченные запросы
        pending_count = sum(1 for inv in sent_invitations if inv.status == InvitationStatus.PENDING)
        tip = get_profile_tip(pending_count, "cofounder")
        if tip:
            profile_text += COFOUNDER_TIP.format(tip=tip)
    else:
        profile_text += f"\n\nПока нет отправленных запросов"

    # Отправляем профиль
    keyboard = get_profile_keyboard("cofounder")
    await message.answer(profile_text, reply_markup=keyboard)


async def show_team_leader_profile(message: Message, stats: dict, session):
    """Показать профиль лидера команды"""
    user = stats['user']
    days = stats['days_registered']

    # Получаем команду
    teams = await crud.get_teams_by_leader(session, user.id)
    team_name = teams[0].team_name if teams else "Не указана"

    # Статус активности
    status_line = f"🟢 Статус: {get_activity_status(user.last_active)}"

    # Основной текст профиля
    profile_text = PROFILE_TEAM.format(
        name=user.name,
        team_name=team_name,
        days=days,
        status_line=status_line
    )

    profile_text += f"\n\nДля статистики команды используйте /team"

    # Отправляем профиль
    keyboard = get_profile_keyboard("team")
    await message.answer(profile_text, reply_markup=keyboard)
