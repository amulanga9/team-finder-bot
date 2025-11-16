"""Обработчики основных команд бота"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database.db import get_db
from bot.database import crud, Language
from bot.utils.i18n import get_text, get_language_keyboard

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help - показать помощь"""
    help_text = """📖 <b>Помощь по командам бота</b>

<b>Основные команды:</b>
/start - Регистрация и создание профиля
/profile - Показать ваш профиль и статистику
/search - Поиск teammates
/team - Статистика команды (только для лидеров)
/cancel - Отменить текущее действие
/help - Показать эту справку

<b>Как это работает:</b>

<b>Для команд (2+ человека):</b>
1. Зарегистрируйтесь как команда
2. Укажите название, идею и нужные навыки
3. Используйте /search для поиска соискателей
4. Отправляйте приглашения (до 5 в день)
5. Проверяйте /team для статистики

<b>Для соло-основателей:</b>
1. Зарегистрируйтесь с вашей идеей
2. Укажите навык и опишите проект
3. /search покажет других соло с совместимостью ⭐
4. Отправляйте запросы на коллаборацию

<b>Для соискателей:</b>
1. Зарегистрируйтесь с вашими навыками (1-3)
2. /search покажет команды (Tinder-style)
3. Свайпайте ✅ Интересно или ❌ Пропустить
4. Команды получат уведомление о вашей заявке

<b>Лимиты:</b>
• Команды: 5 приглашений/день
• Соло: 5 запросов/день
• Соискатели: без лимитов

<b>Нужна помощь?</b>
Напишите @support_bot или в чат Launch Lab"""

    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Команда /cancel - отменить текущее действие"""
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            "❌ Нечего отменять. Вы не в процессе регистрации.\n\n"
            "Используйте /start для начала или /help для помощи."
        )
        return

    await state.clear()
    await message.answer(
        "✅ Действие отменено. Вы можете начать заново:\n\n"
        "/start - Регистрация\n"
        "/search - Поиск teammates\n"
        "/profile - Ваш профиль"
    )


@router.message(Command("language"))
async def cmd_language(message: Message):
    """Команда /language - выбор языка интерфейса"""
    await message.answer(
        get_text("language_select", Language.RU),  # Показываем на всех языках
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    """Установить выбранный язык"""
    lang_code = callback.data.split("_")[1]  # ru, uz, en

    # Маппинг кодов на enum
    lang_map = {
        "ru": Language.RU,
        "uz": Language.UZ,
        "en": Language.EN,
    }

    new_lang = lang_map.get(lang_code, Language.RU)

    try:
        async with get_db() as session:
            user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

            if not user:
                await callback.answer(
                    "❌ Сначала зарегистрируйтесь через /start",
                    show_alert=True
                )
                return

            # Обновляем язык пользователя
            await crud.update_user_language(session, user.id, new_lang)

            # Показываем подтверждение на выбранном языке
            await callback.message.edit_text(
                get_text("language_changed", new_lang)
            )
            await callback.answer()

    except Exception as e:
        await callback.answer(
            get_text("error_try_again", Language.RU),
            show_alert=True
        )
