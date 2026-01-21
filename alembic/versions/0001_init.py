"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-01-21

"""

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
    )
    op.create_index("ix_buildings_address", "buildings", ["address"])

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.CheckConstraint("level >= 1 AND level <= 3", name="ck_activity_level_1_3"),
    )
    op.create_index("ix_activities_name", "activities", ["name"])

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("building_id", sa.Integer(), sa.ForeignKey("buildings.id", ondelete="RESTRICT"), nullable=False),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"])

    op.create_table(
        "phones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_index("ix_phones_number", "phones", ["number"])

    op.create_table(
        "organization_activity",
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    )

def downgrade() -> None:
    op.drop_table("organization_activity")
    op.drop_index("ix_phones_number", table_name="phones")
    op.drop_table("phones")
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")
    op.drop_index("ix_activities_name", table_name="activities")
    op.drop_table("activities")
    op.drop_index("ix_buildings_address", table_name="buildings")
    op.drop_table("buildings")
