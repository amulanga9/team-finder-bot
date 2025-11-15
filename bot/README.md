# Telegram Bot для поиска teammates в стартап-акселераторе

Бот на Python (aiogram 3.x) для поиска teammates в стартап-акселераторе.

## Структура проекта

```
bot/
├── main.py                 # Точка входа в приложение
├── config.py               # Конфигурация бота
├── database/               # Работа с БД
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy модели
│   ├── crud.py            # CRUD операции
│   └── db.py              # Подключение к БД
├── handlers/               # Обработчики команд
│   ├── __init__.py
│   ├── start.py
│   ├── search.py
│   └── profile.py
├── keyboards/              # Клавиатуры бота
│   ├── __init__.py
│   ├── inline.py
│   └── reply.py
├── utils/                  # Вспомогательные функции
│   ├── __init__.py
│   ├── texts.py
│   └── helpers.py
├── .env.example            # Пример переменных окружения
├── requirements.txt        # Зависимости проекта
└── README.md              # Этот файл
```

## Технологии

- Python 3.10+
- aiogram 3.4.1 - фреймворк для Telegram Bot API
- SQLAlchemy 2.0.25 - ORM для работы с БД
- PostgreSQL - база данных
- asyncpg 0.29.0 - асинхронный драйвер PostgreSQL
- Alembic 1.13.1 - миграции БД

## Модели данных

### Users (Пользователи)
- `id` - ID пользователя
- `telegram_id` - ID в Telegram
- `username` - Username в Telegram
- `name` - Имя пользователя
- `user_type` - Тип: участник/команда
- `primary_skill` - Основной навык
- `additional_skills` - Дополнительные навыки
- `idea_what` - Что хочет создать
- `idea_who` - Кого ищет
- `last_active` - Последняя активность
- `created_at` - Дата регистрации

### Teams (Команды)
- `id` - ID команды
- `team_name` - Название команды
- `idea_description` - Описание идеи
- `leader_id` - ID лидера команды
- `needed_skills` - Нужные навыки
- `status` - Статус команды (active/inactive/complete)
- `created_at` - Дата создания

### Invitations (Приглашения)
- `id` - ID приглашения
- `from_user_id` - От кого
- `from_team_id` - От какой команды
- `to_user_id` - Кому
- `message` - Сообщение
- `status` - Статус (pending/accepted/rejected)
- `created_at` - Дата создания
- `viewed_at` - Дата просмотра
- `responded_at` - Дата ответа

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository_url>
cd bot
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните `.env` своими данными:

```env
BOT_TOKEN=ваш_токен_бота
DB_HOST=localhost
DB_PORT=5432
DB_NAME=teammates_bot
DB_USER=postgres
DB_PASSWORD=ваш_пароль
```

### 5. Настройка PostgreSQL

Создайте базу данных:

```bash
psql -U postgres
CREATE DATABASE teammates_bot;
\q
```

### 6. Запуск бота

```bash
python main.py
```

## Разработка

### Миграции БД (через Alembic)

Инициализация Alembic (выполняется один раз):

```bash
alembic init alembic
```

Создание миграции:

```bash
alembic revision --autogenerate -m "описание изменений"
```

Применение миграций:

```bash
alembic upgrade head
```

### Структура handlers (будет добавлено позже)

- `start.py` - обработка команды /start, регистрация
- `profile.py` - управление профилем пользователя
- `search.py` - поиск teammates и отправка приглашений

## TODO

- [ ] Реализовать handlers
- [ ] Создать клавиатуры
- [ ] Добавить тексты сообщений
- [ ] Реализовать систему поиска
- [ ] Добавить фильтры поиска
- [ ] Реализовать систему приглашений

## Лицензия

MIT
