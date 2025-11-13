"""Обработчики приглашений"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.db import async_session_maker
from database import crud
from database.models import InvitationStatus
from utils.texts import (
    INVITATION_RECEIVED, INVITATION_ACCEPTED, INVITATION_REJECTED,
    BUTTON_ACCEPT_INVITE, BUTTON_MEET, BUTTON_REJECT_INVITE
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("invitations"))
async def cmd_invitations(message: Message):
    """Команда /invitations - показать приглашения"""
    try:
        async with async_session_maker() as session:
            # Получаем пользователя
            user = await crud.get_user_by_telegram_id(session, message.from_user.id)

            if not user:
                await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
                return

            # Получаем приглашения
            invitations = await crud.get_received_invitations(
                session,
                user.id,
                status=InvitationStatus.PENDING
            )

            if not invitations:
                await message.answer("📭 У вас нет новых приглашений")
                return

            await message.answer(f"📬 У вас {len(invitations)} новых приглашений:")

            # Показываем каждое приглашение
            for invitation in invitations:
                await show_invitation(message, invitation)

    except Exception as e:
        logger.error(f"Ошибка при показе приглашений: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте еще раз.")


async def show_invitation(message: Message, invitation):
    """Показать приглашение"""
    try:
        async with async_session_maker() as session:
            # Получаем команду
            team = await crud.get_team_by_id(session, invitation.from_team_id) if invitation.from_team_id else None
            from_user = await crud.get_user_by_id(session, invitation.from_user_id)

            if not from_user:
                return

            # Формируем текст
            if team:
                text = INVITATION_RECEIVED.format(
                    team_name=team.team_name,
                    idea=team.idea_description or "Не указано",
                    needed_skills=team.needed_skills or "Не указано"
                )
            else:
                text = f"👤 {from_user.name} приглашает вас к сотрудничеству!"

            # Кнопки
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=BUTTON_ACCEPT_INVITE,
                        callback_data=f"accept_invite_{invitation.id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=BUTTON_REJECT_INVITE,
                        callback_data=f"reject_invite_{invitation.id}"
                    )
                ]
            ]

            await message.answer(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="HTML"
            )

            # Отмечаем как просмотренное
            await crud.mark_invitation_viewed(session, invitation.id)

    except Exception as e:
        logger.error(f"Ошибка при показе приглашения: {e}")


@router.callback_query(F.data.startswith("accept_invite_"))
async def accept_invitation(callback: CallbackQuery):
    """Принять приглашение"""
    invitation_id = int(callback.data.split("_")[2])

    try:
        async with async_session_maker() as session:
            invitation = await crud.get_invitation_by_id(session, invitation_id)

            if not invitation:
                await callback.answer("❌ Приглашение не найдено", show_alert=True)
                return

            # Обновляем статус
            await crud.update_invitation_status(session, invitation_id, InvitationStatus.ACCEPTED)

            # Получаем информацию о команде
            from_user = await crud.get_user_by_id(session, invitation.from_user_id)

            if from_user and from_user.username:
                text = INVITATION_ACCEPTED.format(leader_username=from_user.username)
            else:
                text = "✅ Отлично! Вы приняли приглашение."

            await callback.message.edit_text(text, parse_mode="HTML")
            await callback.answer("✅ Приглашение принято!")

            logger.info(f"Приглашение {invitation_id} принято")

    except Exception as e:
        logger.error(f"Ошибка при принятии приглашения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("reject_invite_"))
async def reject_invitation(callback: CallbackQuery):
    """Отклонить приглашение"""
    invitation_id = int(callback.data.split("_")[2])

    try:
        async with async_session_maker() as session:
            invitation = await crud.get_invitation_by_id(session, invitation_id)

            if not invitation:
                await callback.answer("❌ Приглашение не найдено", show_alert=True)
                return

            # Обновляем статус
            await crud.update_invitation_status(session, invitation_id, InvitationStatus.REJECTED)

            await callback.message.edit_text(INVITATION_REJECTED)
            await callback.answer("Приглашение отклонено")

            logger.info(f"Приглашение {invitation_id} отклонено")

    except Exception as e:
        logger.error(f"Ошибка при отклонении приглашения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)
