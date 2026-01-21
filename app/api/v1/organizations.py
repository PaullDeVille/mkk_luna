from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import api_key_auth
from app.schemas.organization import OrganizationOut, OrganizationCreate
from app.crud.organization import (
    get_org, search_by_name, create_org,
    list_in_rectangular_area
)

router = APIRouter(prefix="/organizations", tags=["organizations"], dependencies=[Depends(api_key_auth)])

@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    """Получить организацию по идентификатору."""
    org = await get_org(db, org_id)
    if not org:
        raise HTTPException(404, detail="Organization not found")
    return org

@router.get("/search/by-name", response_model=list[OrganizationOut])
async def search_organizations(name: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    """Поиск организаций по названию (частичное совпадение, регистр не учитывается)."""
    return await search_by_name(db, name)

@router.post("", response_model=OrganizationOut, status_code=201)
async def add_organization(payload: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    """Создать организацию с привязкой к зданию, телефонами и видами деятельности."""
    return await create_org(db, payload.name, payload.building_id, payload.phone_numbers, payload.activity_ids)

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
    return await list_in_rectangular_area(db, lat, lon, width_m, height_m)
