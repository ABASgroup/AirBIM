from pydantic import BaseModel
from datetime import datetime
from models.workspace import WorkspaceType


class WorkspaceCreateRequest(BaseModel):
    name: str


class WorkspaceCreate(BaseModel):
    name: str
    type: WorkspaceType


class WorkspacePublic(BaseModel):
    """API Response schema"""
    id: int
    name: str
    type: WorkspaceType
    created_at: datetime
    updated_at: datetime
