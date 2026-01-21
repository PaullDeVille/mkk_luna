from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.building import Building

async def list_buildings(db: AsyncSession):
    """Получить список всех зданий, отсортированных по идентификатору."""
    res = await db.execute(select(Building).order_by(Building.id))
    return res.scalars().all()
