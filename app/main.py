import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.organizations import router as org_router
from app.api.v1.buildings import router as bld_router
from app.api.v1.activities import router as act_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

logger.info(f"Инициализация приложения: {settings.APP_NAME}")

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Входящий запрос: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Ответ: {request.method} {request.url.path} - {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса {request.method} {request.url.path}: {str(e)}", exc_info=True)
        raise

# Глобальный обработчик исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Необработанное исключение: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

app.include_router(org_router, prefix="/api/v1")
app.include_router(bld_router, prefix="/api/v1")
app.include_router(act_router, prefix="/api/v1")

logger.info("Маршруты успешно подключены")

@app.get("/health")
async def health():
    """Проверка доступности сервиса."""
    logger.debug("Health check запрос")
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    logger.info("Приложение запущено")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Приложение завершает работу")
