from pydantic import BaseModel


class ControlSchema(BaseModel):
    id: str
    name: str
    description: str
    family: str
    weight: float


class FrameworkListItem(BaseModel):
    id: str
    name: str
    version: str
    control_count: int
    families: list[str]


class FrameworkControls(BaseModel):
    id: str
    name: str
    version: str
    controls: list[ControlSchema]
