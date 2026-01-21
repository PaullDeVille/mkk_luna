from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Phone(Base):
    """Модель номера телефона.

    - id: идентификатор телефонного номера
    - number: строковое представление телефонного номера
    - organization_id: идентификатор организации-владельца номера
    - organization: связанный объект организации
    """

    __tablename__ = "phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String, nullable=False, index=True)

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    organization: Mapped["Organization"] = relationship("Organization", back_populates="phones")
