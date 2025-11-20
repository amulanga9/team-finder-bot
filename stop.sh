#!/bin/bash

###############################################################################
# СКРИПТ ОСТАНОВКИ TEAM FINDER BOT + ADMIN PANEL
#
# Останавливает все запущенные сервисы
# Использование: ./stop.sh
###############################################################################

echo "🛑 Stopping Team Finder Bot + Admin Panel..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Остановка бота
if [ -f "logs/bot.pid" ]; then
    BOT_PID=$(cat logs/bot.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "🤖 Stopping Telegram Bot (PID: $BOT_PID)..."
        kill $BOT_PID
        echo "   ✅ Bot stopped"
    else
        echo "   ℹ️  Bot not running"
    fi
    rm logs/bot.pid
else
    echo "   ℹ️  Bot PID file not found"
fi

# Остановка админки
if [ -f "logs/admin.pid" ]; then
    ADMIN_PID=$(cat logs/admin.pid)
    if ps -p $ADMIN_PID > /dev/null 2>&1; then
        echo "🌐 Stopping Admin Panel (PID: $ADMIN_PID)..."
        kill $ADMIN_PID
        echo "   ✅ Admin Panel stopped"
    else
        echo "   ℹ️  Admin Panel not running"
    fi
    rm logs/admin.pid
else
    echo "   ℹ️  Admin PID file not found"
fi

echo ""
echo "✅ All services stopped"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
