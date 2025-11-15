"""Инлайн клавиатуры бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.texts import (
    SKILLS_DESCRIPTIONS, get_skill_button_text, BUTTON_DONE, BUTTON_SKIP,
    BUTTON_SEARCH_NOW, BUTTON_WAIT, BUTTON_EDIT_PROFILE, BUTTON_SEARCH_TEAMS,
    BUTTON_SEARCH, BUTTON_EDIT, BUTTON_ACCEPT_INVITE, BUTTON_REJECT_INVITE
)


def get_user_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа пользователя"""
    keyboard = [
        [InlineKeyboardButton(text="🎯 У нас команда (2+ человека)", callback_data="type_team")],
        [InlineKeyboardButton(text="💡 У меня идея, ищу со-фаундера", callback_data="type_cofounder")],
        [InlineKeyboardButton(text="👤 Просто хочу помочь команде", callback_data="type_participant")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой пропустить"""
    keyboard = [
        [InlineKeyboardButton(text=BUTTON_SKIP, callback_data="skip")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_skills_keyboard(selected_skills: list = None) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора навыков с множественным выбором

    Args:
        selected_skills: список уже выбранных навыков
    """
    if selected_skills is None:
        selected_skills = []

    keyboard = []

    # Добавляем кнопки навыков
    for skill_key in SKILLS_DESCRIPTIONS.keys():
        is_selected = skill_key in selected_skills
        button_text = get_skill_button_text(skill_key, is_selected)
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"skill_{skill_key}"
        )])

    # Добавляем кнопку "Готово"
    keyboard.append([InlineKeyboardButton(text=BUTTON_DONE, callback_data="skills_done")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_single_skill_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора одного навыка (для co-founder)
    """
    keyboard = []

    # Добавляем кнопки навыков
    for skill_key, skill_info in SKILLS_DESCRIPTIONS.items():
        skill_name = skill_info.get("name", skill_key)
        keyboard.append([InlineKeyboardButton(
            text=skill_name,
            callback_data=f"single_skill_{skill_key}"
        )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_limited_skills_keyboard(selected_skills: list = None, max_skills: int = 3) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора ограниченного количества навыков (для seeker)

    Args:
        selected_skills: список уже выбранных навыков
        max_skills: максимальное количество навыков (по умолчанию 3)
    """
    if selected_skills is None:
        selected_skills = []

    keyboard = []

    # Добавляем кнопки навыков
    for skill_key in SKILLS_DESCRIPTIONS.keys():
        is_selected = skill_key in selected_skills
        button_text = get_skill_button_text(skill_key, is_selected)
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"limited_skill_{skill_key}"
        )])

    # Показываем счетчик выбранных навыков
    done_text = f"{BUTTON_DONE} ({len(selected_skills)}/{max_skills})"
    keyboard.append([InlineKeyboardButton(text=done_text, callback_data="limited_skills_done")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_final_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с финальными действиями после регистрации"""
    keyboard = [
        [InlineKeyboardButton(text=BUTTON_SEARCH_NOW, callback_data="search_now")],
        [InlineKeyboardButton(text=BUTTON_WAIT, callback_data="wait")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# === КЛАВИАТУРЫ ДЛЯ ПРОФИЛЯ ===

def get_profile_keyboard(user_type: str = "participant") -> InlineKeyboardMarkup:
    """
    Клавиатура для профиля пользователя

    Args:
        user_type: тип пользователя (participant, cofounder, team)
    """
    if user_type == "participant":
        keyboard = [
            [InlineKeyboardButton(text=BUTTON_EDIT_PROFILE, callback_data="edit_profile")],
            [InlineKeyboardButton(text=BUTTON_SEARCH_TEAMS, callback_data="search_teams")]
        ]
    elif user_type == "cofounder":
        keyboard = [
            [InlineKeyboardButton(text=BUTTON_EDIT_PROFILE, callback_data="edit_profile")],
            [InlineKeyboardButton(text=BUTTON_SEARCH, callback_data="search_now")]
        ]
    else:  # team
        keyboard = [
            [InlineKeyboardButton(text=BUTTON_EDIT, callback_data="edit_profile")],
            [InlineKeyboardButton(text=BUTTON_SEARCH, callback_data="search_now")]
        ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_invitation_response_keyboard(invitation_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для ответа на приглашение в профиле

    Args:
        invitation_id: ID приглашения
    """
    keyboard = [
        [
            InlineKeyboardButton(text=BUTTON_ACCEPT_INVITE, callback_data=f"accept_invite_{invitation_id}"),
            InlineKeyboardButton(text=BUTTON_REJECT_INVITE, callback_data=f"reject_invite_{invitation_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# === КЛАВИАТУРЫ ДЛЯ TINDER-STYLE ПОИСКА ===

def get_cofounder_search_keyboard(user_id: int, current_index: int = 0) -> InlineKeyboardMarkup:
    """
    Клавиатура для поиска соло-основателей

    Args:
        user_id: ID найденного пользователя
        current_index: текущий индекс в списке найденных
    """
    keyboard = [
        [InlineKeyboardButton(text="💬 Отправить запрос", callback_data=f"send_collab_{user_id}_{current_index}")],
        [InlineKeyboardButton(text="👉 Следующий", callback_data=f"next_cofounder_{current_index}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_participant_team_keyboard(team_id: int, current_index: int = 0) -> InlineKeyboardMarkup:
    """
    Клавиатура для Tinder-style просмотра команд

    Args:
        team_id: ID команды
        current_index: текущий индекс в списке команд
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Интересно!", callback_data=f"interested_team_{team_id}_{current_index}"),
            InlineKeyboardButton(text="❌ Пропустить", callback_data=f"skip_team_{current_index}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_search_empty_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пустого результата поиска"""
    keyboard = [
        [InlineKeyboardButton(text="⏰ Подожду", callback_data="wait_notify")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
