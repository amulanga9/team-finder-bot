"""
Services Layer - 187=5A-;>38:0 ?@8;>65=8O.

!>1;N405B ?@8=F8?K SOLID:
- Single Responsibility: :064K9 A5@28A >B25G05B 70 A2>N >1;0ABL
- Dependency Inversion: handlers 7028AOB >B services, 0 =5 >B crud =0?@O<CN
- Open/Closed: ;53:> @0AH8@O5BAO =>2K<8 A5@28A0<8

A?>;L7>20=85:
    from services import UserService, TeamService

    async with get_db() as session:
        user_service = UserService(session)
        user = await user_service.get_user_by_telegram_id(telegram_id)
"""
from .user_service import UserService
from .team_service import TeamService
from .invitation_service import InvitationService
from .search_service import SearchService

__all__ = [
    "UserService",
    "TeamService",
    "InvitationService",
    "SearchService",
]
