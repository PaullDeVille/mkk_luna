from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.organizations import router as org_router
from app.api.v1.buildings import router as bld_router
from app.api.v1.activities import router as act_router

app = FastAPI(title=settings.APP_NAME)

app.include_router(org_router, prefix="/api/v1")
app.include_router(bld_router, prefix="/api/v1")
app.include_router(act_router, prefix="/api/v1")

@app.get("/health")
async def health():
    """Проверка доступности сервиса."""
    return {"status": "ok"}
