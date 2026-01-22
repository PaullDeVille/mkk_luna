"""Тесты для API endpoints видов деятельности."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.organization import create_org
from app.models.activity import Activity
from app.models.building import Building


@pytest.mark.api
class TestActivitiesAPI:
    """Тесты для API endpoints /api/v1/activities."""

    async def test_get_activities_empty(self, client: AsyncClient, api_headers: dict):
        """Тест получения пустого списка видов деятельности."""
        response = await client.get("/api/v1/activities", headers=api_headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_get_activities(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession
    ):
        """Тест получения списка видов деятельности."""
        activity1 = Activity(name="Еда", parent_id=None, level=1)
        activity2 = Activity(name="Услуги", parent_id=None, level=1)
        db_session.add_all([activity1, activity2])
        await db_session.commit()

        response = await client.get("/api/v1/activities", headers=api_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in item for item in data)
        assert all("name" in item for item in data)

    async def test_get_activities_unauthorized(self, client: AsyncClient, invalid_api_headers: dict):
        """Тест доступа без авторизации."""
        response = await client.get("/api/v1/activities", headers=invalid_api_headers)
        assert response.status_code == 403

    async def test_create_activity_root(self, client: AsyncClient, api_headers: dict):
        """Тест создания корневого вида деятельности."""
        payload = {
            "name": "Торговля",
            "parent_id": None
        }

        response = await client.post("/api/v1/activities", json=payload, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Торговля"
        assert data["parent_id"] is None
        assert data["level"] == 1
        assert "id" in data

    async def test_create_activity_child(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession
    ):
        """Тест создания дочернего вида деятельности."""
        parent = Activity(name="Еда", parent_id=None, level=1)
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        payload = {
            "name": "Мясная продукция",
            "parent_id": parent.id
        }

        response = await client.post("/api/v1/activities", json=payload, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Мясная продукция"
        assert data["parent_id"] == parent.id
        assert data["level"] == 2

    async def test_create_activity_max_depth_exceeded(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession
    ):
        """Тест превышения максимальной глубины."""
        level1 = Activity(name="Уровень 1", parent_id=None, level=1)
        db_session.add(level1)
        await db_session.commit()
        await db_session.refresh(level1)

        level2 = Activity(name="Уровень 2", parent_id=level1.id, level=2)
        db_session.add(level2)
        await db_session.commit()
        await db_session.refresh(level2)

        level3 = Activity(name="Уровень 3", parent_id=level2.id, level=3)
        db_session.add(level3)
        await db_session.commit()
        await db_session.refresh(level3)

        payload = {
            "name": "Уровень 4",
            "parent_id": level3.id
        }

        response = await client.post("/api/v1/activities", json=payload, headers=api_headers)

        assert response.status_code == 400
        assert "Maximum activity depth" in response.json()["detail"]

    async def test_create_activity_parent_not_found(self, client: AsyncClient, api_headers: dict):
        """Тест создания с несуществующим родителем."""
        payload = {
            "name": "Тест",
            "parent_id": 99999
        }

        response = await client.post("/api/v1/activities", json=payload, headers=api_headers)

        assert response.status_code == 404
        assert "Parent activity not found" in response.json()["detail"]

    async def test_get_organizations_by_activity(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_organization
    ):
        """Тест получения организаций по виду деятельности."""
        activity_id = sample_organization.activities[0].id

        response = await client.get(
            f"/api/v1/activities/{activity_id}/organizations",
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(org["id"] == sample_organization.id for org in data)

    async def test_get_organizations_by_activity_with_descendants(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест получения организаций по деятельности с дочерними."""
        food = Activity(name="Еда", parent_id=None, level=1)
        db_session.add(food)
        await db_session.commit()
        await db_session.refresh(food)

        meat = Activity(name="Мясо", parent_id=food.id, level=2)
        db_session.add(meat)
        await db_session.commit()
        await db_session.refresh(meat)

        org1 = await create_org(db_session, "Продуктовый", sample_building.id, [], [food.id])
        org2 = await create_org(db_session, "Мясной", sample_building.id, [], [meat.id])

        response = await client.get(
            f"/api/v1/activities/{food.id}/organizations",
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_search_organizations_by_activity_name(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест поиска организаций по названию вида деятельности."""
        activity = Activity(name="Торговля", parent_id=None, level=1)
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)

        await create_org(db_session, "Магазин", sample_building.id, [], [activity.id])

        response = await client.get(
            "/api/v1/activities/search/by-name/organizations",
            params={"name": "Торговля"},
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_search_organizations_by_activity_name_not_found(
        self,
        client: AsyncClient,
        api_headers: dict
    ):
        """Тест поиска по несуществующему названию."""
        response = await client.get(
            "/api/v1/activities/search/by-name/organizations",
            params={"name": "НесуществующаяДеятельность"},
            headers=api_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_search_organizations_by_activity_name_missing_param(
        self,
        client: AsyncClient,
        api_headers: dict
    ):
        """Тест поиска без обязательного параметра."""
        response = await client.get(
            "/api/v1/activities/search/by-name/organizations",
            headers=api_headers
        )

        assert response.status_code == 422
