"""Pytest configuration and fixtures."""
import asyncio
import logging
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.activity import Activity
from app.models.building import Building
from app.models.organization import Organization
from app.models.phone import Phone

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# URL для тестовой базы данных
# Автоматически определяем: Docker или локальное окружение
if os.getenv("DOCKER_ENV") or os.path.exists("/.dockerenv"):
    # В Docker контейнере используем имя сервиса 'db'
    TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@db:5432/test_mkk_luna_db"
else:
    # Локально используем localhost
    TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/test_mkk_luna_db"

logging.info(f"Используется тестовая БД: {TEST_DATABASE_URL}")

# Создаем тестовый движок
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

# Создаем фабрику сессий для тестов
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии тестирования."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для создания тестовой сессии базы данных.
    
    Создает все таблицы перед тестом и удаляет их после.
    """
    # Создаем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Удаляем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для создания тестового HTTP клиента.
    
    Переопределяет зависимость get_db для использования тестовой базы данных.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_building(db_session: AsyncSession) -> Building:
    """Фикстура для создания тестового здания."""
    building = Building(
        address="Тестовая улица, 123",
        latitude=55.751244,
        longitude=37.618423
    )
    db_session.add(building)
    await db_session.commit()
    await db_session.refresh(building)
    return building


@pytest_asyncio.fixture
async def sample_activity(db_session: AsyncSession) -> Activity:
    """Фикстура для создания тестового вида деятельности."""
    activity = Activity(
        name="Тестовая деятельность",
        parent_id=None,
        level=1
    )
    db_session.add(activity)
    await db_session.commit()
    await db_session.refresh(activity)
    return activity


@pytest_asyncio.fixture
async def sample_organization(
    db_session: AsyncSession,
    sample_building: Building,
    sample_activity: Activity
) -> Organization:
    """Фикстура для создания тестовой организации."""
    org = Organization(
        name="Тестовая организация",
        building_id=sample_building.id
    )
    db_session.add(org)
    await db_session.flush()
    
    # Добавляем телефон
    phone = Phone(number="+79991234567", organization_id=org.id)
    db_session.add(phone)
    
    # Добавляем вид деятельности
    await db_session.run_sync(lambda session: org.activities.append(sample_activity))
    
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
def api_headers() -> dict:
    """Фикстура для создания заголовков с API ключом."""
    return {"X-API-KEY": settings.API_KEY}


@pytest.fixture
def invalid_api_headers() -> dict:
    """Фикстура для создания заголовков с неверным API ключом."""
    return {"X-API-KEY": "invalid_key"}
