"""Тесты для безопасности и утилит."""
import pytest
from httpx import AsyncClient

from app.models.building import Building
from app.crud.organization import create_org

@pytest.mark.unit
class TestSecurity:
    """Тесты для проверки безопасности API."""

    async def test_api_key_valid(self, client: AsyncClient, api_headers: dict):
        """Тест доступа с валидным API ключом."""
        response = await client.get("/api/v1/activities", headers=api_headers)
        assert response.status_code == 200

    async def test_api_key_invalid(self, client: AsyncClient, invalid_api_headers: dict):
        """Тест доступа с невалидным API ключом."""
        response = await client.get("/api/v1/activities", headers=invalid_api_headers)
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    async def test_api_key_missing(self, client: AsyncClient):
        """Тест доступа без API ключа."""
        response = await client.get("/api/v1/activities")
        assert response.status_code == 422

    async def test_api_key_empty(self, client: AsyncClient):
        """Тест доступа с пустым API ключом."""
        response = await client.get("/api/v1/activities", headers={"X-API-KEY": ""})
        assert response.status_code == 403

    async def test_all_endpoints_require_auth(self, client: AsyncClient, invalid_api_headers: dict):
        """Тест что все эндпоинты требуют авторизации."""
        endpoints = [
            "/api/v1/activities",
            "/api/v1/buildings",
            "/api/v1/organizations/search/by-name?name=test"
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint, headers=invalid_api_headers)
            assert response.status_code == 403, f"Endpoint {endpoint} should require auth"


@pytest.mark.unit
class TestHealthCheck:
    """Тесты для health check endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Тест health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    async def test_health_check_no_auth_required(self, client: AsyncClient):
        """Тест что health check не требует авторизации."""
        response = await client.get("/health")
        assert response.status_code == 200


@pytest.mark.integration
class TestIntegration:
    """Интеграционные тесты."""

    async def test_full_workflow_create_and_search(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session,
        sample_building,
        sample_activity
    ):
        """Тест полного workflow: создание и поиск организации."""
        create_payload = {
            "name": "Тестовая организация для workflow",
            "building_id": sample_building.id,
            "phone_numbers": ["+79991234567"],
            "activity_ids": [sample_activity.id]
        }

        create_response = await client.post(
            "/api/v1/organizations",
            json=create_payload,
            headers=api_headers
        )
        assert create_response.status_code == 201
        created_org = create_response.json()
        org_id = created_org["id"]

        get_response = await client.get(
            f"/api/v1/organizations/{org_id}",
            headers=api_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == org_id

        search_response = await client.get(
            "/api/v1/organizations/search/by-name",
            params={"name": "Тестовая организация"},
            headers=api_headers
        )
        assert search_response.status_code == 200
        assert any(org["id"] == org_id for org in search_response.json())

        building_response = await client.get(
            f"/api/v1/buildings/{sample_building.id}/organizations",
            headers=api_headers
        )
        assert building_response.status_code == 200
        assert any(org["id"] == org_id for org in building_response.json())

        activity_response = await client.get(
            f"/api/v1/activities/{sample_activity.id}/organizations",
            headers=api_headers
        )
        assert activity_response.status_code == 200
        assert any(org["id"] == org_id for org in activity_response.json())

    async def test_activity_hierarchy_workflow(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session,
        sample_building
    ):
        """Тест workflow с иерархией видов деятельности."""
        root_payload = {"name": "Еда", "parent_id": None}
        root_response = await client.post(
            "/api/v1/activities",
            json=root_payload,
            headers=api_headers
        )
        assert root_response.status_code == 201
        root_id = root_response.json()["id"]

        child_payload = {"name": "Мясо", "parent_id": root_id}
        child_response = await client.post(
            "/api/v1/activities",
            json=child_payload,
            headers=api_headers
        )
        assert child_response.status_code == 201
        child_id = child_response.json()["id"]

        org_payload = {
            "name": "Мясной магазин",
            "building_id": sample_building.id,
            "phone_numbers": ["+79991234567"],
            "activity_ids": [child_id]
        }
        org_response = await client.post(
            "/api/v1/organizations",
            json=org_payload,
            headers=api_headers
        )
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]

        parent_search_response = await client.get(
            f"/api/v1/activities/{root_id}/organizations",
            headers=api_headers
        )
        assert parent_search_response.status_code == 200
        assert any(org["id"] == org_id for org in parent_search_response.json())

        child_search_response = await client.get(
            f"/api/v1/activities/{child_id}/organizations",
            headers=api_headers
        )
        assert child_search_response.status_code == 200
        assert any(org["id"] == org_id for org in child_search_response.json())

    async def test_geo_search_workflow(
        self,
        client: AsyncClient,
        api_headers: dict,
        db_session,
        sample_activity
    ):
        """Тест workflow геопоиска."""


        building = Building(
            address="Красная площадь, 1",
            latitude=55.753215,
            longitude=37.622504
        )
        db_session.add(building)
        await db_session.commit()
        await db_session.refresh(building)

        org = await create_org(
            db_session,
            "Исторический музей",
            building.id,
            ["+74951234567"],
            [sample_activity.id]
        )

        response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            params={
                "lat": 55.753215,
                "lon": 37.622504,
                "width_m": 500,
                "height_m": 500
            },
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert any(o["id"] == org.id for o in data)

        far_response = await client.get(
            "/api/v1/organizations/geo/rectangular-area",
            params={
                "lat": 56.0,
                "lon": 38.0,
                "width_m": 100,
                "height_m": 100
            },
            headers=api_headers
        )

        assert far_response.status_code == 200
        far_data = far_response.json()
        assert not any(o["id"] == org.id for o in far_data)


@pytest.mark.unit
class TestErrorHandling:
    """Тесты обработки ошибок."""

    async def test_404_not_found(self, client: AsyncClient):
        """Тест несуществующего endpoint."""
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    async def test_method_not_allowed(self, client: AsyncClient, api_headers: dict):
        """Тест недопустимого HTTP метода."""
        response = await client.put("/api/v1/activities", headers=api_headers)
        assert response.status_code in [404, 405]

    async def test_invalid_json(self, client: AsyncClient, api_headers: dict, sample_building):
        """Тест с некорректным JSON."""
        response = await client.post(
            "/api/v1/organizations",
            content="not a json",
            headers={**api_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422

    async def test_missing_required_fields(self, client: AsyncClient, api_headers: dict):
        """Тест с отсутствующими обязательными полями."""
        response = await client.post(
            "/api/v1/organizations",
            json={},
            headers=api_headers
        )
        assert response.status_code == 422

    async def test_invalid_field_types(self, client: AsyncClient, api_headers: dict):
        """Тест с некорректными типами полей."""
        response = await client.post(
            "/api/v1/organizations",
            json={
                "name": "Test",
                "building_id": "not_a_number",
                "phone_numbers": [],
                "activity_ids": []
            },
            headers=api_headers
        )
        assert response.status_code == 422
