"""Tests for CRUD operations"""
import pytest
from bot.database import crud
from bot.database.models import UserType, Language, TeamStatus


class TestUserCRUD:
    """Tests for User CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test creating a new user"""
        user = await crud.create_user(
            session=db_session,
            telegram_id=999888777,
            name="New User",
            user_type=UserType.PARTICIPANT,
            username="newuser",
            primary_skill="JavaScript"
        )

        assert user.id is not None
        assert user.telegram_id == 999888777
        assert user.name == "New User"
        assert user.user_type == UserType.PARTICIPANT
        assert user.primary_skill == "JavaScript"
        assert user.language == Language.RU  # default

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id(self, db_session, test_user):
        """Test retrieving user by telegram_id"""
        user = await crud.get_user_by_telegram_id(db_session, test_user.telegram_id)

        assert user is not None
        assert user.id == test_user.id
        assert user.name == test_user.name

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session, test_user):
        """Test retrieving user by id"""
        user = await crud.get_user_by_id(db_session, test_user.id)

        assert user is not None
        assert user.telegram_id == test_user.telegram_id

    @pytest.mark.asyncio
    async def test_check_name_exists(self, db_session, test_user):
        """Test checking if name exists"""
        # Name should exist
        exists = await crud.check_name_exists(
            db_session,
            test_user.name,
            UserType.PARTICIPANT
        )
        assert exists is True

        # Different user type should not exist
        exists = await crud.check_name_exists(
            db_session,
            test_user.name,
            UserType.COFOUNDER
        )
        assert exists is False

        # Non-existent name
        exists = await crud.check_name_exists(
            db_session,
            "Non Existent",
            UserType.PARTICIPANT
        )
        assert exists is False

    @pytest.mark.asyncio
    async def test_update_user_language(self, db_session, test_user):
        """Test updating user language"""
        updated_user = await crud.update_user_language(
            db_session,
            test_user.id,
            Language.EN
        )

        assert updated_user is not None
        assert updated_user.language == Language.EN

    @pytest.mark.asyncio
    async def test_count_users(self, db_session, test_user, test_cofounder):
        """Test counting total users"""
        count = await crud.count_users(db_session)
        assert count >= 2


class TestTeamCRUD:
    """Tests for Team CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_team(self, db_session, test_team_user):
        """Test creating a new team"""
        team = await crud.create_team(
            session=db_session,
            team_name="Test Team",
            leader_id=test_team_user.id,
            idea_description="Building an app",
            needed_skills="Python, React"
        )

        assert team.id is not None
        assert team.team_name == "Test Team"
        assert team.leader_id == test_team_user.id
        assert team.status == TeamStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_team_by_id(self, db_session, test_team_user):
        """Test retrieving team by id"""
        team = await crud.create_team(
            session=db_session,
            team_name="Another Team",
            leader_id=test_team_user.id
        )

        retrieved_team = await crud.get_team_by_id(db_session, team.id)
        assert retrieved_team is not None
        assert retrieved_team.team_name == "Another Team"

    @pytest.mark.asyncio
    async def test_get_teams_by_leader(self, db_session, test_team_user):
        """Test retrieving all teams for a leader"""
        await crud.create_team(
            session=db_session,
            team_name="Team 1",
            leader_id=test_team_user.id
        )
        await crud.create_team(
            session=db_session,
            team_name="Team 2",
            leader_id=test_team_user.id
        )

        teams = await crud.get_teams_by_leader(db_session, test_team_user.id)
        assert len(teams) >= 2


class TestInvitationCRUD:
    """Tests for Invitation CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_invitation(self, db_session, test_user, test_cofounder):
        """Test creating an invitation"""
        invitation = await crud.create_invitation(
            session=db_session,
            from_user_id=test_cofounder.id,
            to_user_id=test_user.id,
            message="Want to collaborate?"
        )

        assert invitation.id is not None
        assert invitation.from_user_id == test_cofounder.id
        assert invitation.to_user_id == test_user.id

    @pytest.mark.asyncio
    async def test_count_invitations_today(self, db_session, test_user, test_cofounder):
        """Test counting invitations sent today"""
        await crud.create_invitation(
            session=db_session,
            from_user_id=test_cofounder.id,
            to_user_id=test_user.id
        )

        count = await crud.count_invitations_today(db_session, test_cofounder.id)
        assert count >= 1

    @pytest.mark.asyncio
    async def test_check_invitation_limit(self, db_session, test_cofounder):
        """Test checking invitation limit"""
        can_send = await crud.check_invitation_limit(
            db_session,
            test_cofounder.id,
            max_per_day=5
        )
        assert can_send is True
