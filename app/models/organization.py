from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

organization_activity = Table(
    "organization_activity",
    Base.metadata,
    Column("organization_id", ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
)

class Organization(Base):
    """Модель организации.

    - id: идентификатор организации
    - name: наименование организации
    - building_id: идентификатор здания, в котором расположена организация
    - building: связанный объект здания
    - phones: номера телефонов, привязанные к организации
    - activities: виды деятельности, которыми занимается организация
    """

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)

    building_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("buildings.id", ondelete="RESTRICT"), nullable=False
    )
    building: Mapped["Building"] = relationship("Building", back_populates="organizations", lazy="selectin")

    phones: Mapped[list["Phone"]] = relationship(
        "Phone", back_populates="organization", cascade="all, delete-orphan", lazy="selectin"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        secondary=organization_activity,
        back_populates="organizations",
        lazy="selectin"
    )
