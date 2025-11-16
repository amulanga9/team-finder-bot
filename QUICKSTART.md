# 🚀 Быстрый старт

## Проблема с PostgreSQL Enum

Если вы получили ошибку:
```
invalid input value for enum usertype: "participant"
```

Это значит, что в базе данных есть старый enum тип. Следуйте инструкциям ниже.

## Шаг 1: Запустите PostgreSQL

### Ubuntu/Debian:
```bash
sudo service postgresql start
# или
sudo systemctl start postgresql
```

### macOS:
```bash
brew services start postgresql
# или
pg_ctl -D /usr/local/var/postgres start
```

### Docker:
```bash
docker run --name postgres -e POSTGRES_PASSWORD=your_password -p 5432:5432 -d postgres:15
```

## Шаг 2: Создайте базу данных (если её нет)

```bash
# Войдите в PostgreSQL
sudo -u postgres psql

# Создайте базу данных
CREATE DATABASE teammates_bot;

# Создайте пользователя (опционально)
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE teammates_bot TO your_user;

# Выйдите
\q
```

## Шаг 3: Настройте .env файл

Откройте `.env` и замените placeholder значения:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz  # Ваш токен от @BotFather
DB_PASSWORD=your_password_here                      # Ваш пароль PostgreSQL
```

## Шаг 4: Пересоздайте базу данных

```bash
cd /home/user/team-finder-bot
source venv/bin/activate
python recreate_db.py
```

Скрипт спросит подтверждение. Введите `yes` для продолжения.

## Шаг 5: Запустите бота

```bash
python -m bot.main
```

Если всё работает, вы увидите:
```
✅ Бот успешно запущен и готов к работе
```

## Устранение проблем

### PostgreSQL не запускается
```bash
# Проверьте статус
sudo service postgresql status

# Посмотрите логи
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Ошибка подключения к базе данных
1. Проверьте что PostgreSQL запущен
2. Проверьте настройки в `.env`:
   - `DB_HOST=localhost`
   - `DB_PORT=5432`
   - `DB_NAME=teammates_bot`
   - `DB_PASSWORD=ваш_пароль`

### Ошибка "Database not initialized"
Убедитесь, что вы запускаете бота из правильной директории:
```bash
cd /home/user/team-finder-bot
python -m bot.main
```

## Полезные команды

```bash
# Проверить статус PostgreSQL
sudo service postgresql status

# Войти в psql
sudo -u postgres psql

# Посмотреть все базы данных
\l

# Подключиться к базе
\c teammates_bot

# Посмотреть таблицы
\dt

# Посмотреть enum типы
\dT+
```
