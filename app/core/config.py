import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@db:5432/mkk_luna_db"
    API_KEY: str = "SECRET_API_KEY"
    APP_NAME: str = "mkk_luna"

logger.info("Загрузка настроек приложения")
settings = Settings()
logger.info(f"Приложение: {settings.APP_NAME}")
logger.debug(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'не указан'}")
