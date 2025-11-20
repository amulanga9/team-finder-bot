# 📁 PROJECT STRUCTURE

Полная структура проекта Team Finder Bot

---

## 📂 Структура директорий

```
team-finder-bot/
│
├── 📁 bot/                          # Telegram Bot
│   ├── 📁 common/                   # Общие компоненты
│   │   ├── __init__.py
│   │   ├── constants.py             # Константы (лимиты, emoji и т.д.)
│   │   ├── exceptions.py            # Custom исключения
│   │   └── validators.py            # Валидаторы данных
│   │
│   ├── 📁 database/                 # Работа с БД
│   │   ├── __init__.py
│   │   ├── db.py                    # Подключение к БД
│   │   ├── models.py                # SQLAlchemy модели
│   │   └── crud.py                  # CRUD операции
│   │
│   ├── 📁 handlers/                 # Обработчики команд
│   │   ├── __init__.py
│   │   ├── start.py                 # Регистрация пользователей
│   │   ├── search.py                # Поиск teammates
│   │   ├── invitations.py           # Обработка приглашений
│   │   ├── profile.py               # Профиль пользователя
│   │   ├── team.py                  # Статистика команды
│   │   └── commands.py              # /help, /cancel
│   │
│   ├── 📁 services/                 # Бизнес-логика (Services Layer)
│   │   ├── __init__.py
│   │   ├── user_service.py          # Управление пользователями
│   │   ├── team_service.py          # Управление командами
│   │   ├── invitation_service.py    # Логика приглашений
│   │   └── search_service.py        # Алгоритмы поиска
│   │
│   ├── 📁 keyboards/                # Клавиатуры бота
│   │   ├── __init__.py
│   │   ├── inline.py                # Inline клавиатуры
│   │   └── reply.py                 # Reply клавиатуры
│   │
│   ├── 📁 middlewares/              # Middleware компоненты
│   │   ├── __init__.py
│   │   └── throttling.py            # Rate limiting
│   │
│   ├── 📁 utils/                    # Утилиты
│   │   ├── __init__.py
│   │   ├── texts.py                 # Тексты сообщений
│   │   └── states.py                # FSM состояния
│   │
│   ├── 📁 schemas/                  # Pydantic схемы (пусто, для будущего)
│   │   └── __init__.py
│   │
│   ├── config.py                    # Конфигурация (Pydantic Settings)
│   ├── tasks.py                     # Background tasks (cleanup)
│   ├── main.py                      # 🚀 Точка входа бота
│   ├── requirements.txt             # Python зависимости
│   ├── .env.example                 # Пример переменных окружения
│   └── README.md                    # Документация бота
│
├── 📁 admin/                        # 🌐 Admin Panel (Flask)
│   ├── 📁 templates/
│   │   └── index.html               # Главная страница админки
│   ├── 📁 static/
│   │   ├── 📁 css/
│   │   └── 📁 js/
│   └── app.py                       # Flask приложение
│
├── 📁 tests/                        # Unit и Integration тесты
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── 📁 unit/
│   │   ├── __init__.py
│   │   ├── test_validators.py      # Тесты валидаторов
│   │   └── test_services.py        # Тесты сервисов
│   ├── 📁 integration/
│   │   └── __init__.py
│   └── 📁 fixtures/
│       └── __init__.py
│
├── 📁 .github/                      # CI/CD
│   └── 📁 workflows/
│       ├── ci.yml                   # Continuous Integration
│       └── cd.yml                   # Continuous Deployment
│
├── 📁 logs/                         # Логи (создаётся автоматически)
│   ├── bot.log                      # Логи бота
│   ├── admin.log                    # Логи админки
│   ├── bot.pid                      # PID бота
│   └── admin.pid                    # PID админки
│
├── 📄 start.sh                      # 🚀 Скрипт запуска
├── 📄 stop.sh                       # 🛑 Скрипт остановки
├── 📄 .env                          # Переменные окружения (не в git)
├── 📄 .env.production               # Шаблон для production
├── 📄 docker-compose.yml            # Docker Compose конфигурация
├── 📄 Dockerfile                    # Docker образ
├── 📄 pyproject.toml                # Python конфигурация (black, pytest и т.д.)
├── 📄 .pre-commit-config.yaml       # Pre-commit hooks
├── 📄 recreate_db.py                # Скрипт пересоздания БД
│
├── 📄 README.md                     # Главный README
├── 📄 AWS_DEPLOYMENT_GUIDE.md       # 📚 Подробная инструкция для AWS
├── 📄 QUICK_START_CHECKLIST.md      # ✅ Быстрый чек-лист
├── 📄 PROJECT_STRUCTURE.md          # 📁 Этот файл
├── 📄 REFACTORING_REPORT.md         # Отчёт о рефакторинге
├── 📄 DEPLOYMENT.md                 # Общие инструкции по деплою
├── 📄 PRODUCTION.md                 # Production готовность
└── 📄 PROMPTS.md                    # История промптов
```

---

## 📝 ОПИСАНИЕ ОСНОВНЫХ ФАЙЛОВ

### 🤖 Бот

| Файл | Описание |
|------|----------|
| `bot/main.py` | Точка входа, инициализация бота, graceful shutdown |
| `bot/config.py` | Конфигурация через Pydantic Settings |
| `bot/tasks.py` | Background задачи (очистка БД) |

### 🗄️ База данных

| Файл | Описание |
|------|----------|
| `bot/database/models.py` | SQLAlchemy модели (User, Team, Invitation) |
| `bot/database/db.py` | Подключение к БД, context managers |
| `bot/database/crud.py` | CRUD операции с N+1 оптимизацией |

### 🎯 Бизнес-логика

| Файл | Описание |
|------|----------|
| `bot/services/user_service.py` | Управление пользователями |
| `bot/services/team_service.py` | Управление командами |
| `bot/services/invitation_service.py` | Логика приглашений с валидацией |
| `bot/services/search_service.py` | Алгоритмы поиска и совместимости |

### 🌐 Админка

| Файл | Описание |
|------|----------|
| `admin/app.py` | Flask приложение, REST API |
| `admin/templates/index.html` | Веб-интерфейс админки |

### 🔧 Инфраструктура

| Файл | Описание |
|------|----------|
| `start.sh` | Запуск бота и админки |
| `stop.sh` | Остановка всех сервисов |
| `.env` | Переменные окружения (не в git!) |
| `docker-compose.yml` | Docker Compose для локального запуска |

---

## 🔑 КЛЮЧЕВЫЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

Обязательные переменные в `.env`:

```bash
# Telegram
BOT_TOKEN=your_bot_token_here

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=teammates_bot
DB_USER=postgres
DB_PASSWORD=your_password_here

# Admin Panel
ADMIN_PORT=5000

# Application
DEBUG=False
LOG_LEVEL=INFO
```

---

## 📊 РАЗМЕР ПРОЕКТА

```
Всего файлов: 60+
Строк кода: ~5000+
Services: 4
Handlers: 6
Tests: 30+
```

---

## 🚀 ОСНОВНЫЕ КОМАНДЫ

```bash
# Запуск
./start.sh

# Остановка
./stop.sh

# Логи
tail -f logs/bot.log
tail -f logs/admin.log

# Тесты
pytest tests/

# Форматирование кода
black bot/ admin/

# Линтинг
flake8 bot/ admin/
```

---

## 📚 ДОКУМЕНТАЦИЯ

- `README.md` - Обзор проекта
- `AWS_DEPLOYMENT_GUIDE.md` - Детальная инструкция для AWS
- `QUICK_START_CHECKLIST.md` - Быстрый старт
- `REFACTORING_REPORT.md` - Отчёт о качестве кода
- `DEPLOYMENT.md` - Общие инструкции по деплою
- `PRODUCTION.md` - Production готовность

---

## 🎯 АРХИТЕКТУРА

```
┌─────────────┐
│   Telegram  │
│    Users    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│             │     │    Admin    │
│     Bot     │◄────┤    Panel    │
│  (aiogram)  │     │   (Flask)   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       │                   │
       ▼                   ▼
┌─────────────────────────────┐
│        Services Layer       │
│  (Business Logic - SOLID)   │
└──────────────┬──────────────┘
               │
               ▼
        ┌──────────────┐
        │     CRUD     │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │  PostgreSQL  │
        │   Database   │
        └──────────────┘
```

---

## 🛡️ SECURITY

- ✅ Переменные окружения (не в git)
- ✅ Rate limiting (защита от спама)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Input validation (Pydantic, custom validators)
- ✅ Background cleanup (expired data)

---

## 🎉 ГОТОВО К PRODUCTION

- ✅ SOLID принципы применены
- ✅ DRY - нет дублирования
- ✅ Type hints 70%+
- ✅ Unit тесты готовы
- ✅ CI/CD настроен
- ✅ Graceful shutdown
- ✅ Docker ready
- ✅ AWS ready

---

**Версия:** 1.0.0
**Дата:** 2025-11-20
**Статус:** Production-Ready ✅
