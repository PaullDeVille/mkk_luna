from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@db:5432/mkk_luna_db"
    API_KEY: str = "SECRET_API_KEY"
    APP_NAME: str = "mkk_luna"

settings = Settings()
