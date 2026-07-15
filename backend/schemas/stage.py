import uuid
from pydantic import BaseModel, AwareDatetime
from .base import Response


class StageCreateRequest(BaseModel):
    name: str = "New stage"
    description: str | None = None
    start_date: AwareDatetime


class StageModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    project_id: uuid.UUID
    name: str | None = None
    description: str | None = None
    start_date: AwareDatetime


class StageUpdate(BaseModel):
    """Update schema. Use to update in DB."""
    name: str | None = None
    description: str | None = None
    start_date: AwareDatetime | None = None


class StageResponse(Response):
    """API Response schema."""
    project_id: uuid.UUID
    point_cloud_id: uuid.UUID | None = None
    name: str | None = None
    description: str | None = None
    start_date: AwareDatetime
