from pydantic import BaseModel
from models.workspace import WorkspaceType
from .base import Response


class WorkspaceCreateRequest(BaseModel):
    name: str
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    """Update schema. Use to update in DB."""
    name: str | None = None
    description: str | None = None


class WorkspaceResponse(Response):
    """API Response schema."""
    name: str
    description: str | None = None
    type: WorkspaceType


class WorkspaceModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    name: str
    type: WorkspaceType
