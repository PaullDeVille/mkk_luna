from sqlalchemy import Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Activity(Base):
    """Модель деятельности.

    - id: идентификатор вида деятельности
    - name: наименование вида деятельности
    - parent_id: идентификатор родительского вида деятельности (для дерева)
    - level: уровень вложенности в дереве (1–3)
    - parent: родительский объект вида деятельности
    - children: дочерние виды деятельности
    - organizations: организации, относящиеся к этому виду деятельности
    """

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 3", name="ck_activity_level_1_3"),
    )

    parent: Mapped["Activity | None"] = relationship(
        "Activity", remote_side="Activity.id", back_populates="children", lazy="selectin"
    )
    children: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="parent", cascade="all, delete-orphan", lazy="selectin"
    )

    organizations: Mapped[list["Organization"]] = relationship(
        "Organization",
        secondary="organization_activity",
        back_populates="activities",
        lazy="selectin"
    )
