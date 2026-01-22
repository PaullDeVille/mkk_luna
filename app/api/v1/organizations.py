import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import api_key_auth
from app.schemas.organization import OrganizationOut, OrganizationCreate
from app.crud.organization import (
    get_org, search_by_name, create_org,
    list_in_rectangular_area
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"], dependencies=[Depends(api_key_auth)])

@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    """Получить организацию по идентификатору."""
    logger.info(f"API: Запрос организации: org_id={org_id}")
    org = await get_org(db, org_id)
    if not org:
        logger.warning(f"API: Организация не найдена: org_id={org_id}")
        raise HTTPException(404, detail="Organization not found")
    logger.debug(f"API: Организация найдена: id={org_id}, name='{org.name}'")
    return org

@router.get("/search/by-name", response_model=list[OrganizationOut])
async def search_organizations(name: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    """Поиск организаций по названию (частичное совпадение, регистр не учитывается)."""
    logger.info(f"API: Поиск организаций по названию: '{name}'")
    result = await search_by_name(db, name)
    logger.debug(f"API: Найдено {len(result)} организаций")
    return result

@router.post("", response_model=OrganizationOut, status_code=201)
async def add_organization(payload: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    """Создать организацию с привязкой к зданию, телефонами и видами деятельности."""
    logger.info(f"API: Запрос на создание организации: name='{payload.name}', building_id={payload.building_id}")
    result = await create_org(db, payload.name, payload.building_id, payload.phone_numbers, payload.activity_ids)
    logger.info(f"API: Организация создана: id={result.id}")
    return result

@router.get("/geo/rectangular-area", response_model=list[OrganizationOut])
async def orgs_in_rectangular_area(
    lat: float = Query(..., description="Широта центральной точки"),
    lon: float = Query(..., description="Долгота центральной точки"),
    width_m: float = Query(..., gt=0, description="Ширина прямоугольной области в метрах"),
    height_m: float = Query(..., gt=0, description="Высота прямоугольной области в метрах"),
    db: AsyncSession = Depends(get_db),
):
    """Найти организации в прямоугольной области относительно указанной точки на карте.

    Прямоугольник формируется вокруг центральной точки (lat, lon) с заданными размерами.
    """
    logger.info(f"API: Поиск организаций в прямоугольной области: lat={lat}, lon={lon}, width={width_m}м, height={height_m}м")
    result = await list_in_rectangular_area(db, lat, lon, width_m, height_m)
    logger.debug(f"API: Найдено {len(result)} организаций")
    return result
