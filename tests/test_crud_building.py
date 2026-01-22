"""Тесты для CRUD операций с зданиями."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.building import list_buildings
from app.models.building import Building


@pytest.mark.crud
class TestBuildingCRUD:
    """Тесты для CRUD операций зданий."""

    async def test_list_buildings_empty(self, db_session: AsyncSession):
        """Тест получения пустого списка зданий."""
        buildings = await list_buildings(db_session)
        assert buildings == []

    async def test_list_buildings(self, db_session: AsyncSession):
        """Тест получения списка зданий."""
        building1 = Building(
            address="ул. Ленина, 1",
            latitude=55.751244,
            longitude=37.618423
        )
        building2 = Building(
            address="ул. Пушкина, 2",
            latitude=55.755819,
            longitude=37.617644
        )
        building3 = Building(
            address="пр. Мира, 3",
            latitude=55.783315,
            longitude=37.623783
        )

        db_session.add_all([building1, building2, building3])
        await db_session.commit()

        buildings = await list_buildings(db_session)

        assert len(buildings) == 3
        assert all(isinstance(b, Building) for b in buildings)
        assert buildings[0].id < buildings[1].id < buildings[2].id

    async def test_list_buildings_with_fixture(self, db_session: AsyncSession, sample_building: Building):
        """Тест получения списка зданий с использованием фикстуры."""
        buildings = await list_buildings(db_session)

        assert len(buildings) == 1
        assert buildings[0].id == sample_building.id
        assert buildings[0].address == sample_building.address
        assert buildings[0].latitude == sample_building.latitude
        assert buildings[0].longitude == sample_building.longitude
