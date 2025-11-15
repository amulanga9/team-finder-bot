from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Team, Invitation, UserType, InvitationStatus, TeamStatus
from typing import Optional, List
from datetime import datetime, timedelta


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


# ===== SEARCH FUNCTIONS =====

async def find_users_by_skills(
    session: AsyncSession,
    needed_skills: str,
    exclude_user_id: Optional[int] = None
) -> List[User]:
    """
    Найти пользователей по навыкам
    
    Args:
        session: сессия БД
        needed_skills: строка с нужными навыками (например: "Mobile (Flutter), Design (Figma)")
        exclude_user_id: ID пользователя, которого нужно исключить из поиска
    
    Returns:
        Список пользователей, отсортированный по активности
    """
    # Разбираем навыки
    skills_list = [skill.strip() for skill in needed_skills.split(',')]
    
    # Строим запрос для поиска пользователей с нужными навыками
    query = select(User).where(User.user_type == UserType.PARTICIPANT)
    
    if exclude_user_id:
        query = query.where(User.id != exclude_user_id)
    
    # Ищем по primary_skill или additional_skills
    skill_conditions = []
    for skill in skills_list:
        skill_conditions.append(User.primary_skill.ilike(f"%{skill}%"))
        skill_conditions.append(User.additional_skills.ilike(f"%{skill}%"))
    
    query = query.where(or_(*skill_conditions))
    
    # Сортируем по активности (last_active от новых к старым)
    query = query.order_by(User.last_active.desc())
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def count_invitations_today(
    session: AsyncSession,
    from_user_id: int
) -> int:
    """
    Подсчитать количество приглашений, отправленных сегодня
    
    Args:
        session: сессия БД
        from_user_id: ID пользователя-отправителя
    
    Returns:
        Количество приглашений за сегодня
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = await session.execute(
        select(func.count())
        .select_from(Invitation)
        .where(
            and_(
                Invitation.from_user_id == from_user_id,
                Invitation.created_at >= today_start
            )
        )
    )
    return result.scalar()


async def check_invitation_limit(
    session: AsyncSession,
    from_user_id: int,
    max_per_day: int = 5
) -> bool:
    """
    Проверить, не превышен ли лимит приглашений

    Args:
        session: сессия БД
        from_user_id: ID пользователя-отправителя
        max_per_day: максимальное количество приглашений в день

    Returns:
        True если лимит не превышен, False если превышен
    """
    count = await count_invitations_today(session, from_user_id)
    return count < max_per_day


# ===== STATISTICS FUNCTIONS =====

async def get_user_stats(session: AsyncSession, user_id: int) -> dict:
    """
    Получить статистику пользователя

    Returns:
        dict с полями:
        - user: объект User
        - days_registered: количество дней с регистрации
        - sent_invitations: список отправленных приглашений
        - received_invitations: список полученных приглашений
    """
    # Получаем пользователя
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    # Считаем дни с регистрации
    days_registered = (datetime.utcnow() - user.created_at).days

    # Получаем отправленные приглашения
    sent_invitations = await get_sent_invitations(session, user_id)

    # Получаем полученные приглашения
    received_invitations = await get_received_invitations(session, user_id)

    return {
        'user': user,
        'days_registered': days_registered,
        'sent_invitations': sent_invitations,
        'received_invitations': received_invitations,
    }


async def get_team_stats(session: AsyncSession, team_id: int) -> dict:
    """
    Получить статистику команды

    Returns:
        dict с полями:
        - team: объект Team
        - sent_invitations: приглашения от команды
        - received_requests: запросы к команде
        - matching_users_count: количество подходящих пользователей
    """
    # Получаем команду
    team = await get_team_by_id(session, team_id)
    if not team:
        return None

    # Получаем приглашения от команды
    result = await session.execute(
        select(Invitation).where(Invitation.from_team_id == team_id)
    )
    sent_invitations = list(result.scalars().all())

    # Получаем запросы к команде (приглашения к лидеру без from_team_id)
    result = await session.execute(
        select(Invitation).where(
            and_(
                Invitation.to_user_id == team.leader_id,
                Invitation.from_team_id == None
            )
        )
    )
    received_requests = list(result.scalars().all())

    # Считаем подходящих пользователей по навыкам
    matching_users_count = 0
    if team.needed_skills:
        matching_users = await find_users_by_skills(session, team.needed_skills)
        matching_users_count = len(matching_users)

    return {
        'team': team,
        'sent_invitations': sent_invitations,
        'received_requests': received_requests,
        'matching_users_count': matching_users_count,
    }


async def count_profile_views(session: AsyncSession, user_id: int) -> int:
    """
    Подсчитать просмотры профиля
    Пока возвращаем количество полученных приглашений как прокси для просмотров
    """
    result = await session.execute(
        select(func.count())
        .select_from(Invitation)
        .where(Invitation.to_user_id == user_id)
    )
    return result.scalar()


# ===== SEARCH FOR COFOUNDERS AND PARTICIPANTS =====

def calculate_compatibility(user1: User, user2: User) -> int:
    """
    Рассчитать совместимость между двумя соло-основателями

    Алгоритм:
    - Разные навыки (Backend + Design) = 4 звезды
    - Похожие идеи = +1 звезда
    - Одинаковые навыки = 2 звезды

    Returns:
        Количество звезд от 1 до 5
    """
    stars = 2  # базовая совместимость

    # Проверяем навыки
    skill1 = user1.primary_skill or ""
    skill2 = user2.primary_skill or ""

    # Если навыки разные - это хорошо (дополняют друг друга)
    if skill1 and skill2 and skill1.lower() != skill2.lower():
        stars = 4

    # Проверяем похожесть идей (простой check на общие слова)
    idea1_what = (user1.idea_what or "").lower()
    idea2_what = (user2.idea_what or "").lower()

    # Ищем общие ключевые слова
    common_keywords = ["образование", "доставка", "финансы", "здоровье", "edtech", "fintech", "healthtech", "foodtech"]
    idea1_category = None
    idea2_category = None

    for keyword in common_keywords:
        if keyword in idea1_what:
            idea1_category = keyword
        if keyword in idea2_what:
            idea2_category = keyword

    # Если идеи из одной категории - добавляем звезду
    if idea1_category and idea2_category and idea1_category == idea2_category:
        stars = min(5, stars + 1)

    return stars


async def find_cofounders(
    session: AsyncSession,
    user_id: int
) -> List[tuple[User, int]]:
    """
    Найти других соло-основателей для коллаборации

    Returns:
        Список кортежей (User, stars) отсортированный по совместимости
    """
    # Получаем текущего пользователя
    current_user = await get_user_by_id(session, user_id)
    if not current_user:
        return []

    # Ищем других соло-основателей
    query = select(User).where(
        and_(
            User.user_type == UserType.COFOUNDER,
            User.id != user_id
        )
    ).order_by(User.last_active.desc())

    result = await session.execute(query)
    cofounders = list(result.scalars().all())

    # Рассчитываем совместимость для каждого
    cofounders_with_stars = []
    for cofounder in cofounders:
        stars = calculate_compatibility(current_user, cofounder)
        cofounders_with_stars.append((cofounder, stars))

    # Сортируем по количеству звезд (от большего к меньшему)
    cofounders_with_stars.sort(key=lambda x: x[1], reverse=True)

    return cofounders_with_stars


async def find_teams_for_participant(
    session: AsyncSession,
    participant_id: int
) -> List[Team]:
    """
    Найти команды, которым нужны навыки соискателя

    Returns:
        Список команд, отсортированный по активности
    """
    # Получаем соискателя
    participant = await get_user_by_id(session, participant_id)
    if not participant:
        return []

    # Собираем все навыки соискателя
    participant_skills = []
    if participant.primary_skill:
        participant_skills.append(participant.primary_skill.lower())
    if participant.additional_skills:
        additional = [s.strip().lower() for s in participant.additional_skills.split(',')]
        participant_skills.extend(additional)

    if not participant_skills:
        return []

    # Ищем команды, которым нужны эти навыки
    query = select(Team).where(Team.status == TeamStatus.ACTIVE)
    result = await session.execute(query)
    all_teams = list(result.scalars().all())

    # Фильтруем команды по навыкам
    matching_teams = []
    for team in all_teams:
        if team.needed_skills:
            needed_skills_lower = team.needed_skills.lower()
            for skill in participant_skills:
                # Простой поиск подстроки
                skill_keywords = skill.split('(')[0].strip().lower()
                if skill_keywords in needed_skills_lower:
                    matching_teams.append(team)
                    break

    # Сортируем по дате обновления (более активные сверху)
    matching_teams.sort(key=lambda t: t.updated_at, reverse=True)

    return matching_teams


async def count_teams_need_skill(
    session: AsyncSession,
    skill: str
) -> int:
    """
    Подсчитать количество команд, которым нужен определенный навык
    """
    skill_lower = skill.lower()
    skill_keywords = skill_lower.split('(')[0].strip()

    query = select(Team).where(
        and_(
            Team.status == TeamStatus.ACTIVE,
            Team.needed_skills.ilike(f"%{skill_keywords}%")
        )
    )
    result = await session.execute(query)
    teams = list(result.scalars().all())

    return len(teams)
