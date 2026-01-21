from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import api_key_auth
from app.schemas.activity import ActivityOut, ActivityCreate
from app.schemas.organization import OrganizationOut
from app.crud.activity import create_activity, list_activities
from app.crud.organization import list_by_activity_with_descendants, list_by_activity_name_with_descendants

router = APIRouter(prefix="/activities", tags=["activities"], dependencies=[Depends(api_key_auth)])

@router.get("", response_model=list[ActivityOut])
async def get_activities(db: AsyncSession = Depends(get_db)):
    """Список всех видов деятельности (плоский)."""
    return await list_activities(db)

@router.post("", response_model=ActivityOut, status_code=201)
async def add_activity(payload: ActivityCreate, db: AsyncSession = Depends(get_db)):
    """Создать вид деятельности с проверкой глубины вложенности.

    Для создания активности нулевого уровня {"parent_id": null}
    """
    return await create_activity(db, payload.name, payload.parent_id)

@router.get("/{activity_id}/organizations", response_model=list[OrganizationOut])
async def organizations_by_activity(activity_id: int, db: AsyncSession = Depends(get_db)):
    """Получить организации по идентификатору вида деятельности (включая дочерние)."""
    return await list_by_activity_with_descendants(db, activity_id)

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
    return await list_by_activity_name_with_descendants(db, name)
