"""Text formatting utilities"""

from typing import List
from datetime import datetime, timedelta

from bot.database.models import User, Team, Invitation


def format_skills(skills: List[str], separator: str = ", ") -> str:
    """Format skills list as comma-separated string"""
    return separator.join(skills) if skills else "Not specified"


def format_user_profile(user: User, include_stats: bool = False) -> str:
    """
    Format user profile for display

    Args:
        user: User object
        include_stats: Include statistics

    Returns:
        Formatted profile text
    """
    icon = {"TEAM": "🎯", "COFOUNDER": "💡", "PARTICIPANT": "👤"}[user.user_type.name]

    profile = f"{icon} <b>{user.name}</b>\n"
    profile += f"Type: {user.user_type.name.title()}\n"

    if user.primary_skill:
        profile += f"Skill: {user.primary_skill}\n"

    if user.additional_skills:
        profile += f"Additional: {user.additional_skills}\n"

    if user.idea_what:
        profile += f"\n💡 Idea: {user.idea_what}\n"

    if user.idea_who:
        profile += f"Target: {user.idea_who}\n"

    return profile


def format_team_profile(team: Team) -> str:
    """Format team profile for display"""
    profile = f"🎯 <b>{team.team_name}</b>\n"
    profile += f"Status: {team.status.name}\n"

    if team.idea_description:
        profile += f"\n💡 {team.idea_description}\n"

    if team.needed_skills:
        profile += f"\n👥 Looking for: {team.needed_skills}\n"

    return profile


def format_invitation(invitation: Invitation, user: User) -> str:
    """Format invitation for display"""
    msg = f"📨 Invitation from <b>{user.name}</b>\n"

    if invitation.message:
        msg += f"\nMessage: {invitation.message}\n"

    return msg


def format_time_ago(dt: datetime) -> str:
    """Format datetime as 'X time ago'"""
    now = datetime.utcnow()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        mins = int(diff.total_seconds() / 60)
        return f"{mins}m ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = diff.days
        return f"{days}d ago"


def format_compatibility_stars(stars: int) -> str:
    """Format compatibility rating as stars"""
    return "⭐" * min(max(stars, 0), 5)
