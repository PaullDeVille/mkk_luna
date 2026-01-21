import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, bindparam
from sqlalchemy.orm import joinedload
from app.models.organization import Organization
from app.models.phone import Phone
from app.models.activity import Activity
from app.models.building import Building

async def get_org(db: AsyncSession, org_id: int):
    """Получить организацию по идентификатору."""
    stmt = (
        select(Organization)
        .options(
            joinedload(Organization.building),
            joinedload(Organization.phones),
            joinedload(Organization.activities),
        )
        .where(Organization.id == org_id)
    )
    res = await db.execute(stmt)
    return res.scalars().first()

async def search_by_name(db: AsyncSession, name: str):
    """Поиск организаций по названию (частичное совпадение, без учета регистра)."""
    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(func.lower(Organization.name).like(f"%{name.lower()}%"))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    return res.scalars().unique().all()

async def list_by_building(db: AsyncSession, building_id: int):
    """Получить список всех организаций в указанном здании."""
    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Organization.building_id == building_id)
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    return res.scalars().unique().all()

async def list_by_activity_with_descendants(db: AsyncSession, activity_id: int):
    """Получить список организаций по виду деятельности, включая дочерние виды деятельности."""
    sql = text("""
        WITH RECURSIVE act_tree AS (
            SELECT id, parent_id FROM activities WHERE id = :root_id
            UNION ALL
            SELECT a.id, a.parent_id
            FROM activities a
            JOIN act_tree t ON a.parent_id = t.id
        )
        SELECT DISTINCT o.id
        FROM organizations o
        JOIN organization_activity oa ON oa.organization_id = o.id
        JOIN act_tree t ON t.id = oa.activity_id
        ORDER BY o.id
    """)
    rows = (await db.execute(sql, {"root_id": activity_id})).fetchall()
    ids = [r[0] for r in rows]
    if not ids:
        return []
    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Organization.id.in_(ids))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    return res.scalars().unique().all()

async def list_by_activity_name_with_descendants(db: AsyncSession, activity_name: str):
    """Поиск организаций по названию вида деятельности, включая дочерние виды деятельности."""
    stmt = select(Activity).where(func.lower(Activity.name) == activity_name.lower())
    res = await db.execute(stmt)
    matching_activities = res.scalars().all()

    if not matching_activities:
        return []

    if len(matching_activities) == 1:
        return await list_by_activity_with_descendants(db, matching_activities[0].id)

    activity_ids = [act.id for act in matching_activities]

    sql = text("""
        WITH RECURSIVE act_tree AS (
            SELECT id, parent_id FROM activities WHERE id IN :root_ids
            UNION ALL
            SELECT a.id, a.parent_id
            FROM activities a
            JOIN act_tree t ON a.parent_id = t.id
        )
        SELECT DISTINCT o.id
        FROM organizations o
        JOIN organization_activity oa ON oa.organization_id = o.id
        JOIN act_tree t ON t.id = oa.activity_id
        ORDER BY o.id
    """).bindparams(bindparam("root_ids", expanding=True))

    rows = (await db.execute(sql, {"root_ids": activity_ids})).fetchall()
    org_ids = [r[0] for r in rows]

    if not org_ids:
        return []

    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Organization.id.in_(org_ids))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    return res.scalars().unique().all()

async def list_in_rectangular_area(db: AsyncSession, center_lat: float, center_lon: float, width_m: float, height_m: float):
    """Найти организации в прямоугольной области относительно указанной точки на карте.

    Прямоугольник формируется вокруг центральной точки с заданными размерами.
    """
    DEGREES_PER_METER_LAT = 1.0 / 111000.0

    half_height_deg = (height_m / 2.0) * DEGREES_PER_METER_LAT
    half_width_deg = (width_m / 2.0) * DEGREES_PER_METER_LAT / math.cos(math.radians(center_lat))

    min_lat = center_lat - half_height_deg
    max_lat = center_lat + half_height_deg
    min_lon = center_lon - half_width_deg
    max_lon = center_lon + half_width_deg

    stmt = (
        select(Organization)
        .join(Organization.building)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Building.latitude.between(min_lat, max_lat))
        .where(Building.longitude.between(min_lon, max_lon))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    return res.scalars().unique().all()

async def create_org(db: AsyncSession, name: str, building_id: int, phone_numbers: list[str], activity_ids: list[int]):
    """Создать новую организацию с указанными телефонами и видами деятельности."""
    org = Organization(name=name, building_id=building_id)
    db.add(org)
    await db.flush()

    for num in phone_numbers:
        db.add(Phone(number=num, organization_id=org.id))

    if activity_ids:
        res = await db.execute(select(Activity).where(Activity.id.in_(activity_ids)))
        org.activities = res.scalars().all()

    await db.commit()
    return await get_org(db, org.id)
