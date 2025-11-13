from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Team, Invitation, UserType, InvitationStatus, TeamStatus
from typing import Optional, List
from datetime import datetime


# ===== USER CRUD =====

async def create_user(
    session: AsyncSession,
    telegram_id: int,
    name: str,
    user_type: UserType,
    username: Optional[str] = None,
    primary_skill: Optional[str] = None,
    additional_skills: Optional[str] = None,
    idea_what: Optional[str] = None,
    idea_who: Optional[str] = None,
) -> User:
    """Создать нового пользователя"""
    user = User(
        telegram_id=telegram_id,
        username=username,
        name=name,
        user_type=user_type,
        primary_skill=primary_skill,
        additional_skills=additional_skills,
        idea_what=idea_what,
        idea_who=idea_who,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Получить пользователя по telegram_id"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def update_user_last_active(session: AsyncSession, user_id: int) -> None:
    """Обновить время последней активности пользователя"""
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_active=datetime.utcnow())
    )
    await session.commit()


async def count_users(session: AsyncSession) -> int:
    """Подсчитать общее количество пользователей"""
    result = await session.execute(
        select(func.count()).select_from(User)
    )
    return result.scalar()


# ===== TEAM CRUD =====

async def create_team(
    session: AsyncSession,
    team_name: str,
    leader_id: int,
    idea_description: Optional[str] = None,
    needed_skills: Optional[str] = None,
) -> Team:
    """Создать новую команду"""
    team = Team(
        team_name=team_name,
        leader_id=leader_id,
        idea_description=idea_description,
        needed_skills=needed_skills,
    )
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


async def get_team_by_id(session: AsyncSession, team_id: int) -> Optional[Team]:
    """Получить команду по ID"""
    result = await session.execute(
        select(Team).where(Team.id == team_id)
    )
    return result.scalar_one_or_none()


async def get_teams_by_leader(session: AsyncSession, leader_id: int) -> List[Team]:
    """Получить все команды пользователя"""
    result = await session.execute(
        select(Team).where(Team.leader_id == leader_id)
    )
    return list(result.scalars().all())


async def update_team_status(
    session: AsyncSession,
    team_id: int,
    status: TeamStatus
) -> None:
    """Обновить статус команды"""
    await session.execute(
        update(Team)
        .where(Team.id == team_id)
        .values(status=status)
    )
    await session.commit()


# ===== INVITATION CRUD =====

async def create_invitation(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    from_team_id: Optional[int] = None,
    message: Optional[str] = None,
) -> Invitation:
    """Создать новое приглашение"""
    invitation = Invitation(
        from_user_id=from_user_id,
        from_team_id=from_team_id,
        to_user_id=to_user_id,
        message=message,
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)
    return invitation


async def get_invitation_by_id(session: AsyncSession, invitation_id: int) -> Optional[Invitation]:
    """Получить приглашение по ID"""
    result = await session.execute(
        select(Invitation).where(Invitation.id == invitation_id)
    )
    return result.scalar_one_or_none()


async def get_received_invitations(
    session: AsyncSession,
    user_id: int,
    status: Optional[InvitationStatus] = None
) -> List[Invitation]:
    """Получить полученные приглашения пользователя"""
    query = select(Invitation).where(Invitation.to_user_id == user_id)
    if status:
        query = query.where(Invitation.status == status)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_sent_invitations(
    session: AsyncSession,
    user_id: int,
    status: Optional[InvitationStatus] = None
) -> List[Invitation]:
    """Получить отправленные приглашения пользователя"""
    query = select(Invitation).where(Invitation.from_user_id == user_id)
    if status:
        query = query.where(Invitation.status == status)
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_invitation_status(
    session: AsyncSession,
    invitation_id: int,
    status: InvitationStatus
) -> None:
    """Обновить статус приглашения"""
    await session.execute(
        update(Invitation)
        .where(Invitation.id == invitation_id)
        .values(
            status=status,
            responded_at=datetime.utcnow()
        )
    )
    await session.commit()


async def mark_invitation_viewed(
    session: AsyncSession,
    invitation_id: int
) -> None:
    """Отметить приглашение как просмотренное"""
    await session.execute(
        update(Invitation)
        .where(Invitation.id == invitation_id)
        .values(viewed_at=datetime.utcnow())
    )
    await session.commit()
