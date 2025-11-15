from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, Enum, Boolean, Index, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List
import enum


class Base(DeclarativeBase):
    pass


class UserType(enum.Enum):
    """Тип пользователя"""
    PARTICIPANT = "participant"  # Соискатель
    COFOUNDER = "cofounder"       # Соло-основатель
    TEAM = "team"                 # Лидер команды


class InvitationStatus(enum.Enum):
    """Статус приглашения"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TeamStatus(enum.Enum):
    """Статус команды"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETE = "complete"


class User(Base):
    """Модель пользователя с оптимизацией для поиска"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False, index=True)

    # Навыки и идея
    primary_skill: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    additional_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idea_what: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idea_who: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус поиска (ВАЖНО для производительности!)
    is_searching: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    found_team_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Временные метки
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # Relationships с cascade для автоматической очистки
    led_teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="leader",
        foreign_keys="Team.leader_id",
        cascade="all, delete-orphan"
    )
    sent_invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="from_user",
        foreign_keys="Invitation.from_user_id",
        cascade="all, delete-orphan"
    )
    received_invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="to_user",
        foreign_keys="Invitation.to_user_id",
        cascade="all, delete-orphan"
    )

    # Композитные индексы для частых запросов
    __table_args__ = (
        Index('idx_user_active_search', 'user_type', 'is_searching', 'deleted_at'),
        Index('idx_user_last_active', 'last_active', 'deleted_at'),
        CheckConstraint("user_type IN ('participant', 'cofounder', 'team')", name='check_user_type'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, name={self.name}, type={self.user_type})>"


class Team(Base):
    """Модель команды с оптимизацией"""
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    idea_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    leader_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    needed_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус команды
    status: Mapped[TeamStatus] = mapped_column(Enum(TeamStatus), default=TeamStatus.ACTIVE, index=True)
    is_full: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leader: Mapped["User"] = relationship("User", back_populates="led_teams", foreign_keys=[leader_id])
    invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="from_team",
        foreign_keys="Invitation.from_team_id",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_team_status_full', 'status', 'is_full'),
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, team_name={self.team_name}, leader_id={self.leader_id}, status={self.status})>"


class Invitation(Base):
    """Модель приглашения с оптимизацией для лимитов"""
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    from_team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статус и временные метки
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus),
        default=InvitationStatus.PENDING,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    from_user: Mapped["User"] = relationship(
        "User",
        back_populates="sent_invitations",
        foreign_keys=[from_user_id]
    )
    to_user: Mapped["User"] = relationship(
        "User",
        back_populates="received_invitations",
        foreign_keys=[to_user_id]
    )
    from_team: Mapped[Optional["Team"]] = relationship(
        "Team",
        back_populates="invitations",
        foreign_keys=[from_team_id]
    )

    # Индексы для проверки дневных лимитов и истекших приглашений
    __table_args__ = (
        Index('idx_invitation_daily_limit', 'from_user_id', 'created_at'),
        Index('idx_invitation_team_daily', 'from_team_id', 'created_at'),
        Index('idx_invitation_expired', 'status', 'expires_at'),
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'expired')", name='check_invitation_status'),
    )

    def __repr__(self) -> str:
        return f"<Invitation(id={self.id}, from_user={self.from_user_id}, to_user={self.to_user_id}, status={self.status})>"
