"""Обработчики приглашений"""
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.db import async_session_maker
from database import crud
from database.models import InvitationStatus
from utils.texts import (
    INVITATION_RECEIVED,
    BUTTON_ACCEPT_INVITE, BUTTON_MEET, BUTTON_REJECT_INVITE,
    INVITATION_ACCEPTED_TO_TEAM, INVITATION_ACCEPTED_TO_USER,
    INVITATION_MEET_TO_TEAM, INVITATION_MEET_TO_USER,
    INVITATION_REJECTED_TO_TEAM, INVITATION_REJECTED_TO_USER,
    BUTTON_SEND_CHECKLIST, MEETING_CHECKLIST
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
                        text=BUTTON_MEET,
                        callback_data=f"meet_invite_{invitation.id}"
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
async def accept_invitation(callback: CallbackQuery, bot: Bot):
    """Принять приглашение"""
    invitation_id = int(callback.data.split("_")[2])

    try:
        async with async_session_maker() as session:
            invitation = await crud.get_invitation_by_id(session, invitation_id)

            if not invitation:
                await callback.answer("❌ Приглашение не найдено", show_alert=True)
                return

            # Получаем всю необходимую информацию
            from_user = await crud.get_user_by_id(session, invitation.from_user_id)
            to_user = await crud.get_user_by_id(session, invitation.to_user_id)
            team = await crud.get_team_by_id(session, invitation.from_team_id) if invitation.from_team_id else None

            if not from_user or not to_user:
                await callback.answer("❌ Ошибка получения данных", show_alert=True)
                return

            # Обновляем статус
            await crud.update_invitation_status(session, invitation_id, InvitationStatus.ACCEPTED)

            # Отправляем уведомление соискателю (текущий пользователь)
            if from_user.username:
                user_text = INVITATION_ACCEPTED_TO_USER.format(
                    team_name=team.team_name if team else from_user.name,
                    leader_username=from_user.username
                )
            else:
                user_text = f"✅ Ты принял приглашение!\n\nК сожалению, у лидера команды нет username в Telegram."

            await callback.message.edit_text(user_text, parse_mode="HTML")

            # Отправляем уведомление команде
            try:
                if to_user.username:
                    team_text = INVITATION_ACCEPTED_TO_TEAM.format(
                        name=to_user.name,
                        username=to_user.username
                    )
                else:
                    team_text = f"🎉 {to_user.name} принял приглашение!\n\nК сожалению, у него нет username в Telegram."

                # Добавляем кнопку для отправки чеклиста
                keyboard = [
                    [InlineKeyboardButton(
                        text=BUTTON_SEND_CHECKLIST,
                        callback_data=f"send_checklist_{to_user.telegram_id}"
                    )]
                ]

                await bot.send_message(
                    from_user.telegram_id,
                    team_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
                logger.info(f"Уведомление о принятии отправлено команде {from_user.telegram_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления команде: {e}")

            await callback.answer("✅ Приглашение принято!")
            logger.info(f"Приглашение {invitation_id} принято")

    except Exception as e:
        logger.error(f"Ошибка при принятии приглашения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("meet_invite_"))
async def meet_invitation(callback: CallbackQuery, bot: Bot):
    """Встретиться (то же что принять, но другой текст)"""
    invitation_id = int(callback.data.split("_")[2])

    try:
        async with async_session_maker() as session:
            invitation = await crud.get_invitation_by_id(session, invitation_id)

            if not invitation:
                await callback.answer("❌ Приглашение не найдено", show_alert=True)
                return

            # Получаем всю необходимую информацию
            from_user = await crud.get_user_by_id(session, invitation.from_user_id)
            to_user = await crud.get_user_by_id(session, invitation.to_user_id)
            team = await crud.get_team_by_id(session, invitation.from_team_id) if invitation.from_team_id else None

            if not from_user or not to_user:
                await callback.answer("❌ Ошибка получения данных", show_alert=True)
                return

            # Обновляем статус (тоже ACCEPTED)
            await crud.update_invitation_status(session, invitation_id, InvitationStatus.ACCEPTED)

            # Отправляем уведомление соискателю (текущий пользователь)
            if from_user.username:
                user_text = INVITATION_MEET_TO_USER.format(
                    team_name=team.team_name if team else from_user.name,
                    leader_username=from_user.username
                )
            else:
                user_text = f"📅 Отлично!\n\nК сожалению, у лидера команды нет username в Telegram."

            await callback.message.edit_text(user_text, parse_mode="HTML")

            # Отправляем уведомление команде
            try:
                if to_user.username:
                    team_text = INVITATION_MEET_TO_TEAM.format(
                        name=to_user.name,
                        username=to_user.username
                    )
                else:
                    team_text = f"📅 {to_user.name} хочет встретиться!\n\nК сожалению, у него нет username в Telegram."

                await bot.send_message(
                    from_user.telegram_id,
                    team_text
                )
                logger.info(f"Уведомление о встрече отправлено команде {from_user.telegram_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления команде: {e}")

            await callback.answer("📅 Договоритесь о встрече!")
            logger.info(f"Приглашение {invitation_id} принято (встреча)")

    except Exception as e:
        logger.error(f"Ошибка при принятии приглашения на встречу: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("reject_invite_"))
async def reject_invitation(callback: CallbackQuery, bot: Bot):
    """Отклонить приглашение"""
    invitation_id = int(callback.data.split("_")[2])

    try:
        async with async_session_maker() as session:
            invitation = await crud.get_invitation_by_id(session, invitation_id)

            if not invitation:
                await callback.answer("❌ Приглашение не найдено", show_alert=True)
                return

            # Получаем информацию о пользователях
            from_user = await crud.get_user_by_id(session, invitation.from_user_id)
            to_user = await crud.get_user_by_id(session, invitation.to_user_id)

            if not from_user or not to_user:
                await callback.answer("❌ Ошибка получения данных", show_alert=True)
                return

            # Обновляем статус
            await crud.update_invitation_status(session, invitation_id, InvitationStatus.REJECTED)

            # Отправляем уведомление соискателю (текущий пользователь)
            await callback.message.edit_text(INVITATION_REJECTED_TO_USER)

            # Отправляем уведомление команде
            try:
                team_text = INVITATION_REJECTED_TO_TEAM.format(name=to_user.name)
                await bot.send_message(
                    from_user.telegram_id,
                    team_text
                )
                logger.info(f"Уведомление об отклонении отправлено команде {from_user.telegram_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления команде: {e}")

            await callback.answer("Приглашение отклонено")
            logger.info(f"Приглашение {invitation_id} отклонено")

    except Exception as e:
        logger.error(f"Ошибка при отклонении приглашения: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("send_checklist_"))
async def send_checklist(callback: CallbackQuery, bot: Bot):
    """Отправить чеклист соискателю"""
    user_telegram_id = int(callback.data.split("_")[2])

    try:
        # Отправляем чеклист соискателю
        await bot.send_message(
            user_telegram_id,
            MEETING_CHECKLIST,
            parse_mode="HTML"
        )

        await callback.answer("✅ Чеклист отправлен!")
        await callback.message.answer("✅ Чеклист отправлен соискателю")

        logger.info(f"Чеклист отправлен пользователю {user_telegram_id}")

    except Exception as e:
        logger.error(f"Ошибка при отправке чеклиста: {e}")
        await callback.answer("❌ Ошибка отправки чеклиста", show_alert=True)
