import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import api_key_auth
from app.schemas.building import BuildingOut
from app.schemas.organization import OrganizationOut
from app.crud.building import list_buildings
from app.crud.organization import list_by_building

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buildings", tags=["buildings"], dependencies=[Depends(api_key_auth)])

@router.get("", response_model=list[BuildingOut])
async def get_buildings(db: AsyncSession = Depends(get_db)):
    """Список всех зданий."""
    logger.info("API: Запрос списка всех зданий")
    result = await list_buildings(db)
    logger.debug(f"API: Возвращено {len(result)} зданий")
    return result

@router.get("/{building_id}/organizations", response_model=list[OrganizationOut])
async def organizations_in_building(building_id: int, db: AsyncSession = Depends(get_db)):
    """Организации, расположенные в указанном здании."""
    logger.info(f"API: Запрос организаций в здании: building_id={building_id}")
    result = await list_by_building(db, building_id)
    logger.debug(f"API: Найдено {len(result)} организаций")
    return result
