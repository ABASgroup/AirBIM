import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseRepository
from sqlalchemy.orm import selectinload
from models.task import Task


class TaskRepository(BaseRepository[Task]):
    """Repository class for CRUD operations with Task model."""
    _model = Task
