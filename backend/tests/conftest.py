"""Pytest fixtures for database and Redis."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.database.connection import Base, get_db
from src.database.redis import RedisClient
from src.main import app

# Test database URL (use separate test database)
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/aitrainer_test"
)
TEST_REDIS_URL = "redis://localhost:6379/1"  # Use database 1 for tests


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable connection pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(
    test_db_engine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_redis_client() -> AsyncGenerator[Redis, None]:
    """Create test Redis client."""
    client = RedisClient()
    client._redis_url = TEST_REDIS_URL
    await client.connect()

    yield client.client

    # Clear test database
    await client.client.flushdb()
    await client.disconnect()


@pytest_asyncio.fixture(scope="function")
async def test_client(
    test_db_session: AsyncSession,
    test_redis_client: Redis,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database and Redis overrides."""

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_health_metrics() -> dict:
    """Sample health metrics data for testing."""
    return {
        "date": "2025-10-24",
        "hrv_rmssd": 45.0,
        "resting_heart_rate": 58,
        "sleep_duration_hours": 7.5,
        "sleep_quality_score": 85,
        "stress_level": 30,
    }


@pytest.fixture
def sample_workout_data() -> dict:
    """Sample workout data for testing."""
    return {
        "date": "2025-10-24",
        "workout_type": "run",
        "duration_minutes": 45,
        "distance_km": 8.5,
        "avg_heart_rate": 155,
        "max_heart_rate": 175,
        "training_load": 125,
    }
