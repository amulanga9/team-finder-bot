"""
Система локализации (i18n) для бота

Поддерживаемые языки:
- ru: Русский
- uz: O'zbek (Узбекский)
- en: English
"""
from bot.database.models import Language


# Все переводы в одном месте
TRANSLATIONS = {
    # Основные команды
    "start_message": {
        Language.RU: "👋 Привет! Я помогу найти teammates для твоего проекта.\n\nВыбери свою роль:",
        Language.UZ: "👋 Salom! Men sizga loyihangiz uchun jamoadorlarni topishda yordam beraman.\n\nRolingizni tanlang:",
        Language.EN: "👋 Hello! I'll help you find teammates for your project.\n\nChoose your role:",
    },

    # Типы пользователей
    "type_team": {
        Language.RU: "🎯 У нас команда (2+ человека)",
        Language.UZ: "🎯 Bizda jamoa bor (2+ kishi)",
        Language.EN: "🎯 We have a team (2+ people)",
    },
    "type_cofounder": {
        Language.RU: "💡 У меня идея, ищу со-фаундера",
        Language.UZ: "💡 Menda g'oya bor, hamkor qidiraman",
        Language.EN: "💡 I have an idea, looking for a co-founder",
    },
    "type_participant": {
        Language.RU: "👤 Просто хочу помочь команде",
        Language.UZ: "👤 Faqat jamoaga yordam bermoqchiman",
        Language.EN: "👤 Just want to help a team",
    },

    # Кнопки
    "button_skip": {
        Language.RU: "⏭ Пропустить",
        Language.UZ: "⏭ O'tkazib yuborish",
        Language.EN: "⏭ Skip",
    },
    "button_done": {
        Language.RU: "✅ Готово",
        Language.UZ: "✅ Tayyor",
        Language.EN: "✅ Done",
    },
    "button_search": {
        Language.RU: "🔍 Начать поиск",
        Language.UZ: "🔍 Qidiruvni boshlash",
        Language.EN: "🔍 Start search",
    },
    "button_profile": {
        Language.RU: "👤 Профиль",
        Language.UZ: "👤 Profil",
        Language.EN: "👤 Profile",
    },
    "button_wait": {
        Language.RU: "⏰ Подожду",
        Language.UZ: "⏰ Kutaman",
        Language.EN: "⏰ I'll wait",
    },

    # Регистрация команды
    "team_name_request": {
        Language.RU: "Как называется ваша команда?",
        Language.UZ: "Jamoangiz nomi nima?",
        Language.EN: "What's your team name?",
    },
    "team_idea_request": {
        Language.RU: "Опишите вашу идею (1-2 предложения):",
        Language.UZ: "G'oyangizni tavsiflang (1-2 jumla):",
        Language.EN: "Describe your idea (1-2 sentences):",
    },
    "team_skills_request": {
        Language.RU: "Выберите нужные навыки (можно несколько):",
        Language.UZ: "Kerakli ko'nikmalarni tanlang (bir nechtasini tanlash mumkin):",
        Language.EN: "Select needed skills (multiple choice):",
    },
    "team_registration_complete": {
        Language.RU: "🎉 Отлично! Команда '{team_name}' зарегистрирована!\n\nТеперь можете начать поиск teammates.",
        Language.UZ: "🎉 Ajoyib! '{team_name}' jamoasi ro'yxatdan o'tdi!\n\nEndi jamoadorlarni qidirishingiz mumkin.",
        Language.EN: "🎉 Great! Team '{team_name}' is registered!\n\nNow you can start searching for teammates.",
    },

    # Регистрация со-фаундера
    "cofounder_name_request": {
        Language.RU: "Как тебя зовут?",
        Language.UZ: "Ismingiz nima?",
        Language.EN: "What's your name?",
    },
    "cofounder_skill_request": {
        Language.RU: "Выбери свой основной навык:",
        Language.UZ: "Asosiy ko'nikm

angizni tanlang:",
        Language.EN: "Choose your main skill:",
    },
    "cofounder_idea_what_request": {
        Language.RU: "Над чем хочешь работать? (1-2 предложения)\n\nНапример: 'AI-помощник для студентов'",
        Language.UZ: "Nima ustida ishlashni xohlaysiz? (1-2 jumla)\n\nMasalan: 'Talabalar uchun AI-yordamchi'",
        Language.EN: "What do you want to work on? (1-2 sentences)\n\nExample: 'AI assistant for students'",
    },
    "cofounder_idea_who_request": {
        Language.RU: "Для кого это будет? (целевая аудитория)\n\nНапример: 'Для студентов School 21'",
        Language.UZ: "Bu kim uchun? (maqsadli auditoriya)\n\nMasalan: 'School 21 talabalari uchun'",
        Language.EN: "Who is this for? (target audience)\n\nExample: 'For School 21 students'",
    },
    "cofounder_registration_complete": {
        Language.RU: "🎉 Отлично, {name}! Ты зарегистрирован как со-фаундер!",
        Language.UZ: "🎉 Ajoyib, {name}! Siz hamkor sifatida ro'yxatdan o'tdingiz!",
        Language.EN: "🎉 Great, {name}! You're registered as a co-founder!",
    },

    # Регистрация участника
    "seeker_name_request": {
        Language.RU: "Как тебя зовут?",
        Language.UZ: "Ismingiz nima?",
        Language.EN: "What's your name?",
    },
    "seeker_skills_request": {
        Language.RU: "Выбери свои навыки (1-3):",
        Language.UZ: "Ko'nikmalaringizni tanlang (1-3):",
        Language.EN: "Choose your skills (1-3):",
    },
    "seeker_registration_complete": {
        Language.RU: "🎉 Отлично, {name}! Ты зарегистрирован!",
        Language.UZ: "🎉 Ajoyib, {name}! Siz ro'yxatdan o'tdingiz!",
        Language.EN: "🎉 Great, {name}! You're registered!",
    },

    # Поиск
    "search_no_results": {
        Language.RU: "🤷‍♂️ Пока никого не нашли...\n\nПопробуйте позже или измените требуемые навыки.",
        Language.UZ: "🤷‍♂️ Hozircha hech kim topilmadi...\n\nKeyinroq urinib ko'ring yoki talab qilinadigan ko'nikmalarni o'zgartiring.",
        Language.EN: "🤷‍♂️ No one found yet...\n\nTry again later or change required skills.",
    },

    # Профиль
    "profile_participant": {
        Language.RU: "👤 <b>Твой профиль (Участник)</b>\n\n"
                      "Имя: {name}\n"
                      "💼 Навыки: {skills}\n"
                      "📅 В боте: {days} дн.\n"
                      "{status_line}",
        Language.UZ: "👤 <b>Sizning profilingiz (Ishtirokchi)</b>\n\n"
                      "Ism: {name}\n"
                      "💼 Ko'nikmalar: {skills}\n"
                      "📅 Botda: {days} kun\n"
                      "{status_line}",
        Language.EN: "👤 <b>Your profile (Participant)</b>\n\n"
                      "Name: {name}\n"
                      "💼 Skills: {skills}\n"
                      "📅 In bot: {days} days\n"
                      "{status_line}",
    },

    # Ошибки
    "already_registered": {
        Language.RU: "⚠️ Вы уже зарегистрированы!\n\nИспользуйте /profile для просмотра профиля или /search для поиска.",
        Language.UZ: "⚠️ Siz allaqachon ro'yxatdan o'tgansiz!\n\nProfilni ko'rish uchun /profile yoki qidirish uchun /search buyrug'idan foydalaning.",
        Language.EN: "⚠️ You're already registered!\n\nUse /profile to view your profile or /search to find teammates.",
    },
    "name_already_exists": {
        Language.RU: "⚠️ Имя '{name}' уже занято!\n\nВыберите другое имя.",
        Language.UZ: "⚠️ '{name}' ismi band!\n\nBoshqa ism tanlang.",
        Language.EN: "⚠️ Name '{name}' is already taken!\n\nChoose a different name.",
    },
    "error_try_again": {
        Language.RU: "❌ Произошла ошибка. Попробуйте еще раз.",
        Language.UZ: "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
        Language.EN: "❌ An error occurred. Please try again.",
    },

    # Команда /language
    "language_select": {
        Language.RU: "🌍 Выберите язык / Choose language / Tilni tanlang:",
        Language.UZ: "🌍 Tilni tanlang / Choose language / Выберите язык:",
        Language.EN: "🌍 Choose language / Выберите язык / Tilni tanlang:",
    },
    "language_changed": {
        Language.RU: "✅ Язык изменен на русский",
        Language.UZ: "✅ Til o'zbek tiliga o'zgartirildi",
        Language.EN: "✅ Language changed to English",
    },
}


def get_text(key: str, lang: Language = Language.RU, **kwargs) -> str:
    """
    Получить переведенный текст

    Args:
        key: Ключ перевода
        lang: Язык (по умолчанию русский)
        **kwargs: Параметры для форматирования строки

    Returns:
        Переведенный текст с подставленными параметрами
    """
    text = TRANSLATIONS.get(key, {}).get(lang)

    if text is None:
        # Fallback на русский если перевод не найден
        text = TRANSLATIONS.get(key, {}).get(Language.RU, f"[Missing: {key}]")

    # Форматируем строку с параметрами
    if kwargs:
        return text.format(**kwargs)

    return text


def get_language_keyboard():
    """Клавиатура выбора языка"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = [
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
