"""Тесты для API endpoints организаций."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.building import Building
from app.crud.organization import create_org

@pytest.mark.api
class TestOrganizationsAPI:
    """Тесты для API endpoints /api/v1/organizations."""

    async def test_get_organization(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_organization
    ):
        """Тест получения организации по ID."""
        response = await client.get(
            f"/api/v1/organizations/{sample_organization.id}",
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_organization.id
        assert data["name"] == sample_organization.name
        assert "building" in data
        assert "phones" in data
        assert "activities" in data

    async def test_get_organization_not_found(self, client: AsyncClient, api_headers: dict):
        """Тест получения несуществующей организации."""
        response = await client.get("/api/v1/organizations/99999", headers=api_headers)

        assert response.status_code == 404
        assert "Organization not found" in response.json()["detail"]

    async def test_get_organization_unauthorized(
        self,
        client: AsyncClient,
        invalid_api_headers: dict,
        sample_organization
    ):
        """Тест доступа без авторизации."""
        response = await client.get(
            f"/api/v1/organizations/{sample_organization.id}",
            headers=invalid_api_headers
        )
        assert response.status_code == 403

    async def test_search_organizations_by_name(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_organization
    ):
        """Тест поиска организаций по названию."""
        response = await client.get(
            "/api/v1/organizations/search/by-name",
            params={"name": sample_organization.name},
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(org["id"] == sample_organization.id for org in data)

    async def test_search_organizations_by_name_partial(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест поиска по частичному совпадению."""
        await create_org(db_session, "Магазин Продукты", sample_building.id, [], [sample_activity.id])
        await create_org(db_session, "Магазин Одежда", sample_building.id, [], [sample_activity.id])
        await create_org(db_session, "Кафе", sample_building.id, [], [sample_activity.id])

        response = await client.get(
            "/api/v1/organizations/search/by-name",
            params={"name": "Магазин"},
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Магазин" in org["name"] for org in data)

    async def test_search_organizations_by_name_case_insensitive(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест поиска без учета регистра."""
        await create_org(db_session, "ТЕСТОВАЯ ОРГАНИЗАЦИЯ", sample_building.id, [], [sample_activity.id])

        response = await client.get(
            "/api/v1/organizations/search/by-name",
            params={"name": "тестовая"},
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_search_organizations_by_name_not_found(
        self,
        client: AsyncClient,
        api_headers: dict
    ):
        """Тест поиска без результатов."""
        response = await client.get(
            "/api/v1/organizations/search/by-name",
            params={"name": "НесуществующаяОрганизация12345"},
            headers=api_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_search_organizations_missing_param(
        self,
        client: AsyncClient,
        api_headers: dict
    ):
        """Тест поиска без обязательного параметра."""
        response = await client.get(
            "/api/v1/organizations/search/by-name",
            headers=api_headers
        )

        assert response.status_code == 422

    async def test_create_organization_minimal(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_building: Building
    ):
        """Тест создания организации с минимальными данными."""
        payload = {
            "name": "Новая организация",
            "building_id": sample_building.id,
            "phone_numbers": [],
            "activity_ids": []
        }

        response = await client.post("/api/v1/organizations", json=payload, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Новая организация"
        assert data["building"]["id"] == sample_building.id
        assert len(data["phones"]) == 0
        assert len(data["activities"]) == 0

    async def test_create_organization_full(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест создания организации со всеми данными."""
        payload = {
            "name": "Полная организация",
            "building_id": sample_building.id,
            "phone_numbers": ["+79991111111", "+79992222222"],
            "activity_ids": [sample_activity.id]
        }

        response = await client.post("/api/v1/organizations", json=payload, headers=api_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Полная организация"
        assert len(data["phones"]) == 2
        assert len(data["activities"]) == 1
        assert data["activities"][0]["id"] == sample_activity.id

    async def test_create_organization_unauthorized(
        self,
        client: AsyncClient,
        invalid_api_headers: dict,
        sample_building: Building
    ):
        """Тест создания без авторизации."""
        payload = {
            "name": "Тест",
            "building_id": sample_building.id,
            "phone_numbers": [],
            "activity_ids": []
        }

        response = await client.post("/api/v1/organizations", json=payload, headers=invalid_api_headers)
        assert response.status_code == 403

    async def test_orgs_in_rectangular_area(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession,
        sample_activity: Activity
    ):
        """Тест поиска организаций в прямоугольной области."""

        building_center = Building(address="Центр", latitude=55.751244, longitude=37.618423)
        building_nearby = Building(address="Рядом", latitude=55.752244, longitude=37.619423)
        building_far = Building(address="Далеко", latitude=55.800000, longitude=37.700000)

        db_session.add_all([building_center, building_nearby, building_far])
        await db_session.commit()
        await db_session.refresh(building_center)
        await db_session.refresh(building_nearby)
        await db_session.refresh(building_far)

        org1 = await create_org(db_session, "В центре", building_center.id, [], [sample_activity.id])
        org2 = await create_org(db_session, "Рядом", building_nearby.id, [], [sample_activity.id])
        org3 = await create_org(db_session, "Далеко", building_far.id, [], [sample_activity.id])

        response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            params={
                "lat": 55.751244,
                "lon": 37.618423,
                "width_m": 200,
                "height_m": 200
            },
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        org_ids = {org["id"] for org in data}
        assert org1.id in org_ids

    async def test_orgs_in_rectangular_area_empty(
        self,
        client: AsyncClient,
        api_headers: dict
    ):
        """Тест поиска в области без организаций."""
        response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            params={
                "lat": 0.0,
                "lon": 0.0,
                "width_m": 100,
                "height_m": 100
            },
            headers=api_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_orgs_in_rectangular_area_missing_params(
        self,
        client: AsyncClient,
        api_headers: dict
    ):
        """Тест поиска без обязательных параметров."""
        response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            headers=api_headers
        )

        assert response.status_code == 422

    async def test_orgs_in_rectangular_area_invalid_params(
        self,
        client: AsyncClient,
        api_headers: dict
    ):
        """Тест поиска с некорректными параметрами."""
        response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            params={
                "lat": 55.0,
                "lon": 37.0,
                "width_m": -100,
                "height_m": 100
            },
            headers=api_headers
        )

        assert response.status_code == 422

    async def test_orgs_in_rectangular_area_large_area(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession,
        sample_activity: Activity
    ):
        """Тест поиска в большой области."""
        buildings = [
            Building(address=f"Адрес {i}", latitude=55.75 + i*0.01, longitude=37.61 + i*0.01)
            for i in range(5)
        ]
        db_session.add_all(buildings)
        await db_session.commit()

        for building in buildings:
            await db_session.refresh(building)
            await create_org(db_session, f"Орг в {building.address}", building.id, [], [sample_activity.id])

        response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            params={
                "lat": 55.75,
                "lon": 37.61,
                "width_m": 5000,
                "height_m": 5000
            },
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_orgs_in_rectangular_area_unauthorized(
        self,
        client: AsyncClient,
        invalid_api_headers: dict
    ):
        """Тест доступа без авторизации."""
        response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            params={
                "lat": 55.0,
                "lon": 37.0,
                "width_m": 100,
                "height_m": 100
            },
            headers=invalid_api_headers
        )
        assert response.status_code == 403
