#!/bin/bash

###############################################################################
# СКРИПТ ЗАПУСКА TEAM FINDER BOT + ADMIN PANEL
#
# Запускает бот и админку одновременно в фоновом режиме
# Использование: ./start.sh
###############################################################################

set -e  # Останавливаться при ошибках

echo "🚀 Starting Team Finder Bot + Admin Panel..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка переменных окружения
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ ERROR: BOT_TOKEN not set!"
    echo "Please set BOT_TOKEN environment variable or add it to .env file"
    exit 1
fi

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ ERROR: DB_PASSWORD not set!"
    echo "Please set DB_PASSWORD environment variable or add it to .env file"
    exit 1
fi

echo "✅ Environment variables loaded"

# Активация виртуального окружения (если есть)
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Установка зависимостей (если нужно)
echo "📦 Checking dependencies..."
pip install -q -r bot/requirements.txt

# Создание директории для логов
mkdir -p logs

# Запуск бота в фоновом режиме
echo "🤖 Starting Telegram Bot..."
cd bot
python main.py > ../logs/bot.log 2>&1 &
BOT_PID=$!
echo "   ✅ Bot started (PID: $BOT_PID)"
cd ..

# Небольшая пауза
sleep 2

# Запуск админки в фоновом режиме
echo "🌐 Starting Admin Panel..."
cd admin
python app.py > ../logs/admin.log 2>&1 &
ADMIN_PID=$!
echo "   ✅ Admin Panel started (PID: $ADMIN_PID)"
cd ..

# Сохраняем PID в файлы для остановки
echo $BOT_PID > logs/bot.pid
echo $ADMIN_PID > logs/admin.pid

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All services started successfully!"
echo ""
echo "📊 Services:"
echo "   🤖 Telegram Bot:  PID $BOT_PID"
echo "   🌐 Admin Panel:   PID $ADMIN_PID (http://localhost:5000)"
echo ""
echo "📝 Logs:"
echo "   Bot:    tail -f logs/bot.log"
echo "   Admin:  tail -f logs/admin.log"
echo ""
echo "🛑 To stop: ./stop.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
