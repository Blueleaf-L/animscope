"""Pytest fixtures for API testing."""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.company import Company
from app.models.work import Work

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database for each test function."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP test client with database override."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seed_data(db_session: AsyncSession):
    """Seed test database with sample companies and works."""
    company = Company(name="测试动画公司", type="3D")
    db_session.add(company)
    await db_session.flush()

    works = [
        Work(company_id=company.id, name="测试作品A", year=2023, rating_label="年度推荐", rating_score=5.0),
        Work(company_id=company.id, name="测试作品B", year=2022, rating_label="佳作", rating_score=3.0),
        Work(company_id=company.id, name="测试作品C", year=2024, rating_label="还行", rating_score=1.0),
        Work(company_id=company.id, name="测试作品D", year=2023, rating_label="拉了", rating_score=-3.0),
    ]
    db_session.add_all(works)

    company2 = Company(name="另一个动画公司", type="2D")
    db_session.add(company2)
    await db_session.flush()

    works2 = [
        Work(company_id=company2.id, name="2D作品A", year=2023, rating_label="年度推荐", rating_score=5.0),
        Work(company_id=company2.id, name="2D作品B", year=2024, rating_label="佳作", rating_score=3.0),
    ]
    db_session.add_all(works2)
    await db_session.commit()

    return {"companies": [company, company2], "works": works + works2}
