from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.activity import Activity

async def create_activity(db: AsyncSession, name: str, parent_id: int | None):
    """Создать новый вид деятельности с проверкой максимальной глубины вложенности (3 уровня)."""
    if parent_id is None:
        level = 1
    else:
        parent = await db.get(Activity, parent_id)
        if not parent:
            raise HTTPException(404, detail="Parent activity not found")
        if parent.level >= 3:
            raise HTTPException(400, detail="Maximum activity depth is 3 levels")
        level = parent.level + 1

    act = Activity(name=name, parent_id=parent_id, level=level)
    db.add(act)
    await db.commit()
    await db.refresh(act)
    return act

async def list_activities(db: AsyncSession):
    """Получить список всех видов деятельности, отсортированных по уровню и идентификатору."""
    res = await db.execute(select(Activity).order_by(Activity.level, Activity.id))
    return res.scalars().all()
