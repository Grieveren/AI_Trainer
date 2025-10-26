"""Database connection configuration using SQLAlchemy 2.0+ with asyncpg."""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/aitrainer"
)

# Create synchronous database URL (for Celery jobs)
SYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()

# Create synchronous engine (for Celery background jobs)
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Create synchronous session factory
SyncSessionLocal = sessionmaker(
    sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.

    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for consistency with route code
get_async_session = get_db


@contextmanager
def get_sync_db_session():
    """
    Context manager to get synchronous database session.

    Usage in Celery jobs or tests:
        with get_sync_db_session() as db:
            user = db.query(User).first()
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
