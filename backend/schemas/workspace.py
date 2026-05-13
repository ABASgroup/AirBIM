from pydantic import BaseModel
from models.workspace import WorkspaceType
from .base import Response


class WorkspaceCreateRequest(BaseModel):
    name: str


class WorkspaceResponse(Response):
    """API Response schema."""
    name: str
    type: WorkspaceType


class WorkspaceModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    name: str
    type: WorkspaceType
