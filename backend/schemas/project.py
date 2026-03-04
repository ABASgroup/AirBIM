from pydantic import BaseModel
from datetime import datetime
from models.project import ProjectStatus


class ProjectCreate(BaseModel):
    """Create in DB schema"""
    workspace_id: int
    name: str = "New project"
    description: str
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdate(BaseModel):
    """Update in DB schema"""
    name: str
    description: str
    role: ProjectStatus


class ProjectPublic(BaseModel):
    """API Response schema"""
    workspace_id: int
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
