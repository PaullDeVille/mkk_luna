from pydantic import BaseModel, Field

class BuildingOut(BaseModel):
    """Схема ответа для здания.

    - id: идентификатор здания
    - address: почтовый адрес здания
    - latitude: географическая широта здания
    - longitude: географическая долгота здания
    """

    id: int
    address: str
    latitude: float
    longitude: float
    model_config = {"from_attributes": True}

class BuildingCreate(BaseModel):
    """Схема создания здания.

    - address: почтовый адрес здания
    - latitude: географическая широта здания
    - longitude: географическая долгота здания
    """

    address: str = Field(..., examples=["г. Москва, ул. Ленина 1, офис 3"])
    latitude: float
    longitude: float
