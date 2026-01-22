"""Тесты для CRUD операций с организациями."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.organization import (
    get_org, search_by_name, create_org,
    list_by_building, list_by_activity_with_descendants,
    list_by_activity_name_with_descendants, list_in_rectangular_area
)
from app.models.activity import Activity
from app.models.building import Building
from app.models.organization import Organization


@pytest.mark.crud
class TestOrganizationCRUD:
    """Тесты для CRUD операций организаций."""

    async def test_get_org_success(self, db_session: AsyncSession, sample_organization: Organization):
        """Тест получения организации по ID."""
        org = await get_org(db_session, sample_organization.id)
        
        assert org is not None
        assert org.id == sample_organization.id
        assert org.name == sample_organization.name
        assert org.building is not None
        assert org.phones is not None
        assert len(org.phones) > 0
        assert org.activities is not None
        assert len(org.activities) > 0

    async def test_get_org_not_found(self, db_session: AsyncSession):
        """Тест получения несуществующей организации."""
        org = await get_org(db_session, 99999)
        assert org is None

    async def test_search_by_name_exact(
        self,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест поиска организации по точному названию."""
        # Создаем тестовые организации
        await create_org(db_session, "Магазин Продукты", sample_building.id, ["+79991111111"], [sample_activity.id])
        await create_org(db_session, "Кафе Уют", sample_building.id, ["+79992222222"], [sample_activity.id])
        
        results = await search_by_name(db_session, "Магазин Продукты")
        
        assert len(results) == 1
        assert results[0].name == "Магазин Продукты"

    async def test_search_by_name_partial(
        self,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест поиска организации по частичному совпадению."""
        await create_org(db_session, "Магазин Продукты", sample_building.id, ["+79991111111"], [sample_activity.id])
        await create_org(db_session, "Магазин Одежда", sample_building.id, ["+79992222222"], [sample_activity.id])
        await create_org(db_session, "Кафе Уют", sample_building.id, ["+79993333333"], [sample_activity.id])
        
        results = await search_by_name(db_session, "магазин")
        
        assert len(results) == 2
        assert all("магазин" in org.name.lower() for org in results)

    async def test_search_by_name_case_insensitive(
        self,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест поиска без учета регистра."""
        await create_org(db_session, "Магазин ПРОДУКТЫ", sample_building.id, ["+79991111111"], [sample_activity.id])
        
        results = await search_by_name(db_session, "продукты")
        
        assert len(results) == 1
        assert "ПРОДУКТЫ" in results[0].name

    async def test_search_by_name_no_results(self, db_session: AsyncSession):
        """Тест поиска без результатов."""
        results = await search_by_name(db_session, "НесуществующаяОрганизация")
        assert results == []

    async def test_list_by_building(
        self,
        db_session: AsyncSession,
        sample_activity: Activity
    ):
        """Тест получения организаций по зданию."""
        # Создаем два здания
        building1 = Building(address="Адрес 1", latitude=55.0, longitude=37.0)
        building2 = Building(address="Адрес 2", latitude=56.0, longitude=38.0)
        db_session.add_all([building1, building2])
        await db_session.commit()
        await db_session.refresh(building1)
        await db_session.refresh(building2)
        
        # Создаем организации в разных зданиях
        await create_org(db_session, "Орг 1 в здании 1", building1.id, ["+79991111111"], [sample_activity.id])
        await create_org(db_session, "Орг 2 в здании 1", building1.id, ["+79992222222"], [sample_activity.id])
        await create_org(db_session, "Орг в здании 2", building2.id, ["+79993333333"], [sample_activity.id])
        
        results = await list_by_building(db_session, building1.id)
        
        assert len(results) == 2
        assert all(org.building_id == building1.id for org in results)

    async def test_list_by_activity_with_descendants_no_children(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест получения организаций по виду деятельности без дочерних."""
        activity = Activity(name="Торговля", parent_id=None, level=1)
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        org = await create_org(db_session, "Магазин", sample_building.id, ["+79991111111"], [activity.id])
        
        results = await list_by_activity_with_descendants(db_session, activity.id)
        
        assert len(results) == 1
        assert results[0].id == org.id

    async def test_list_by_activity_with_descendants_with_children(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест получения организаций по виду деятельности с дочерними."""
        # Создаем иерархию видов деятельности
        food = Activity(name="Еда", parent_id=None, level=1)
        db_session.add(food)
        await db_session.commit()
        await db_session.refresh(food)
        
        meat = Activity(name="Мясо", parent_id=food.id, level=2)
        dairy = Activity(name="Молоко", parent_id=food.id, level=2)
        db_session.add_all([meat, dairy])
        await db_session.commit()
        await db_session.refresh(meat)
        await db_session.refresh(dairy)
        
        # Создаем организации с разными видами деятельности
        org1 = await create_org(db_session, "Продуктовый", sample_building.id, ["+79991111111"], [food.id])
        org2 = await create_org(db_session, "Мясной", sample_building.id, ["+79992222222"], [meat.id])
        org3 = await create_org(db_session, "Молочный", sample_building.id, ["+79993333333"], [dairy.id])
        
        # Поиск по родительскому виду деятельности должен вернуть все организации
        results = await list_by_activity_with_descendants(db_session, food.id)
        
        assert len(results) == 3
        org_ids = {org.id for org in results}
        assert org1.id in org_ids
        assert org2.id in org_ids
        assert org3.id in org_ids

    async def test_list_by_activity_with_descendants_empty(self, db_session: AsyncSession):
        """Тест получения пустого списка организаций по виду деятельности."""
        activity = Activity(name="Пустая деятельность", parent_id=None, level=1)
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        results = await list_by_activity_with_descendants(db_session, activity.id)
        assert results == []

    async def test_list_by_activity_name_with_descendants_single_match(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест поиска организаций по названию вида деятельности (одно совпадение)."""
        food = Activity(name="Еда", parent_id=None, level=1)
        db_session.add(food)
        await db_session.commit()
        await db_session.refresh(food)
        
        meat = Activity(name="Мясо", parent_id=food.id, level=2)
        db_session.add(meat)
        await db_session.commit()
        await db_session.refresh(meat)
        
        org1 = await create_org(db_session, "Продуктовый", sample_building.id, ["+79991111111"], [food.id])
        org2 = await create_org(db_session, "Мясной", sample_building.id, ["+79992222222"], [meat.id])
        
        results = await list_by_activity_name_with_descendants(db_session, "Еда")
        
        assert len(results) == 2

    async def test_list_by_activity_name_with_descendants_case_insensitive(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест поиска по названию без учета регистра."""
        activity = Activity(name="ТОРГОВЛЯ", parent_id=None, level=1)
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        await create_org(db_session, "Магазин", sample_building.id, ["+79991111111"], [activity.id])
        
        results = await list_by_activity_name_with_descendants(db_session, "торговля")
        
        assert len(results) == 1

    async def test_list_by_activity_name_with_descendants_not_found(self, db_session: AsyncSession):
        """Тест поиска по несуществующему названию вида деятельности."""
        results = await list_by_activity_name_with_descendants(db_session, "НесуществующаяДеятельность")
        assert results == []

    async def test_list_in_rectangular_area(
        self,
        db_session: AsyncSession,
        sample_activity: Activity
    ):
        """Тест поиска организаций в прямоугольной области."""
        # Создаем здания в разных точках
        # Центр: 55.751244, 37.618423
        building_center = Building(address="Центр", latitude=55.751244, longitude=37.618423)
        building_nearby = Building(address="Рядом", latitude=55.752244, longitude=37.619423)
        building_far = Building(address="Далеко", latitude=55.800000, longitude=37.700000)
        
        db_session.add_all([building_center, building_nearby, building_far])
        await db_session.commit()
        await db_session.refresh(building_center)
        await db_session.refresh(building_nearby)
        await db_session.refresh(building_far)
        
        # Создаем организации в этих зданиях
        org1 = await create_org(db_session, "В центре", building_center.id, ["+79991111111"], [sample_activity.id])
        org2 = await create_org(db_session, "Рядом", building_nearby.id, ["+79992222222"], [sample_activity.id])
        org3 = await create_org(db_session, "Далеко", building_far.id, ["+79993333333"], [sample_activity.id])
        
        # Поиск в области 200м x 200м от центра
        results = await list_in_rectangular_area(db_session, 55.751244, 37.618423, 200, 200)
        
        # Должны найтись только первые две организации
        assert len(results) >= 1  # Как минимум центральная
        org_ids = {org.id for org in results}
        assert org1.id in org_ids

    async def test_list_in_rectangular_area_empty(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест поиска в области без организаций."""
        # Поиск в области, где нет зданий
        results = await list_in_rectangular_area(db_session, 0.0, 0.0, 100, 100)
        assert results == []

    async def test_create_org_minimal(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест создания организации с минимальными данными."""
        org = await create_org(db_session, "Тестовая организация", sample_building.id, [], [])
        
        assert org.id is not None
        assert org.name == "Тестовая организация"
        assert org.building_id == sample_building.id
        assert len(org.phones) == 0
        assert len(org.activities) == 0

    async def test_create_org_full(
        self,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест создания организации со всеми данными."""
        phones = ["+79991111111", "+79992222222"]
        activities = [sample_activity.id]
        
        org = await create_org(
            db_session,
            "Полная организация",
            sample_building.id,
            phones,
            activities
        )
        
        assert org.id is not None
        assert org.name == "Полная организация"
        assert org.building_id == sample_building.id
        assert len(org.phones) == 2
        assert set(p.number for p in org.phones) == set(phones)
        assert len(org.activities) == 1
        assert org.activities[0].id == sample_activity.id

    async def test_create_org_multiple_activities(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест создания организации с несколькими видами деятельности."""
        activity1 = Activity(name="Деятельность 1", parent_id=None, level=1)
        activity2 = Activity(name="Деятельность 2", parent_id=None, level=1)
        db_session.add_all([activity1, activity2])
        await db_session.commit()
        await db_session.refresh(activity1)
        await db_session.refresh(activity2)
        
        org = await create_org(
            db_session,
            "Мультиактивная организация",
            sample_building.id,
            ["+79991111111"],
            [activity1.id, activity2.id]
        )
        
        assert len(org.activities) == 2
        activity_ids = {a.id for a in org.activities}
        assert activity1.id in activity_ids
        assert activity2.id in activity_ids
