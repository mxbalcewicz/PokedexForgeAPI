from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from testcontainers.postgres import PostgresContainer

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def async_db_url(postgres_container: PostgresContainer) -> str:
    url = postgres_container.get_connection_url()
    # testcontainers returns postgresql+psycopg2://... → swap driver
    return url.replace("postgresql+psycopg2", "postgresql+asyncpg")


@pytest_asyncio.fixture(scope="function")
async def db_engine(async_db_url: str) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(async_db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Each test gets its own transaction that is rolled back on teardown,
    keeping tests fully isolated without recreating the schema.
    """
    async with db_engine.connect() as conn:
        await conn.begin()

        session_factory = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",  # nested savepoints → real rollback
        )

        async with session_factory() as session:
            yield session

        await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client with get_db overridden to use the test session.
    Every request in a test hits the same rolled-back transaction.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
