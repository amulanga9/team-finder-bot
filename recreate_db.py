#!/usr/bin/env python3
"""
Скрипт для пересоздания базы данных (удаляет все данные!)
Используйте только в разработке.

Usage:
    python recreate_db.py
"""
import asyncio
import sys
from pathlib import Path

# Добавляем bot в путь
sys.path.insert(0, str(Path(__file__).parent / "bot"))

from bot.config import settings
from bot.database.db import init_db, recreate_database, close_db


async def main():
    print("=" * 60)
    print("ВНИМАНИЕ: Это удалит ВСЕ данные из базы данных!")
    print("=" * 60)
    print(f"База данных: {settings.DB_NAME}")
    print(f"Хост: {settings.DB_HOST}:{settings.DB_PORT}")
    print("=" * 60)

    response = input("Вы уверены? (yes/no): ")
    if response.lower() != "yes":
        print("Отменено.")
        return

    print("\n🔄 Инициализация подключения к БД...")
    await init_db()

    print("🗑️  Удаление старых таблиц и enum типов...")
    print("✨ Создание новых таблиц...")
    await recreate_database()

    print("\n✅ База данных успешно пересоздана!")
    print("Теперь вы можете запустить бота: python -m bot.main")

    await close_db()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
