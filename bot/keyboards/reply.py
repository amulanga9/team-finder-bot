"""Reply клавиатуры бота"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove


def get_remove_keyboard() -> ReplyKeyboardRemove:
    """Удалить клавиатуру"""
    return ReplyKeyboardRemove()


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню (для будущего использования)"""
    keyboard = [
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="📬 Приглашения"), KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
