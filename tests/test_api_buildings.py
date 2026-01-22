"""Тесты для API endpoints зданий."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.building import Building


@pytest.mark.api
class TestBuildingsAPI:
    """Тесты для API endpoints /api/v1/buildings."""

    async def test_get_buildings_empty(self, client: AsyncClient, api_headers: dict):
        """Тест получения пустого списка зданий."""
        response = await client.get("/api/v1/buildings", headers=api_headers)
        
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_buildings(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_building: Building
    ):
        """Тест получения списка зданий."""
        response = await client.get("/api/v1/buildings", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_building.id
        assert data[0]["address"] == sample_building.address
        assert data[0]["latitude"] == sample_building.latitude
        assert data[0]["longitude"] == sample_building.longitude

    async def test_get_buildings_unauthorized(self, client: AsyncClient, invalid_api_headers: dict):
        """Тест доступа без авторизации."""
        response = await client.get("/api/v1/buildings", headers=invalid_api_headers)
        assert response.status_code == 403

    async def test_get_buildings_multiple(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession
    ):
        """Тест получения списка нескольких зданий."""
        # Создаем несколько зданий
        buildings = [
            Building(address="Адрес 1", latitude=55.0, longitude=37.0),
            Building(address="Адрес 2", latitude=55.1, longitude=37.1),
            Building(address="Адрес 3", latitude=55.2, longitude=37.2)
        ]
        db_session.add_all(buildings)
        await db_session.commit()
        
        response = await client.get("/api/v1/buildings", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_get_organizations_in_building(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_organization
    ):
        """Тест получения организаций в здании."""
        building_id = sample_organization.building_id
        
        response = await client.get(
            f"/api/v1/buildings/{building_id}/organizations",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(org["id"] == sample_organization.id for org in data)

    async def test_get_organizations_in_building_empty(
        self,
        client: AsyncClient,
        api_headers: dict,
        sample_building: Building
    ):
        """Тест получения организаций в пустом здании."""
        response = await client.get(
            f"/api/v1/buildings/{sample_building.id}/organizations",
            headers=api_headers
        )
        
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_organizations_in_building_multiple(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity
    ):
        """Тест получения нескольких организаций в здании."""
        from app.crud.organization import create_org
        
        # Создаем несколько организаций в одном здании
        org1 = await create_org(db_session, "Орг 1", sample_building.id, [], [sample_activity.id])
        org2 = await create_org(db_session, "Орг 2", sample_building.id, [], [sample_activity.id])
        org3 = await create_org(db_session, "Орг 3", sample_building.id, [], [sample_activity.id])
        
        response = await client.get(
            f"/api/v1/buildings/{sample_building.id}/organizations",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        org_ids = {org["id"] for org in data}
        assert org1.id in org_ids
        assert org2.id in org_ids
        assert org3.id in org_ids

    async def test_get_organizations_in_building_unauthorized(
        self,
        client: AsyncClient,
        invalid_api_headers: dict,
        sample_building: Building
    ):
        """Тест доступа без авторизации."""
        response = await client.get(
            f"/api/v1/buildings/{sample_building.id}/organizations",
            headers=invalid_api_headers
        )
        assert response.status_code == 403
