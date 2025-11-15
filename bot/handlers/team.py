"""Обработчики команды /team"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database.db import async_session_maker
from database import crud
from database.models import UserType, InvitationStatus
from keyboards.inline import get_profile_keyboard, get_invitation_response_keyboard
from utils.texts import (
    TEAM_STATS, TEAM_INVITATIONS_SECTION, TEAM_REQUESTS_SECTION,
    NO_TEAM_INVITATIONS, NO_TEAM_REQUESTS, TEAM_TIP,
    format_invitation_status, format_request_status,
    get_profile_tip
)

router = Router()


@router.message(Command("team"))
async def cmd_team(message: Message):
    """Показать статистику команды (только для team_lead)"""
    async with async_session_maker() as session:
        # Получаем пользователя
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("❌ Вы не зарегистрированы. Используйте /start")
            return

        # Проверяем, что это лидер команды
        if user.user_type != UserType.TEAM:
            await message.answer("❌ Эта команда доступна только для лидеров команд.\nИспользуйте /profile")
            return

        # Получаем команду
        teams = await crud.get_teams_by_leader(session, user.id)
        if not teams:
            await message.answer("❌ У вас нет команды. Используйте /start для создания.")
            return

        team = teams[0]  # Берем первую команду

        # Получаем статистику команды
        team_stats = await crud.get_team_stats(session, team.id)
        if not team_stats:
            await message.answer("❌ Ошибка получения статистики команды")
            return

        # Подсчитываем просмотры (количество отправленных приглашений как прокси)
        views_count = len(team_stats['sent_invitations'])

        # Основной текст статистики
        stats_text = TEAM_STATS.format(
            team_name=team.team_name,
            views=views_count,
            matching=team_stats['matching_users_count']
        )

        # Добавляем приглашения от команды
        sent_invitations = team_stats['sent_invitations']
        if sent_invitations:
            inv_lines = []
            for inv in sent_invitations[:5]:  # Показываем до 5
                to_user = await crud.get_user_by_id(session, inv.to_user_id)
                to_name = to_user.name if to_user else "Пользователь"
                to_username = to_user.username if to_user and to_user.username else None

                status = format_invitation_status(inv, to_username)
                inv_lines.append(f"• {to_name} - {status}")

            inv_text = "\n".join(inv_lines)
            stats_text += TEAM_INVITATIONS_SECTION.format(invitations=inv_text)
        else:
            stats_text += f"\n\n{NO_TEAM_INVITATIONS}"

        # Добавляем запросы от соискателей
        received_requests = team_stats['received_requests']
        if received_requests:
            req_lines = []
            pending_requests = []

            for req in received_requests[:5]:  # Показываем до 5
                from_user = await crud.get_user_by_id(session, req.from_user_id)
                from_name = from_user.name if from_user else "Пользователь"
                from_username = from_user.username if from_user and from_user.username else None

                status = format_request_status(req, from_username)
                req_lines.append(f"• {from_name} - {status}")

                if req.status == InvitationStatus.PENDING:
                    pending_requests.append((req, from_user))

            req_text = "\n".join(req_lines)
            stats_text += TEAM_REQUESTS_SECTION.format(requests=req_text)

            # Считаем неотвеченные запросы
            pending_count = sum(1 for req in received_requests if req.status == InvitationStatus.PENDING)
            tip = get_profile_tip(pending_count, "team")
            if tip:
                stats_text += TEAM_TIP.format(tip=tip)
        else:
            stats_text += f"\n\n{NO_TEAM_REQUESTS}"

        # Отправляем статистику
        keyboard = get_profile_keyboard("team")
        await message.answer(stats_text, reply_markup=keyboard)

        # Если есть ожидающие запросы, показываем их с кнопками
        if received_requests:
            pending_requests = [req for req in received_requests if req.status == InvitationStatus.PENDING]
            for req in pending_requests[:3]:  # Показываем до 3 с кнопками
                from_user = await crud.get_user_by_id(session, req.from_user_id)
                from_name = from_user.name if from_user else "Пользователь"

                # Формируем информацию о соискателе
                skills = []
                if from_user and from_user.primary_skill:
                    skills.append(from_user.primary_skill)
                if from_user and from_user.additional_skills:
                    skills.append(from_user.additional_skills)
                skills_text = ", ".join(skills) if skills else "Не указаны"

                # Вычисляем время ожидания
                from datetime import datetime
                hours = int((datetime.utcnow() - req.created_at).total_seconds() / 3600)
                time_text = f"{hours} ч" if hours > 0 else "только что"

                req_text = f"<b>{from_name}</b>\n🛠 {skills_text}\n⏱ Ждет: {time_text}"
                keyboard = get_invitation_response_keyboard(req.id)
                await message.answer(req_text, reply_markup=keyboard)
