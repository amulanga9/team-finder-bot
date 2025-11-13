# Инструкции по деплою Telegram Bot

Это руководство описывает как задеплоить бота на различных платформах.

## 📋 Содержание

- [VPS (Ubuntu/Debian)](#vps-ubuntudebian)
- [Docker](#docker)
- [Heroku](#heroku)
- [Railway](#railway)
- [Systemd Service](#systemd-service)

---

## VPS (Ubuntu/Debian)

### 1. Подключиться к серверу

```bash
ssh user@your-server-ip
```

### 2. Обновить систему

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Установить зависимости

```bash
# Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Git
sudo apt install git -y
```

### 4. Настроить PostgreSQL

```bash
sudo -u postgres psql

# В psql консоли:
CREATE DATABASE teammates_db;
CREATE USER teammates_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE teammates_db TO teammates_user;
\q
```

### 5. Клонировать репозиторий

```bash
cd /opt
sudo git clone https://github.com/yourusername/exams_21.git
cd exams_21
sudo chown -R $USER:$USER /opt/exams_21
```

### 6. Создать виртуальное окружение

```bash
cd bot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Настроить .env

```bash
cp .env.example .env
nano .env
```

Измените:
```env
BOT_TOKEN=your_real_bot_token
DATABASE_URL=postgresql+asyncpg://teammates_user:your_secure_password@localhost:5432/teammates_db
```

### 8. Запустить бота (тест)

```bash
python main.py
```

Если все работает, переходите к настройке systemd.

---

## Systemd Service

Создайте systemd service для автозапуска.

### 1. Создать service file

```bash
sudo nano /etc/systemd/system/teammates-bot.service
```

Содержимое:

```ini
[Unit]
Description=Teammates Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/exams_21/bot
Environment="PATH=/opt/exams_21/bot/venv/bin"
ExecStart=/opt/exams_21/bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Замените `your_username` на ваше имя пользователя.

### 2. Включить и запустить service

```bash
sudo systemctl daemon-reload
sudo systemctl enable teammates-bot
sudo systemctl start teammates-bot
```

### 3. Проверить статус

```bash
sudo systemctl status teammates-bot
```

### 4. Просмотр логов

```bash
sudo journalctl -u teammates-bot -f
```

---

## Docker

### 1. Создать Dockerfile

```dockerfile
# /opt/exams_21/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установить зависимости системы
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копировать requirements
COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать код
COPY bot/ .

# Запустить бота
CMD ["python", "main.py"]
```

### 2. Создать docker-compose.yml

```yaml
# /opt/exams_21/docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: teammates_db
      POSTGRES_USER: teammates_user
      POSTGRES_PASSWORD: your_secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U teammates_user -d teammates_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  bot:
    build: .
    environment:
      BOT_TOKEN: ${BOT_TOKEN}
      DATABASE_URL: postgresql+asyncpg://teammates_user:your_secure_password@db:5432/teammates_db
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

### 3. Создать .env

```bash
echo "BOT_TOKEN=your_real_bot_token" > .env
```

### 4. Запустить

```bash
docker-compose up -d
```

### 5. Просмотр логов

```bash
docker-compose logs -f bot
```

### 6. Остановить

```bash
docker-compose down
```

---

## Heroku

### 1. Установить Heroku CLI

```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

### 2. Создать Procfile

```
# /opt/exams_21/Procfile
worker: cd bot && python main.py
```

### 3. Создать runtime.txt

```
# /opt/exams_21/runtime.txt
python-3.11.0
```

### 4. Создать приложение

```bash
cd /opt/exams_21
heroku create your-teammates-bot
```

### 5. Добавить PostgreSQL

```bash
heroku addons:create heroku-postgresql:mini
```

### 6. Установить переменные окружения

```bash
heroku config:set BOT_TOKEN=your_real_bot_token
```

Database URL устанавливается автоматически при добавлении PostgreSQL.

### 7. Деплой

```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### 8. Проверить логи

```bash
heroku logs --tail
```

---

## Railway

### 1. Установить Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. Инициализировать проект

```bash
cd /opt/exams_21
railway init
```

### 3. Добавить PostgreSQL

В Railway Dashboard:
- New → Database → PostgreSQL

### 4. Установить переменные

В Railway Dashboard:
- Variables → Add Variable
- `BOT_TOKEN`: your_real_bot_token
- `DATABASE_URL`: автоматически добавлен PostgreSQL

### 5. Деплой

```bash
railway up
```

---

## Советы по безопасности

### 1. Используйте секреты для токенов

Никогда не коммитьте `.env` файл в git.

```bash
# Добавьте в .gitignore
echo ".env" >> .gitignore
```

### 2. Используйте сильные пароли для БД

Генерируйте случайные пароли:

```bash
openssl rand -base64 32
```

### 3. Обновляйте зависимости

```bash
pip list --outdated
pip install --upgrade package_name
```

### 4. Настройте firewall (для VPS)

```bash
sudo ufw allow ssh
sudo ufw allow 5432/tcp  # PostgreSQL (только если нужен внешний доступ)
sudo ufw enable
```

### 5. Регулярные бэкапы БД

```bash
# Создать бэкап
pg_dump -U teammates_user teammates_db > backup_$(date +%Y%m%d).sql

# Восстановить из бэкапа
psql -U teammates_user teammates_db < backup_20250101.sql
```

---

## Мониторинг

### Uptime Kuma (Self-hosted)

```bash
docker run -d --restart=always \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  --name uptime-kuma \
  louislam/uptime-kuma:1
```

### Prometheus + Grafana

Для production рекомендуется настроить:
- Prometheus для сбора метрик
- Grafana для визуализации
- Alertmanager для уведомлений

---

## Масштабирование

### Использовать Redis для кэша

Замените in-memory кэш в `handlers/search.py`:

```python
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost")
```

### Использовать очереди для задач

Celery + RabbitMQ для фоновых задач:
- Отправка уведомлений
- Очистка старых данных
- Генерация отчетов

### Load Balancing

Используйте nginx для балансировки нагрузки между несколькими инстансами бота.

---

## Troubleshooting

### Бот не запускается

```bash
# Проверить логи
sudo journalctl -u teammates-bot -n 50

# Проверить статус
sudo systemctl status teammates-bot
```

### Ошибка подключения к БД

```bash
# Проверить PostgreSQL
sudo systemctl status postgresql

# Проверить подключение
psql -U teammates_user -d teammates_db
```

### Out of Memory

Увеличьте swap на VPS:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

Удачи с деплоем! 🚀
