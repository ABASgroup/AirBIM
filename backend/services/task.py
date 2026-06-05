"""Service layer logic for tasks."""
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task, TaskStatus
from repositories.task import TaskRepository
from schemas.task import TaskModel, TaskUpdateModel
from core.exceptions import NotFoundError


class TaskService:
    @classmethod
    async def create_task(
        cls,
        task_data: TaskModel,
        session: AsyncSession
    ) -> Task:
        """
        Create a new task.

        This task is just a pending operation with no progress.
        """
        task = await TaskRepository.create(
            task_data.model_dump(exclude_unset=True),
            session=session
        )

        await session.flush()
        return task

    @classmethod
    async def start_task(
        cls,
        task_id: UUID,
        celery_task_id: str,
        session: AsyncSession
    ) -> Task:
        """
        Start the task.

        Attach Celery id and mark task as started.
        """
        task = await cls.get_task(task_id, session=session)

        task_update_data = TaskUpdateModel(
            celery_task_id=celery_task_id,
            status=TaskStatus.STARTED,
        )
        task = await TaskRepository.update(
            task,
            task_update_data.model_dump(exclude_unset=True),
            session=session,
        )

        await session.flush()
        return task

    @classmethod
    async def get_task(cls, task_id: UUID, session: AsyncSession) -> Task:
        """Get task by id."""
        task = await TaskRepository.get_by_id(task_id, session=session)

        if task is None:
            raise NotFoundError("Task was not found.")

        return task

    @classmethod
    async def update_task_progress(
        cls,
        task_id: UUID,
        progress: int,
        session: AsyncSession
    ) -> Task:
        """Update task progress."""
        task = await cls.get_task(task_id, session=session)

        task_update_data = TaskUpdateModel(progress=progress)
        task = await TaskRepository.update(task, task_update_data.model_dump(exclude_unset=True), session=session)

        await session.flush()
        return task

    @classmethod
    async def update_task_status(
        cls,
        task_id: UUID,
        status: TaskStatus,
        session: AsyncSession
    ) -> Task:
        """Update task status."""
        task = await cls.get_task(task_id, session=session)

        if status == TaskStatus.FAILED or status == TaskStatus.SUCCEEDED:
            task_update_data = TaskUpdateModel(
                status=status, finished_at=datetime.now(timezone.utc))
        else:
            task_update_data = TaskUpdateModel(status=status)
        task = await TaskRepository.update(task, task_update_data.model_dump(exclude_unset=True), session=session)

        await session.flush()
        return task
