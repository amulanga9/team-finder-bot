"""
Константы приложения.

Централизованное хранение всех магических чисел и строк
для соблюдения принципа DRY и упрощения поддержки.
"""

# === Валидация ===
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50
MIN_TEAM_NAME_LENGTH = 3
MAX_TEAM_NAME_LENGTH = 50
MAX_DESCRIPTION_LENGTH = 200
MIN_SKILLS_COUNT = 1
MAX_SKILLS_COUNT_TEAM = 10  # Команда может искать много навыков
MAX_SKILLS_COUNT_PARTICIPANT = 3  # Соискатель выбирает 1-3 навыка
MAX_SKILLS_COUNT_COFOUNDER = 1  # Co-founder выбирает 1 основной навык

# === Лимиты ===
MAX_INVITATIONS_PER_DAY = 5
MAX_SEARCH_RESULTS = 10
MAX_PROFILE_INVITATIONS_DISPLAY = 5
MAX_TEAMS_DISPLAY = 5

# === UI/UX ===
# Emoji для статусов
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARNING = "⚠️"
EMOJI_INFO = "ℹ️"
EMOJI_THINKING = "🤔"
EMOJI_STAR = "⭐"
EMOJI_SEARCH = "🔍"
EMOJI_TEAM = "👥"
EMOJI_USER = "👤"
EMOJI_SKILL = "🛠"
EMOJI_IDEA = "💡"
EMOJI_CALENDAR = "📅"
EMOJI_CHART = "📊"
EMOJI_MAIL_SENT = "📬"
EMOJI_MAIL_RECEIVED = "📭"
EMOJI_FIRE = "🔥"
EMOJI_CLOCK = "⏰"
EMOJI_EYES = "👁"
EMOJI_HOURGLASS = "⏳"
EMOJI_GREEN_CIRCLE = "🟢"
EMOJI_YELLOW_CIRCLE = "🟡"
EMOJI_RED_CIRCLE = "🔴"

# === Времена (для readability) ===
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7

# === Префиксы для callback_data ===
CALLBACK_PREFIX_TYPE = "type_"
CALLBACK_PREFIX_SKILL = "skill_"
CALLBACK_PREFIX_SINGLE_SKILL = "single_skill_"
CALLBACK_PREFIX_LIMITED_SKILL = "limited_skill_"
CALLBACK_PREFIX_SEND_COLLAB = "send_collab_"
CALLBACK_PREFIX_NEXT_COFOUNDER = "next_cofounder_"
CALLBACK_PREFIX_INTERESTED_TEAM = "interested_team_"
CALLBACK_PREFIX_SKIP_TEAM = "skip_team_"
CALLBACK_PREFIX_ACCEPT_INVITE = "accept_invite_"
CALLBACK_PREFIX_REJECT_INVITE = "reject_invite_"

# === Ключи для состояний поиска (FSM data) ===
STATE_KEY_SEARCH_INDEX = "search_index"
STATE_KEY_SEARCH_RESULTS = "search_results"
STATE_KEY_SELECTED_SKILLS = "selected_skills"
STATE_KEY_TEAM_NAME = "team_name"
STATE_KEY_IDEA_DESCRIPTION = "idea_description"

# === Категории идей для алгоритма совместимости ===
IDEA_CATEGORIES = [
    "образование",
    "доставка",
    "финансы",
    "здоровье",
    "edtech",
    "fintech",
    "healthtech",
    "foodtech",
    "transport",
    "logistics",
    "ecommerce",
    "social",
    "entertainment",
    "productivity",
]

# === Минимальные оценки совместимости ===
MIN_COMPATIBILITY_STARS = 1
MAX_COMPATIBILITY_STARS = 5
BASE_COMPATIBILITY_STARS = 2
DIFFERENT_SKILLS_BONUS = 2  # +2 звезды за разные навыки
SAME_IDEA_BONUS = 1  # +1 звезда за похожие идеи
