"""Pytest Async Fixtures and Testing Configuration.

Sets up an in-memory SQLite async database engine and FastAPI AsyncClient override
for fast, isolated unit and integration testing.
"""

from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

import src.db.session as db_session_module
from src.db.base import Base
from src.db.session import get_async_db
from src.main import app

# In-memory SQLite async database for isolated fast testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
async def setup_test_database(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[None, None]:
    """Creates database tables before each test and overrides global session factory."""
    # Override AsyncSessionFactory so background tasks use in-memory SQLite
    monkeypatch.setattr(db_session_module, "AsyncSessionFactory", TestingSessionFactory)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields an isolated test database session."""
    async with TestingSessionFactory() as session:
        yield session


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yields an HTTP AsyncClient connected to the FastAPI application."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
