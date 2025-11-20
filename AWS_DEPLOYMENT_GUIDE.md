# 🚀 AWS EC2 DEPLOYMENT GUIDE - Team Finder Bot

**Полная инструкция по запуску телеграм-бота и админки на AWS EC2**

---

## 📋 СОДЕРЖАНИЕ

1. [Требования](#требования)
2. [Подготовка AWS EC2](#подготовка-aws-ec2)
3. [Установка на Ubuntu Server](#установка-на-ubuntu-server)
4. [Настройка переменных окружения](#настройка-переменных-окружения)
5. [Запуск сервисов](#запуск-сервисов)
6. [Проверка работоспособности](#проверка-работоспособности)
7. [Автозапуск через systemd](#автозапуск-через-systemd)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 ТРЕБОВАНИЯ

### AWS EC2 Instance
- **Тип**: t2.micro (или выше)
- **ОС**: Ubuntu 22.04 LTS
- **RAM**: минимум 1GB
- **Storage**: минимум 10GB
- **Security Group**: открыты порты 22 (SSH), 80/5000 (админка)

### Локальные требования
- Telegram Bot Token (от @BotFather)
- SSH ключ для подключения к EC2
- IP адрес вашего EC2 инстанса

---

## 🔧 ПОДГОТОВКА AWS EC2

### 1. Создание EC2 Instance

1. **Зайдите в AWS Console** → EC2 → Launch Instance

2. **Настройте параметры:**
   ```
   Name: team-finder-bot
   AMI: Ubuntu Server 22.04 LTS
   Instance type: t2.micro (Free Tier)
   Key pair: создайте новый или используйте существующий
   ```

3. **Настройте Security Group:**

   **Inbound Rules:**
   ```
   Port 22  (SSH)   - Ваш IP
   Port 80  (HTTP)  - 0.0.0.0/0 (или ваш IP)
   Port 5000 (Admin)- 0.0.0.0/0 (или ваш IP)
   Port 5432 (PostgreSQL) - только localhost (не открывать наружу!)
   ```

4. **Запустите инстанс** и дождитесь статуса "Running"

5. **Запомните Public IP адрес** (например: 54.123.45.67)

---

## 🖥 УСТАНОВКА НА UBUNTU SERVER

### 1. Подключение к серверу

```bash
# Сделайте ключ приватным
chmod 400 your-key.pem

# Подключитесь к серверу
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### 2. Обновление системы

```bash
# Обновите пакеты
sudo apt update && sudo apt upgrade -y

# Установите необходимые инструменты
sudo apt install -y python3-pip python3-venv git postgresql postgresql-contrib nginx
```

### 3. Настройка PostgreSQL

```bash
# Войдите в PostgreSQL
sudo -u postgres psql

# В psql выполните:
CREATE DATABASE teammates_bot;
CREATE USER botuser WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE teammates_bot TO botuser;
\q

# Проверьте подключение
psql -h localhost -U botuser -d teammates_bot
# Введите пароль
# Если успешно, выйдите: \q
```

### 4. Клонирование проекта

```bash
# Перейдите в домашнюю директорию
cd ~

# Создайте директорию для проекта
mkdir -p projects
cd projects

# Загрузите проект (используйте ваш метод):

# Вариант 1: Через Git (если репозиторий публичный)
git clone YOUR_REPO_URL team-finder-bot

# Вариант 2: Через SCP (с вашего локального компьютера)
# На вашем компьютере выполните:
# scp -i your-key.pem -r /path/to/project ubuntu@YOUR_EC2_IP:~/projects/team-finder-bot

# Перейдите в директорию проекта
cd team-finder-bot
```

### 5. Установка Python зависимостей

```bash
# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте его
source venv/bin/activate

# Обновите pip
pip install --upgrade pip

# Установите зависимости
pip install -r bot/requirements.txt

# Проверьте установку
python -c "import aiogram, flask; print('✅ Dependencies OK')"
```

---

## 🔐 НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ

### 1. Создание .env файла

```bash
# Скопируйте шаблон
cp .env.production .env

# Отредактируйте файл
nano .env
```

### 2. Заполните .env файл

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1. Telegram Bot Token (получите у @BotFather)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567

# 2. Database Password (который вы создали выше)
DB_PASSWORD=your_strong_password

# 3. Database настройки
DB_HOST=localhost
DB_PORT=5432
DB_NAME=teammates_bot
DB_USER=botuser

# 4. Admin Panel
ADMIN_PORT=5000

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ОПЦИОНАЛЬНЫЕ (можно оставить как есть)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEBUG=False
LOG_LEVEL=INFO
LOG_TO_FILE=True
LOG_FILE_PATH=logs/bot.log

RATE_LIMIT_DAILY_INVITATIONS=5
RATE_LIMIT_REQUESTS_PER_MINUTE=20

CLEANUP_EXPIRED_INVITATIONS_HOURS=72
CLEANUP_INACTIVE_USERS_DAYS=30
CLEANUP_INTERVAL_MINUTES=60
```

**Сохраните и закройте:** `Ctrl+X` → `Y` → `Enter`

### 3. Загрузка переменных

```bash
# Загрузите переменные в текущую сессию
export $(cat .env | xargs)

# Проверьте
echo $BOT_TOKEN  # Должен показать ваш токен
```

---

## 🚀 ЗАПУСК СЕРВИСОВ

### 1. Инициализация базы данных

```bash
# Активируйте виртуальное окружение (если ещё не активно)
source venv/bin/activate

# Запустите скрипт инициализации БД
cd bot
python -c "
import asyncio
from database.db import init_db, create_tables

async def init():
    await init_db()
    await create_tables()
    print('✅ Database initialized')

asyncio.run(init())
"
cd ..
```

### 2. Тестовый запуск

```bash
# Сначала протестируйте бота (5-10 секунд)
cd bot
python main.py &
BOT_PID=$!
sleep 5

# Проверьте логи
cat ../logs/bot.log

# Если всё ОК, остановите
kill $BOT_PID
cd ..

# Теперь протестируйте админку
cd admin
python app.py &
ADMIN_PID=$!
sleep 3

# Проверьте в браузере:
# http://YOUR_EC2_IP:5000

# Остановите
kill $ADMIN_PID
cd ..
```

### 3. Запуск через скрипт

```bash
# Загрузите переменные окружения
export $(cat .env | xargs)

# Запустите всё вместе
./start.sh

# Вы увидите:
# ✅ All services started successfully!
# 🤖 Telegram Bot:  PID 12345
# 🌐 Admin Panel:   PID 12346 (http://localhost:5000)
```

### 4. Проверка логов

```bash
# Логи бота (в реальном времени)
tail -f logs/bot.log

# Логи админки
tail -f logs/admin.log

# Оба лога одновременно
tail -f logs/*.log
```

---

## ✅ ПРОВЕРКА РАБОТОСПОСОБНОСТИ

### 1. Проверка Telegram Бота

**В Telegram:**
1. Найдите вашего бота по username (@your_bot_name)
2. Отправьте команду: `/start`
3. Бот должен ответить приветственным сообщением
4. Попробуйте зарегистрироваться

**Если бот не отвечает:**
```bash
# Проверьте, запущен ли процесс
ps aux | grep "python main.py"

# Проверьте логи на ошибки
tail -30 logs/bot.log

# Проверьте токен
echo $BOT_TOKEN
```

### 2. Проверка Админки

**В браузере:**
1. Откройте: `http://YOUR_EC2_IP:5000`
2. Вы должны увидеть админ-панель
3. Статистика должна загрузиться (может быть 0 если нет данных)

**Если админка не открывается:**
```bash
# Проверьте, запущена ли админка
ps aux | grep "python app.py"

# Проверьте логи
tail -30 logs/admin.log

# Проверьте порт
sudo netstat -tulpn | grep 5000

# Проверьте Security Group в AWS:
# Порт 5000 должен быть открыт!
```

### 3. Проверка базы данных

```bash
# Подключитесь к БД
psql -h localhost -U botuser -d teammates_bot

# Проверьте таблицы
\dt

# Вы должны увидеть: users, teams, invitations

# Проверьте количество пользователей
SELECT COUNT(*) FROM users;

# Выйдите
\q
```

---

## 🔄 АВТОЗАПУСК ЧЕРЕЗ SYSTEMD

Настройте автоматический запуск при перезагрузке сервера.

### 1. Создайте systemd сервис для бота

```bash
sudo nano /etc/systemd/system/teamfinder-bot.service
```

Содержимое:
```ini
[Unit]
Description=Team Finder Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/projects/team-finder-bot/bot
EnvironmentFile=/home/ubuntu/projects/team-finder-bot/.env
ExecStart=/home/ubuntu/projects/team-finder-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Создайте systemd сервис для админки

```bash
sudo nano /etc/systemd/system/teamfinder-admin.service
```

Содержимое:
```ini
[Unit]
Description=Team Finder Admin Panel
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/projects/team-finder-bot/admin
EnvironmentFile=/home/ubuntu/projects/team-finder-bot/.env
ExecStart=/home/ubuntu/projects/team-finder-bot/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Активируйте сервисы

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable teamfinder-bot
sudo systemctl enable teamfinder-admin

# Запустите сервисы
sudo systemctl start teamfinder-bot
sudo systemctl start teamfinder-admin

# Проверьте статус
sudo systemctl status teamfinder-bot
sudo systemctl status teamfinder-admin
```

### 4. Полезные команды

```bash
# Остановка
sudo systemctl stop teamfinder-bot
sudo systemctl stop teamfinder-admin

# Перезапуск
sudo systemctl restart teamfinder-bot
sudo systemctl restart teamfinder-admin

# Просмотр логов
sudo journalctl -u teamfinder-bot -f
sudo journalctl -u teamfinder-admin -f
```

---

## 🔧 TROUBLESHOOTING

### Проблема 1: Бот не запускается

**Симптомы:**
- Процесс умирает сразу после запуска
- В логах ошибка подключения к БД

**Решение:**
```bash
# 1. Проверьте переменные окружения
env | grep BOT_TOKEN
env | grep DB_

# 2. Проверьте подключение к БД вручную
psql -h localhost -U botuser -d teammates_bot

# 3. Проверьте формат DATABASE_URL
echo $DATABASE_URL

# 4. Перезапустите с явным указанием .env
export $(cat .env | xargs)
cd bot && python main.py
```

### Проблема 2: Админка не открывается

**Симптомы:**
- Браузер показывает "Connection refused"
- Не могу подключиться к http://EC2_IP:5000

**Решение:**
```bash
# 1. Проверьте Security Group в AWS
# Порт 5000 должен быть открыт для вашего IP!

# 2. Проверьте, запущена ли админка
ps aux | grep app.py

# 3. Проверьте, слушает ли порт
sudo netstat -tulpn | grep 5000

# 4. Попробуйте локально на сервере
curl http://localhost:5000

# 5. Проверьте firewall
sudo ufw status
sudo ufw allow 5000/tcp
```

### Проблема 3: База данных недоступна

**Симптомы:**
- Ошибки "connection refused" к PostgreSQL
- "FATAL: password authentication failed"

**Решение:**
```bash
# 1. Проверьте, запущен ли PostgreSQL
sudo systemctl status postgresql

# 2. Перезапустите PostgreSQL
sudo systemctl restart postgresql

# 3. Проверьте пароль
psql -h localhost -U botuser -d teammates_bot
# Введите пароль из .env

# 4. Пересоздайте пользователя
sudo -u postgres psql
DROP USER IF EXISTS botuser;
CREATE USER botuser WITH PASSWORD 'new_password';
GRANT ALL PRIVILEGES ON DATABASE teammates_bot TO botuser;
\q

# 5. Обновите .env с новым паролем
```

### Проблема 4: Permission denied

**Симптомы:**
- "Permission denied" при запуске скриптов
- Не могу создать файлы/директории

**Решение:**
```bash
# 1. Сделайте скрипты исполняемыми
chmod +x start.sh stop.sh

# 2. Проверьте владельца файлов
ls -la

# 3. Измените владельца (если нужно)
sudo chown -R ubuntu:ubuntu /home/ubuntu/projects/team-finder-bot

# 4. Создайте директорию для логов
mkdir -p logs
chmod 755 logs
```

---

## 📊 МОНИТОРИНГ И ПОДДЕРЖКА

### Проверка состояния сервисов

```bash
# Скрипт для быстрой проверки
cat > check_status.sh << 'EOF'
#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Team Finder Bot - Status Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка БД
echo "🗄️  PostgreSQL:"
sudo systemctl is-active postgresql && echo "   ✅ Running" || echo "   ❌ Stopped"

# Проверка бота
echo "🤖 Bot:"
pgrep -f "python main.py" > /dev/null && echo "   ✅ Running" || echo "   ❌ Stopped"

# Проверка админки
echo "🌐 Admin:"
pgrep -f "python app.py" > /dev/null && echo "   ✅ Running" || echo "   ❌ Stopped"

# Проверка портов
echo "🔌 Ports:"
sudo netstat -tulpn | grep -q ":5000" && echo "   ✅ 5000 (Admin)" || echo "   ❌ 5000 not open"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
EOF

chmod +x check_status.sh
./check_status.sh
```

### Регулярное резервное копирование

```bash
# Создайте скрипт бэкапа
cat > backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

echo "📦 Creating backup..."
pg_dump -U botuser -h localhost teammates_bot > "$BACKUP_DIR/backup_$DATE.sql"
echo "✅ Backup created: $BACKUP_DIR/backup_$DATE.sql"

# Удалить старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x backup_db.sh

# Добавьте в cron (ежедневный бэкап в 2:00 AM)
crontab -e
# Добавьте строку:
# 0 2 * * * /home/ubuntu/projects/team-finder-bot/backup_db.sh
```

---

## 🎉 ГОТОВО!

Ваш бот и админка теперь работают на AWS EC2!

**📱 Проверьте бота:** Найдите в Telegram и отправьте `/start`

**🌐 Проверьте админку:** Откройте `http://YOUR_EC2_IP:5000`

**📊 Мониторинг:** Используйте `./check_status.sh` для проверки

---

## 📞 КОНТАКТЫ И ПОДДЕРЖКА

Если возникли проблемы:
1. Проверьте раздел [Troubleshooting](#troubleshooting)
2. Просмотрите логи: `tail -f logs/*.log`
3. Проверьте статус: `./check_status.sh`

---

**Автор:** Claude (Anthropic)
**Дата:** 2025-11-20
**Версия:** 1.0.0
