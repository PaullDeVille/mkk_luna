import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

logger.info("Инициализация подключения к базе данных")
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, autoflush=False, autocommit=False, expire_on_commit=False)
logger.info("Движок базы данных успешно создан")

class Base(DeclarativeBase):
    pass

async def get_db():
    logger.debug("Создание новой сессии базы данных")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            logger.debug("Сессия базы данных успешно завершена")
        except Exception as e:
            logger.error(f"Ошибка в сессии базы данных: {str(e)}")
            raise
