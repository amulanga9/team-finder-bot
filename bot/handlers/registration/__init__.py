"""
Модуль регистрации пользователей.

Разделен на отдельные файлы по типам:
- team.py: регистрация команды
- cofounder.py: регистрация со-фаундера
- seeker.py: регистрация соискателя
"""
from .team import router as team_router
from .cofounder import router as cofounder_router
from .seeker import router as seeker_router

__all__ = ["team_router", "cofounder_router", "seeker_router"]
