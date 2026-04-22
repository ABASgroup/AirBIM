import uuid
import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum
from datetime import datetime
from core.roles import Role
from .base import BaseModel


class TaskStatus(enum.StrEnum):
    """
    Task statuses.

    Represent current state of a task.

    From Celery.
    """
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class Task(BaseModel):
    __tablename__ = "tasks"

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="workspace_types", create_constraint=True),
        nullable=False,
        default=TaskStatus.STARTED
    )
