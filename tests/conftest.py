"""Pytest configuration and fixtures"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from bot.database.models import Base, UserType, Language
from bot.database import crud


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine"""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def test_user(db_session):
    """Create test user"""
    user = await crud.create_user(
        session=db_session,
        telegram_id=123456789,
        name="Test User",
        user_type=UserType.PARTICIPANT,
        username="testuser",
        primary_skill="Python"
    )
    return user


@pytest.fixture
async def test_cofounder(db_session):
    """Create test cofounder"""
    user = await crud.create_user(
        session=db_session,
        telegram_id=987654321,
        name="Test Cofounder",
        user_type=UserType.COFOUNDER,
        username="cofounder",
        primary_skill="Design",
        idea_what="SaaS platform",
        idea_who="Startups"
    )
    return user


@pytest.fixture
async def test_team_user(db_session):
    """Create test team leader"""
    user = await crud.create_user(
        session=db_session,
        telegram_id=111222333,
        name="Team Leader",
        user_type=UserType.TEAM,
        username="teamlead"
    )
    return user
