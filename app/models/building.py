from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Building(Base):
    """Модель здания.

    - id: идентификатор здания
    - address: почтовый адрес здания
    - latitude: географическая широта здания
    - longitude: географическая долгота здания
    - organizations: организации, расположенные в этом здании
    """

    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String, nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    organizations: Mapped[list["Organization"]] = relationship(
        "Organization", back_populates="building", cascade="all, delete-orphan"
    )
