"""Тесты для CRUD операций с видами деятельности."""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.activity import create_activity, list_activities
from app.models.activity import Activity


@pytest.mark.crud
class TestActivityCRUD:
    """Тесты для CRUD операций видов деятельности."""

    async def test_create_root_activity(self, db_session: AsyncSession):
        """Тест создания корневого вида деятельности."""
        activity = await create_activity(db_session, "Еда", None)

        assert activity.id is not None
        assert activity.name == "Еда"
        assert activity.parent_id is None
        assert activity.level == 1

    async def test_create_child_activity(self, db_session: AsyncSession):
        """Тест создания дочернего вида деятельности."""
        parent = await create_activity(db_session, "Еда", None)
        child = await create_activity(db_session, "Мясная продукция", parent.id)

        assert child.id is not None
        assert child.name == "Мясная продукция"
        assert child.parent_id == parent.id
        assert child.level == 2

    async def test_create_activity_max_depth(self, db_session: AsyncSession):
        """Тест создания вида деятельности с максимальной глубиной."""
        level1 = await create_activity(db_session, "Уровень 1", None)
        level2 = await create_activity(db_session, "Уровень 2", level1.id)
        level3 = await create_activity(db_session, "Уровень 3", level2.id)

        assert level3.level == 3

        with pytest.raises(HTTPException) as exc_info:
            await create_activity(db_session, "Уровень 4", level3.id)

        assert exc_info.value.status_code == 400
        assert "Maximum activity depth is 3 levels" in str(exc_info.value.detail)

    async def test_create_activity_parent_not_found(self, db_session: AsyncSession):
        """Тест создания вида деятельности с несуществующим родителем."""
        with pytest.raises(HTTPException) as exc_info:
            await create_activity(db_session, "Test", 99999)

        assert exc_info.value.status_code == 404
        assert "Parent activity not found" in str(exc_info.value.detail)

    async def test_list_activities_empty(self, db_session: AsyncSession):
        """Тест получения пустого списка видов деятельности."""
        activities = await list_activities(db_session)
        assert activities == []

    async def test_list_activities(self, db_session: AsyncSession):
        """Тест получения списка видов деятельности."""
        food = await create_activity(db_session, "Еда", None)
        meat = await create_activity(db_session, "Мясная продукция", food.id)
        dairy = await create_activity(db_session, "Молочная продукция", food.id)
        services = await create_activity(db_session, "Услуги", None)

        activities = await list_activities(db_session)

        assert len(activities) == 4
        assert activities[0].level == 1
        assert activities[1].level == 1
        assert activities[2].level == 2
        assert activities[3].level == 2

    async def test_list_activities_ordering(self, db_session: AsyncSession):
        """Тест правильности сортировки видов деятельности."""
        level1_b = await create_activity(db_session, "Услуги", None)
        level1_a = await create_activity(db_session, "Еда", None)
        level2 = await create_activity(db_session, "Мясо", level1_a.id)

        activities = await list_activities(db_session)

        assert len(activities) == 3
        assert all(activities[i].level <= activities[i+1].level for i in range(len(activities)-1))
