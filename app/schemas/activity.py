from pydantic import BaseModel, Field
from typing import Optional, List

class ActivityOut(BaseModel):
    """Схема ответа для вида деятельности.

    - id: идентификатор вида деятельности
    - name: наименование вида деятельности
    - parent_id: идентификатор родительского вида деятельности
    - level: уровень вложенности в дереве (1–3)
    """

    id: int
    name: str
    parent_id: Optional[int] = None
    level: int
    model_config = {"from_attributes": True}

class ActivityCreate(BaseModel):
    """Схема создания вида деятельности.

    - name: наименование вида деятельности
    - parent_id: идентификатор родительского вида деятельности (для дерева)
    """

    name: str = Field(..., examples=["Еда"])
    parent_id: Optional[int] = None

class ActivityTreeNode(BaseModel):
    """Схема узла дерева деятельностей.

    - id: идентификатор вида деятельности
    - name: наименование вида деятельности
    - level: уровень вложенности в дереве (1–3)
    - children: список дочерних узлов
    """

    id: int
    name: str
    level: int
    children: List["ActivityTreeNode"] = []
    model_config = {"from_attributes": True}

ActivityTreeNode.model_rebuild()
