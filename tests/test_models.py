"""Тесты для моделей данных."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.building import Building
from app.models.organization import Organization
from app.models.phone import Phone


@pytest.mark.unit
class TestModels:
    """Тесты для моделей SQLAlchemy."""

    async def test_activity_model(self, db_session: AsyncSession):
        """Тест модели Activity."""
        activity = Activity(name="Торговля", parent_id=None, level=1)
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        assert activity.id is not None
        assert activity.name == "Торговля"
        assert activity.parent_id is None
        assert activity.level == 1

    async def test_activity_hierarchy(self, db_session: AsyncSession):
        """Тест иерархии видов деятельности."""
        parent = Activity(name="Еда", parent_id=None, level=1)
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)
        
        child = Activity(name="Мясо", parent_id=parent.id, level=2)
        db_session.add(child)
        await db_session.commit()
        await db_session.refresh(child)
        
        assert child.parent_id == parent.id
        assert child.level == 2

    async def test_building_model(self, db_session: AsyncSession):
        """Тест модели Building."""
        building = Building(
            address="Тестовый адрес",
            latitude=55.751244,
            longitude=37.618423
        )
        db_session.add(building)
        await db_session.commit()
        await db_session.refresh(building)
        
        assert building.id is not None
        assert building.address == "Тестовый адрес"
        assert building.latitude == 55.751244
        assert building.longitude == 37.618423

    async def test_organization_model(
        self,
        db_session: AsyncSession,
        sample_building: Building
    ):
        """Тест модели Organization."""
        org = Organization(name="Тестовая организация", building_id=sample_building.id)
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        
        assert org.id is not None
        assert org.name == "Тестовая организация"
        assert org.building_id == sample_building.id

    async def test_phone_model(
        self,
        db_session: AsyncSession,
        sample_organization: Organization
    ):
        """Тест модели Phone."""
        phone = Phone(number="+79991234567", organization_id=sample_organization.id)
        db_session.add(phone)
        await db_session.commit()
        await db_session.refresh(phone)
        
        assert phone.id is not None
        assert phone.number == "+79991234567"
        assert phone.organization_id == sample_organization.id

    async def test_organization_relationships(
        self,
        db_session: AsyncSession,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест связей модели Organization."""
        org = Organization(name="Тест", building_id=sample_building.id)
        db_session.add(org)
        await db_session.flush()
        
        # Добавляем телефон
        phone = Phone(number="+79991234567", organization_id=org.id)
        db_session.add(phone)
        
        # Добавляем деятельность
        await db_session.run_sync(lambda session: org.activities.append(sample_activity))
        
        await db_session.commit()
        await db_session.refresh(org)
        
        assert org.building is not None
        assert org.building.id == sample_building.id
        assert len(org.phones) == 1
        assert org.phones[0].number == "+79991234567"
        assert len(org.activities) == 1
        assert org.activities[0].id == sample_activity.id

    async def test_cascade_delete_phones(
        self,
        db_session: AsyncSession,
        sample_organization: Organization
    ):
        """Тест каскадного удаления телефонов."""
        org_id = sample_organization.id
        
        # Добавляем телефон
        phone = Phone(number="+79991234567", organization_id=org_id)
        db_session.add(phone)
        await db_session.commit()
        
        # Удаляем организацию
        await db_session.delete(sample_organization)
        await db_session.commit()
        
        # Проверяем, что телефон тоже удалился
        from sqlalchemy import select
        result = await db_session.execute(select(Phone).where(Phone.organization_id == org_id))
        phones = result.scalars().all()
        assert len(phones) == 0
