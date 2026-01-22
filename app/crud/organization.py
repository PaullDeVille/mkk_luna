import logging
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, bindparam
from sqlalchemy.orm import joinedload
from app.models.organization import Organization
from app.models.phone import Phone
from app.models.activity import Activity
from app.models.building import Building

logger = logging.getLogger(__name__)

async def get_org(db: AsyncSession, org_id: int):
    """Получить организацию по идентификатору."""
    logger.debug(f"Получение организации: id={org_id}")
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
    org = res.scalars().first()
    if org:
        logger.info(f"Организация найдена: id={org_id}, name='{org.name}'")
    else:
        logger.warning(f"Организация не найдена: id={org_id}")
    return org

async def search_by_name(db: AsyncSession, name: str):
    """Поиск организаций по названию (частичное совпадение, без учета регистра)."""
    logger.debug(f"Поиск организаций по названию: '{name}'")
    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(func.lower(Organization.name).like(f"%{name.lower()}%"))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()
    logger.info(f"Найдено {len(orgs)} организаций по запросу '{name}'")
    return orgs

async def list_by_building(db: AsyncSession, building_id: int):
    """Получить список всех организаций в указанном здании."""
    logger.debug(f"Получение организаций в здании: building_id={building_id}")
    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Organization.building_id == building_id)
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()
    logger.info(f"Найдено {len(orgs)} организаций в здании {building_id}")
    return orgs

async def list_by_activity_with_descendants(db: AsyncSession, activity_id: int):
    """Получить список организаций по виду деятельности, включая дочерние виды деятельности."""
    logger.debug(f"Получение организаций по виду деятельности: activity_id={activity_id}")
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
        logger.info(f"Организации по виду деятельности {activity_id} не найдены")
        return []
    logger.debug(f"Найдено {len(ids)} организаций через рекурсивный запрос")
    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Organization.id.in_(ids))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()
    logger.info(f"Получено {len(orgs)} организаций по виду деятельности {activity_id}")
    return orgs

async def list_by_activity_name_with_descendants(db: AsyncSession, activity_name: str):
    """Поиск организаций по названию вида деятельности, включая дочерние виды деятельности."""
    logger.debug(f"Поиск организаций по названию вида деятельности: '{activity_name}'")
    stmt = select(Activity).where(func.lower(Activity.name) == activity_name.lower())
    res = await db.execute(stmt)
    matching_activities = res.scalars().all()

    if not matching_activities:
        logger.warning(f"Вид деятельности не найден: '{activity_name}'")
        return []

    logger.debug(f"Найдено {len(matching_activities)} совпадающих видов деятельности")

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
        logger.info(f"Организации с видом деятельности '{activity_name}' не найдены")
        return []

    stmt = (
        select(Organization)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Organization.id.in_(org_ids))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()
    logger.info(f"Найдено {len(orgs)} организаций с видом деятельности '{activity_name}'")
    return orgs

async def list_in_rectangular_area(db: AsyncSession, center_lat: float, center_lon: float, width_m: float, height_m: float):
    """Найти организации в прямоугольной области относительно указанной точки на карте.

    Прямоугольник формируется вокруг центральной точки с заданными размерами.
    """
    logger.debug(f"Поиск организаций в прямоугольной области: lat={center_lat}, lon={center_lon}, width={width_m}м, height={height_m}м")
    
    DEGREES_PER_METER_LAT = 1.0 / 111000.0

    half_height_deg = (height_m / 2.0) * DEGREES_PER_METER_LAT
    half_width_deg = (width_m / 2.0) * DEGREES_PER_METER_LAT / math.cos(math.radians(center_lat))

    min_lat = center_lat - half_height_deg
    max_lat = center_lat + half_height_deg
    min_lon = center_lon - half_width_deg
    max_lon = center_lon + half_width_deg

    logger.debug(f"Границы области: lat=[{min_lat:.6f}, {max_lat:.6f}], lon=[{min_lon:.6f}, {max_lon:.6f}]")

    stmt = (
        select(Organization)
        .join(Organization.building)
        .options(joinedload(Organization.building), joinedload(Organization.phones), joinedload(Organization.activities))
        .where(Building.latitude.between(min_lat, max_lat))
        .where(Building.longitude.between(min_lon, max_lon))
        .order_by(Organization.id)
    )
    res = await db.execute(stmt)
    orgs = res.scalars().unique().all()
    logger.info(f"Найдено {len(orgs)} организаций в прямоугольной области")
    return orgs

async def create_org(db: AsyncSession, name: str, building_id: int, phone_numbers: list[str], activity_ids: list[int]):
    """Создать новую организацию с указанными телефонами и видами деятельности."""
    logger.info(f"Создание организации: name='{name}', building_id={building_id}")
    logger.debug(f"Телефоны: {phone_numbers}, Виды деятельности: {activity_ids}")
    
    org = Organization(name=name, building_id=building_id)
    db.add(org)
    await db.flush()
    logger.debug(f"Организация добавлена в БД: id={org.id}")

    for num in phone_numbers:
        db.add(Phone(number=num, organization_id=org.id))
    logger.debug(f"Добавлено {len(phone_numbers)} телефонов")

    if activity_ids:
        res = await db.execute(select(Activity).where(Activity.id.in_(activity_ids)))
        activities = res.scalars().all()
        await db.run_sync(lambda session: org.activities.extend(activities))
        logger.debug(f"Добавлено {len(activities)} видов деятельности")

    await db.commit()
    logger.info(f"Организация успешно создана: id={org.id}, name='{name}'")
    return await get_org(db, org.id)
