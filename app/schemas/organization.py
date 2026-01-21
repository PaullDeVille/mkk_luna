from pydantic import BaseModel, Field
from typing import List

from app.schemas.building import BuildingOut
from app.schemas.activity import ActivityOut

class PhoneOut(BaseModel):
    """Схема номера телефона.

    - id: идентификатор телефонного номера
    - number: строковое представление телефонного номера
    """

    id: int
    number: str
    model_config = {"from_attributes": True}

class OrganizationOut(BaseModel):
    """Схема ответа для организации.

    - id: идентификатор организации
    - name: наименование организации
    - building: здание, в котором расположена организация
    - phones: список номеров телефонов организации
    - activities: список видов деятельности организации
    """

    id: int
    name: str
    building: BuildingOut
    phones: List[PhoneOut]
    activities: List[ActivityOut]
    model_config = {"from_attributes": True}

class OrganizationCreate(BaseModel):
    """Схема создания организации.

    - name: наименование организации
    - building_id: идентификатор здания, в котором расположена организация
    - phone_numbers: список телефонных номеров организации
    - activity_ids: список идентификаторов видов деятельности
    """

    name: str = Field(..., examples=['ООО "Рога и Копыта"'])
    building_id: int
    phone_numbers: List[str] = Field(default_factory=list, examples=[["2-222-222", "8-923-666-13-13"]])
    activity_ids: List[int] = Field(default_factory=list)
