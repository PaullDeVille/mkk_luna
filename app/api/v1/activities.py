import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import api_key_auth
from app.schemas.activity import ActivityOut, ActivityCreate
from app.schemas.organization import OrganizationOut
from app.crud.activity import create_activity, list_activities
from app.crud.organization import list_by_activity_with_descendants, list_by_activity_name_with_descendants

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/activities", tags=["activities"], dependencies=[Depends(api_key_auth)])

@router.get("", response_model=list[ActivityOut])
async def get_activities(db: AsyncSession = Depends(get_db)):
    """Список всех видов деятельности (плоский)."""
    logger.info("API: Запрос списка всех видов деятельности")
    result = await list_activities(db)
    logger.debug(f"API: Возвращено {len(result)} видов деятельности")
    return result

@router.post("", response_model=ActivityOut, status_code=201)
async def add_activity(payload: ActivityCreate, db: AsyncSession = Depends(get_db)):
    """Создать вид деятельности с проверкой глубины вложенности.

    Для создания активности нулевого уровня {"parent_id": null}
    """
    logger.info(f"API: Запрос на создание вида деятельности: name='{payload.name}', parent_id={payload.parent_id}")
    result = await create_activity(db, payload.name, payload.parent_id)
    logger.info(f"API: Вид деятельности создан: id={result.id}")
    return result

@router.get("/{activity_id}/organizations", response_model=list[OrganizationOut])
async def organizations_by_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    """Получить организации по идентификатору вида деятельности (включая дочерние)."""
    logger.info(f"API: Запрос организаций по виду деятельности: activity_id={activity_id}")
    result = await list_by_activity_with_descendants(db, activity_id)
    logger.debug(f"API: Найдено {len(result)} организаций")
    return result

@router.get("/search/by-name/organizations", response_model=list[OrganizationOut])
async def organizations_by_activity_name(
    name: str = Query(..., min_length=1, description="Название вида деятельности"),
    db: AsyncSession = Depends(get_db)
):
    """Поиск организаций по названию вида деятельности (включая дочерние виды деятельности).

    Например, поиск по «Еда» найдёт организации с деятельностью:
    - Еда
    - Мясная продукция (дочерняя)
    - Молочная продукция (дочерняя)
    """
    logger.info(f"API: Поиск организаций по названию вида деятельности: '{name}'")
    result = await list_by_activity_name_with_descendants(db, name)
    logger.debug(f"API: Найдено {len(result)} организаций")
    return result
