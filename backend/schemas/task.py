from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator
from models.task import TaskType, TaskStatus
from .base import Response


class TaskModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    entity_id: UUID
    entity_type: str
    celery_task_id: str | None = None
    workspace_id: UUID
    progress: int = 0
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, value: int) -> int:
        if not (0 <= value <= 100):
            raise ValueError("Progress must be in range from 0 to 100.")
        return value


class TaskUpdateModel(BaseModel):
    """Schema for updating task."""
    progress: int | None = None
    celery_task_id: str | None = None
    status: TaskStatus | None = None
    finished_at: datetime | None = None

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, value: int | None) -> int | None:
        if value is not None and not (0 <= value <= 100):
            raise ValueError("Progress must be in range from 0 to 100.")
        return value


class TaskResponse(Response):
    """API Response schema."""
    celery_task_id: str | None = None
    workspace_id: UUID
    progress: int
    type: TaskType
    status: TaskStatus
    entity_id: UUID
    entity_type: str
    started_at: datetime
    finished_at: datetime | None
