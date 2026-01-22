import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.activity import Activity

logger = logging.getLogger(__name__)

async def create_activity(db: AsyncSession, name: str, parent_id: int | None):
    """Создать новый вид деятельности с проверкой максимальной глубины вложенности (3 уровня)."""
    logger.info(f"Создание вида деятельности: name='{name}', parent_id={parent_id}")
    
    if parent_id is None:
        level = 1
        logger.debug(f"Создание корневого вида деятельности (level={level})")
    else:
        parent = await db.get(Activity, parent_id)
        if not parent:
            logger.error(f"Родительская деятельность не найдена: parent_id={parent_id}")
            raise HTTPException(404, detail="Parent activity not found")
        if parent.level >= 3:
            logger.warning(f"Превышена максимальная глубина вложенности: parent_level={parent.level}")
            raise HTTPException(400, detail="Maximum activity depth is 3 levels")
        level = parent.level + 1
        logger.debug(f"Создание дочернего вида деятельности (level={level}, parent='{parent.name}')")

    act = Activity(name=name, parent_id=parent_id, level=level)
    db.add(act)
    await db.commit()
    await db.refresh(act)
    logger.info(f"Вид деятельности успешно создан: id={act.id}, name='{act.name}', level={act.level}")
    return act

async def list_activities(db: AsyncSession):
    """Получить список всех видов деятельности, отсортированных по уровню и идентификатору."""
    logger.debug("Получение списка всех видов деятельности")
    res = await db.execute(select(Activity).order_by(Activity.level, Activity.id))
    activities = res.scalars().all()
    logger.info(f"Получено {len(activities)} видов деятельности")
    return activities
