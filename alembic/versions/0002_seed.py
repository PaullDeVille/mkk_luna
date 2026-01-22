"""seed test data

Revision ID: 0002_seed
Revises: 0001_init
Create Date: 2026-01-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_seed"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO buildings (id, address, latitude, longitude) VALUES
        (1, 'г. Москва, ул. Ленина 1, офис 3', 55.7558, 37.6173),
        (2, 'г. Москва, ул. Блюхера, 32/1', 55.7600, 37.6200),
        (3, 'г. Москва, пр-т Мира, 10', 99.7700, 37.6400)
        ON CONFLICT (id) DO NOTHING;
    """))

    op.execute(sa.text("""
        INSERT INTO activities (id, name, parent_id, level) VALUES
        (1, 'Еда', NULL, 1),
        (2, 'Мясная продукция', 1, 2),
        (3, 'Молочная продукция', 1, 2),
        (4, 'Автомобили', NULL, 1),
        (5, 'Грузовые', 4, 2),
        (6, 'Легковые', 4, 2),
        (7, 'Запчасти', 6, 3),
        (8, 'Аксессуары', 6, 3)
        ON CONFLICT (id) DO NOTHING;
    """))

    op.execute(sa.text("""
        INSERT INTO organizations (id, name, building_id) VALUES
        (1, 'ООО "Рога и Копыта"', 2),
        (2, 'Мясной Двор', 1),
        (3, 'Молоко и Ко', 1),
        (4, 'АвтоМир', 3)
        ON CONFLICT (id) DO NOTHING;
    """))

    op.execute(sa.text("""
        INSERT INTO phones (id, number, organization_id) VALUES
        (1, '2-222-222', 1),
        (2, '3-333-333', 1),
        (3, '8-923-666-13-13', 1),
        (4, '8-999-111-22-33', 2),
        (5, '8-999-444-55-66', 3),
        (6, '8-800-555-35-35', 4)
        ON CONFLICT (id) DO NOTHING;
    """))

    op.execute(sa.text("""
        INSERT INTO organization_activity (organization_id, activity_id) VALUES
        (1, 2),
        (1, 3),
        (2, 2),
        (3, 3),
        (4, 7),
        (4, 8)
        ON CONFLICT DO NOTHING;
    """))

    # Сброс sequences после вставки данных с явными ID
    op.execute(sa.text("SELECT setval('buildings_id_seq', (SELECT COALESCE(MAX(id), 1) FROM buildings));"))
    op.execute(sa.text("SELECT setval('activities_id_seq', (SELECT COALESCE(MAX(id), 1) FROM activities));"))
    op.execute(sa.text("SELECT setval('organizations_id_seq', (SELECT COALESCE(MAX(id), 1) FROM organizations));"))
    op.execute(sa.text("SELECT setval('phones_id_seq', (SELECT COALESCE(MAX(id), 1) FROM phones));"))

def downgrade() -> None:
    op.execute(sa.text("DELETE FROM organization_activity;"))
    op.execute(sa.text("DELETE FROM phones;"))
    op.execute(sa.text("DELETE FROM organizations;"))
    op.execute(sa.text("DELETE FROM activities;"))
    op.execute(sa.text("DELETE FROM buildings;"))
