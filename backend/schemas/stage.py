from pydantic import BaseModel
from datetime import datetime


class StageCreate(BaseModel):
    """Create in DB schema"""
    project_id: int


class StagePublic(BaseModel):
    """API Response schema"""
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
