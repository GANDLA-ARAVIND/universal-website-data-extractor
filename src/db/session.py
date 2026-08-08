"""Database Session Factory and Async Engine Configuration.

Configures SQLAlchemy 2.0 async engine (asyncpg or aiosqlite) and provides an async generator
for FastAPI dependency injection.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.core.config import settings

# Engine kwargs
engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

if settings.USE_SQLITE:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 3600

# Create async engine
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    **engine_kwargs,
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator yielding an active async database session.

    Yields:
        AsyncSession: Isolated async database session context.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
