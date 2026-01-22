import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.building import Building

logger = logging.getLogger(__name__)

async def list_buildings(db: AsyncSession):
    """Получить список всех зданий, отсортированных по идентификатору."""
    logger.debug("Получение списка всех зданий")
    res = await db.execute(select(Building).order_by(Building.id))
    buildings = res.scalars().all()
    logger.info(f"Получено {len(buildings)} зданий")
    return buildings
