"""
Admin Panel для Team Finder Bot.

Веб-интерфейс для управления ботом и просмотра статистики.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Добавляем путь к bot модулю
sys.path.insert(0, str(Path(__file__).parent.parent / "bot"))

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database.models import User, Team, Invitation, UserType, InvitationStatus, TeamStatus
from config import settings

app = Flask(__name__)
CORS(app)

# Настройка подключения к БД
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Получить сессию БД"""
    async with AsyncSessionLocal() as session:
        yield session


@app.route("/")
async def index():
    """Главная страница админки"""
    return render_template("index.html")


@app.route("/api/stats")
async def get_stats():
    """Получить общую статистику"""
    try:
        async with AsyncSessionLocal() as session:
            # Общее количество пользователей
            total_users_result = await session.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar()

            # Пользователи по типам
            teams_result = await session.execute(
                select(func.count(User.id)).where(User.user_type == UserType.TEAM)
            )
            teams_count = teams_result.scalar()

            cofounders_result = await session.execute(
                select(func.count(User.id)).where(User.user_type == UserType.COFOUNDER)
            )
            cofounders_count = cofounders_result.scalar()

            participants_result = await session.execute(
                select(func.count(User.id)).where(User.user_type == UserType.PARTICIPANT)
            )
            participants_count = participants_result.scalar()

            # Общее количество команд
            total_teams_result = await session.execute(select(func.count(Team.id)))
            total_teams = total_teams_result.scalar()

            # Активные команды
            active_teams_result = await session.execute(
                select(func.count(Team.id)).where(Team.status == TeamStatus.ACTIVE)
            )
            active_teams = active_teams_result.scalar()

            # Приглашения
            total_invitations_result = await session.execute(select(func.count(Invitation.id)))
            total_invitations = total_invitations_result.scalar()

            pending_invitations_result = await session.execute(
                select(func.count(Invitation.id)).where(
                    Invitation.status == InvitationStatus.PENDING
                )
            )
            pending_invitations = pending_invitations_result.scalar()

            accepted_invitations_result = await session.execute(
                select(func.count(Invitation.id)).where(
                    Invitation.status == InvitationStatus.ACCEPTED
                )
            )
            accepted_invitations = accepted_invitations_result.scalar()

            return jsonify(
                {
                    "users": {
                        "total": total_users,
                        "teams": teams_count,
                        "cofounders": cofounders_count,
                        "participants": participants_count,
                    },
                    "teams": {"total": total_teams, "active": active_teams},
                    "invitations": {
                        "total": total_invitations,
                        "pending": pending_invitations,
                        "accepted": accepted_invitations,
                    },
                }
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users")
async def get_users():
    """Получить список пользователей"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        user_type = request.args.get("type", None)

        async with AsyncSessionLocal() as session:
            query = select(User).order_by(User.created_at.desc())

            if user_type:
                query = query.where(User.user_type == UserType[user_type.upper()])

            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

            result = await session.execute(query)
            users = result.scalars().all()

            users_data = []
            for user in users:
                users_data.append(
                    {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "name": user.name,
                        "user_type": user.user_type.value,
                        "primary_skill": user.primary_skill,
                        "is_searching": user.is_searching,
                        "created_at": user.created_at.isoformat(),
                        "last_active": user.last_active.isoformat(),
                    }
                )

            return jsonify({"users": users_data, "page": page, "per_page": per_page})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/teams")
async def get_teams():
    """Получить список команд"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        async with AsyncSessionLocal() as session:
            query = select(Team).order_by(Team.created_at.desc())
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

            result = await session.execute(query)
            teams = result.scalars().all()

            teams_data = []
            for team in teams:
                teams_data.append(
                    {
                        "id": team.id,
                        "team_name": team.team_name,
                        "idea_description": team.idea_description,
                        "needed_skills": team.needed_skills,
                        "status": team.status.value,
                        "is_full": team.is_full,
                        "leader_id": team.leader_id,
                        "created_at": team.created_at.isoformat(),
                    }
                )

            return jsonify({"teams": teams_data, "page": page, "per_page": per_page})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/invitations")
async def get_invitations():
    """Получить список приглашений"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        status = request.args.get("status", None)

        async with AsyncSessionLocal() as session:
            query = select(Invitation).order_by(Invitation.created_at.desc())

            if status:
                query = query.where(Invitation.status == InvitationStatus[status.upper()])

            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)

            result = await session.execute(query)
            invitations = result.scalars().all()

            invitations_data = []
            for inv in invitations:
                invitations_data.append(
                    {
                        "id": inv.id,
                        "from_user_id": inv.from_user_id,
                        "to_user_id": inv.to_user_id,
                        "from_team_id": inv.from_team_id,
                        "status": inv.status.value,
                        "created_at": inv.created_at.isoformat(),
                        "viewed_at": inv.viewed_at.isoformat() if inv.viewed_at else None,
                        "responded_at": (
                            inv.responded_at.isoformat() if inv.responded_at else None
                        ),
                    }
                )

            return jsonify(
                {"invitations": invitations_data, "page": page, "per_page": per_page}
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


if __name__ == "__main__":
    # Получаем порт из ENV или используем 5000 по умолчанию
    port = int(os.environ.get("ADMIN_PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"

    print(f"🚀 Starting Admin Panel on http://0.0.0.0:{port}")
    print(f"📊 Debug mode: {debug}")

    app.run(host="0.0.0.0", port=port, debug=debug)
