import uuid
from pydantic import BaseModel
from .base import Response


class StageModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    project_id: uuid.UUID


class StageResponse(Response):
    """API Response schema."""
    project_id: uuid.UUID
