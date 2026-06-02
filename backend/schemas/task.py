from uuid import UUID
from pydantic import BaseModel, field_validator
from models.task import TaskType, TaskStatus
from .base import Response


class TaskModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    celery_task_id: UUID
    workspace_id: UUID
    progress: int = 0
    type: TaskType
    status: TaskStatus

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, value: int) -> int:
        if not (0 <= value <= 100):
            raise ValueError("Progress must be in range from 0 to 100.")
        return value


class TaskResponse(Response):
    """API Response schema."""
    celery_task_id: UUID
    workspace_id: UUID
    progress: int
    type: TaskType
    status: TaskStatus
