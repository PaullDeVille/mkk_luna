import logging
from fastapi import Header, HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

def api_key_auth(x_api_key: str = Header(..., alias="X-API-KEY")):
    logger.debug("Проверка API ключа")
    if x_api_key != settings.API_KEY:
        logger.warning(f"Неудачная попытка аутентификации с ключом: {x_api_key[:10]}...")
        raise HTTPException(status_code=403, detail="Invalid API key")
    logger.debug("API ключ успешно проверен")
