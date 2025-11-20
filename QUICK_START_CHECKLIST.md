# ✅ QUICK START CHECKLIST - AWS EC2 Deployment

Быстрый чек-лист для запуска проекта на AWS EC2

---

## 📋 ПЕРЕД НАЧАЛОМ

- [ ] AWS аккаунт создан
- [ ] EC2 instance запущен (Ubuntu 22.04)
- [ ] SSH ключ скачан
- [ ] Security Group настроен (порты 22, 80, 5000 открыты)
- [ ] Telegram Bot Token получен от @BotFather
- [ ] Записан Public IP адрес EC2

---

## 🚀 УСТАНОВКА (5-10 минут)

### 1. Подключение к серверу

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### 2. Установка зависимостей

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git postgresql postgresql-contrib
```

### 3. Настройка PostgreSQL

```bash
sudo -u postgres psql
```

В psql выполните:
```sql
CREATE DATABASE teammates_bot;
CREATE USER botuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE teammates_bot TO botuser;
\q
```

### 4. Загрузка проекта

```bash
cd ~
mkdir -p projects && cd projects

# Загрузите проект (через git или scp)
# scp -i key.pem -r /local/path ubuntu@IP:~/projects/team-finder-bot

cd team-finder-bot
```

### 5. Установка Python зависимостей

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r bot/requirements.txt
```

---

## 🔐 НАСТРОЙКА ПЕРЕМЕННЫХ

### 6. Создание .env файла

```bash
cp .env.production .env
nano .env
```

**ОБЯЗАТЕЛЬНО заполните:**
```bash
BOT_TOKEN=your_telegram_bot_token_here
DB_PASSWORD=your_database_password
DB_USER=botuser
DB_HOST=localhost
ADMIN_PORT=5000
```

Сохраните: `Ctrl+X` → `Y` → `Enter`

### 7. Загрузка переменных

```bash
export $(cat .env | xargs)
```

---

## 🚀 ЗАПУСК

### 8. Инициализация БД

```bash
source venv/bin/activate
cd bot
python -c "
import asyncio
from database.db import init_db, create_tables
asyncio.run(init_db())
asyncio.run(create_tables())
"
cd ..
```

### 9. Запуск сервисов

```bash
./start.sh
```

Вы увидите:
```
✅ All services started successfully!
🤖 Telegram Bot:  PID 12345
🌐 Admin Panel:   PID 12346 (http://localhost:5000)
```

---

## ✅ ПРОВЕРКА

### 10. Проверка Telegram бота

1. Найдите бота в Telegram: `@your_bot_name`
2. Отправьте: `/start`
3. Бот должен ответить

### 11. Проверка админки

Откройте в браузере: `http://YOUR_EC2_IP:5000`

---

## 🔄 АВТОЗАПУСК (опционально)

### 12. Настройка systemd

```bash
# Создайте сервисы
sudo nano /etc/systemd/system/teamfinder-bot.service
sudo nano /etc/systemd/system/teamfinder-admin.service

# Активируйте
sudo systemctl daemon-reload
sudo systemctl enable teamfinder-bot teamfinder-admin
sudo systemctl start teamfinder-bot teamfinder-admin

# Проверьте статус
sudo systemctl status teamfinder-bot
sudo systemctl status teamfinder-admin
```

---

## 📊 КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ

```bash
# Запуск
./start.sh

# Остановка
./stop.sh

# Логи бота
tail -f logs/bot.log

# Логи админки
tail -f logs/admin.log

# Статус сервисов
ps aux | grep python

# Проверка портов
sudo netstat -tulpn | grep 5000
```

---

## 🐛 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### Бот не отвечает?
```bash
# Проверьте логи
tail -30 logs/bot.log

# Проверьте токен
echo $BOT_TOKEN

# Перезапустите
./stop.sh && ./start.sh
```

### Админка не открывается?
```bash
# Проверьте Security Group в AWS
# Порт 5000 должен быть открыт!

# Проверьте процесс
ps aux | grep app.py

# Проверьте порт
sudo netstat -tulpn | grep 5000
```

### БД не подключается?
```bash
# Проверьте PostgreSQL
sudo systemctl status postgresql

# Проверьте подключение
psql -h localhost -U botuser -d teammates_bot

# Перезапустите PostgreSQL
sudo systemctl restart postgresql
```

---

## 📚 ПОЛНАЯ ДОКУМЕНТАЦИЯ

Подробные инструкции: `AWS_DEPLOYMENT_GUIDE.md`

---

## 🎉 ГОТОВО!

- ✅ Бот работает в Telegram
- ✅ Админка доступна по http://YOUR_EC2_IP:5000
- ✅ База данных настроена
- ✅ Логи записываются

**Время установки:** 10-15 минут
**Сложность:** Средняя

---

**Если возникли проблемы - смотрите AWS_DEPLOYMENT_GUIDE.md**
