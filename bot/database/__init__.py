"""Модуль работы с базой данных"""
from database.models import User, Team, Invitation, UserType, InvitationStatus, TeamStatus
from database.db import create_tables, drop_tables, get_db
from database import crud  # ВАЖНО: импортируем crud модуль!

__all__ = [
    "User",
    "Team",
    "Invitation",
    "UserType",
    "InvitationStatus",
    "TeamStatus",
    "create_tables",
    "drop_tables",
    "get_db",
    "crud",  # Экспортируем crud
]
