import uuid
from pydantic import BaseModel
from models.project import ProjectStatus
from .base import Response


class ProjectCreateRequest(BaseModel):
    name: str = "New project"
    description: str


class ProjectResponse(Response):
    """API Response schema."""
    workspace_id: uuid.UUID
    name: str
    description: str
    status: ProjectStatus


class ProjectUpdate(BaseModel):
    """Update schema. Use to update in DB."""
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    workspace_id: uuid.UUID
    name: str = "New project"
    description: str
    status: ProjectStatus = ProjectStatus.ACTIVE
