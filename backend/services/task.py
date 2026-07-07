"""Service layer logic for tasks."""
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task, TaskStatus, TaskStep
from repositories.task import TaskRepository, TaskStepRepository
from schemas.task import TaskModel, TaskUpdateModel, TaskStepModel, TaskStepUpdateModel
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

        return task

    @classmethod
    async def start_task(
        cls,
        task_id: UUID,
        session: AsyncSession
    ) -> Task:
        """
        Start the task.

        Attach Celery id and mark task as started.
        """
        task = await cls.get_task(task_id, session=session)

        task_update_data = TaskUpdateModel(
            status=TaskStatus.STARTED,
        )
        task = await TaskRepository.update(
            task,
            task_update_data.model_dump(exclude_unset=True),
            session=session,
        )

        return task

    @classmethod
    async def get_task(cls, task_id: UUID, session: AsyncSession) -> Task:
        """Get task by id."""
        task = await TaskRepository.get_by_id(task_id, session=session)

        if task is None:
            raise NotFoundError("Task was not found.")

        return task

    @classmethod
    async def get_tasks_by_workspace_id(
        cls,
        workspace_id: UUID,
        statuses: list[TaskStatus] | None,
        session: AsyncSession
    ) -> list[Task]:
        """Get all tasks belonging to a workspace."""
        tasks = list(await TaskRepository.get_by_workspace_id(workspace_id, statuses=statuses, session=session))
        return tasks

    @classmethod
    async def update_task_progress(
        cls,
        task_id: UUID,
        progress: float,
        session: AsyncSession
    ) -> Task:
        """
        Update task progress based on the amount of steps finished.

        The current progress is calculated as the ratio of finished steps to total steps, multiplied by 100.

        It will be calculated automatically, make sure you call it after the step is finished to keep data up-to-date.
        """
        task = await cls.get_task(task_id, session=session)

        total_steps = task.steps
        finished_steps = len(await cls.get_finished_task_steps(task_id, session=session))

        if finished_steps == total_steps:
            # all steps are finished, mark task as succeeded
            await cls.update_task_status(
                task_id=task_id,
                status=TaskStatus.SUCCEEDED,
                session=session
            )
        else:
            # update progress of the task
            progress = (finished_steps / total_steps) * 100
            task_update_data = TaskUpdateModel(progress=progress)
            task = await TaskRepository.update(task, task_update_data.model_dump(exclude_unset=True), session=session)

        return task

    @classmethod
    async def update_task_status(
        cls,
        task_id: UUID,
        status: TaskStatus,
        session: AsyncSession
    ) -> Task:
        """
        Update task status.

        If the task is finished (succeeded or failed), the progress is set to 100
        and the finished_at timestamp is set to the current time.
        """
        task = await cls.get_task(task_id, session=session)

        if status in [TaskStatus.FAILED, TaskStatus.CANCELED, TaskStatus.SUCCEEDED]:
            task_update_data = TaskUpdateModel(
                progress=100.0,
                status=status,
                finished_at=datetime.now(timezone.utc)
            )
        else:
            task_update_data = TaskUpdateModel(status=status)
        task = await TaskRepository.update(task, task_update_data.model_dump(exclude_unset=True), session=session)

        return task

    @classmethod
    async def cancel_task(
        cls,
        task_id: UUID,
        session: AsyncSession
    ) -> Task:
        """
        Cancel the task.

        - Changes status to CANCELED and prevents further processing.
        - Deletes all related data.
        """
        task = await cls.update_task_status(task_id=task_id, status=TaskStatus.CANCELED, session=session)
        return task

    @classmethod
    async def add_meta_info(
        cls,
        task_id: UUID,
        meta: str,
        session: AsyncSession
    ):
        """Add meta information to the task."""
        # need to separate info entry
        meta += f"\n{datetime.now(timezone.utc).isoformat()} - {meta}"

        task = await cls.get_task(task_id, session=session)

        task_update_data = TaskUpdateModel(meta=meta)
        task = await TaskRepository.update(task, task_update_data.model_dump(exclude_unset=True), session=session)
        return task

    @classmethod
    async def create_task_step(
        cls,
        step_data: TaskStepModel,
        session: AsyncSession
    ) -> TaskStep:
        """Create a new task step."""
        # check if task exists first
        await cls.get_task(step_data.task_id, session=session)
        task_step = await TaskStepRepository.create(step_data.model_dump(exclude_unset=True), session=session)
        return task_step

    @classmethod
    async def get_finished_task_steps(
        cls,
        task_id: UUID,
        session: AsyncSession
    ) -> list[TaskStep]:
        """Get all finished task steps for a given task."""
        # check if task exists first
        await cls.get_task(task_id, session=session)
        task_steps = await TaskStepRepository.get_finished_steps_by_task_id(task_id, session=session)
        return list(task_steps)

    @classmethod
    async def finish_task_step(
        cls,
        task_id: UUID,
        step_task_id: str,
        finished_at: datetime,
        session: AsyncSession
    ) -> TaskStep:
        """Finish a task step."""
        # check if task exists first
        await cls.get_task(task_id, session=session)
        task_step = await TaskStepRepository.get_by_step_task_id(step_task_id, session=session)

        if not task_step:
            raise ValueError("Task step not found")

        task_step_update_data = TaskStepUpdateModel(finished_at=finished_at)
        task_step = await TaskStepRepository.update(task_step, task_step_update_data.model_dump(exclude_unset=True), session=session)
        return task_step
