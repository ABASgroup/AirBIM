from datetime import datetime, timezone
from uuid import UUID
import logging
from celery.exceptions import Ignore
from core.dependencies import get_database_uow
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.task import TaskService
from models.task import TaskStatus
from schemas.task import TaskStepModel

logger = logging.getLogger(__name__)


class BaseCeleryTask(celery_app.Task):
    """
    The base task for every Celery task in the app.

    Every single task, that is not a periodic or maintenance task, must use this class.
    """
    abstract = True

    # base settings for every task
    # define the parameters and values you need
    autoretry_for = (ConnectionError, TimeoutError)
    retry_backoff = True
    retry_backoff_max = 600
    max_retries = 3

    def __call__(self, *args, **kwargs):
        """
        This method is called before task's execution.

        Use it for logic that should be executed before the task's main logic.

        But be careful, do not change the task .
        """
        task_id = kwargs.get('task_id')
        step_name = self.name.split('.')[-1].replace('_', ' ')
        celery_task_id = self.request.id
        self._step_started_at = datetime.now(timezone.utc)

        # check headers
        if task_id is None:
            self._fail_celery_task(
                "Missing required info: task_id must be provided.")

        # check task status
        if not run_async(self._task_is_ready(task_id)):
            self._fail_celery_task("Task is not ready.")

        # task is found, start task and make a task step
        run_async(self._start(task_id))

        # logging
        message = f"Celery task {celery_task_id} ({step_name}) is starting."
        logger.info(message)
        run_async(self._update_meta(task_id, message))

        # DO NOT TOUCH: run the celery task's main logic
        return super().__call__(*args, **kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Executes on a complete failure (all retries have failed)."""
        task_id = kwargs.get('task_id')
        celery_task_id = self.request.id

        # mark task as failed
        run_async(self._fail(task_id))

        message = f"Celery task {celery_task_id} failed permanently. Reason: {exc}"
        logger.error(message)
        run_async(self._update_meta(task_id, message))

        # DO NOT TOUCH: run the celery task's main logic
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Executes on a success."""
        task_id = kwargs.get('task_id')
        celery_task_id = self.request.id

        message = f"Celery task {celery_task_id} completed successfully."
        logger.info(message)
        run_async(self._update_meta(task_id, message))

        run_async(self._finish(task_id))

        # DO NOT TOUCH: run the celery task's main logic
        return super().on_success(retval, task_id, args, kwargs)

    def _fail_celery_task(self, reason: str = "Unknown error."):
        """
        Set celery task as failed and stop the task execution.

        You can additionally provide a reason for the failure, which will be logged and added to the task's meta.
        """
        celery_task_id = self.request.id

        self.update_state(
            state='FAILURE',
            meta={
                'exc_type': 'ValueError',
                'exc_message': f"{reason}"
            }
        )

        raise Ignore(f"Task aborted {celery_task_id}: {reason}.")

    async def _task_is_ready(self, task_id: UUID) -> bool:
        """
        Check task's status.

        If the task is canceled or failed, task is not ready.
        """
        async with get_database_uow() as uow:
            task = await TaskService.get_task(task_id, uow.session)
            status = task.status
        return status not in [TaskStatus.CANCELED, TaskStatus.FAILED]

    async def _start(self, task_id: UUID):
        """
        Start the task.

        Will set status to started (even if it was already started, 
        we only change the status) and create a new task step (celery task) for the task.
        """
        step_name = self.name.split('.')[-1].replace('_', ' ')
        async with get_database_uow() as uow:
            # task
            await TaskService.start_task(task_id, uow.session)
            # task step
            task_step_data = TaskStepModel(
                task_id=task_id,
                name=step_name,
                step_task_id=self.request.id,
                started_at=self._step_started_at
            )
            await TaskService.create_task_step(task_step_data, uow.session)

    async def _finish(self, task_id: UUID):
        """
        Finish the task step.

        Will set finished_at for the task step and update the progress of the task if required.
        """
        async with get_database_uow() as uow:
            finished_at = datetime.now(timezone.utc)
            # finish task step
            await TaskService.finish_task_step(
                task_id=task_id,
                step_task_id=self.request.id,
                finished_at=finished_at,
                session=uow.session
            )
            # update progress of the Task (based on amount of steps completed)
            await TaskService.update_task_progress(task_id, session=uow.session)

    async def _fail(self, task_id: UUID):
        """
        Mark task as failed.
        """
        async with get_database_uow() as uow:
            finished_at = datetime.now(timezone.utc)
            await TaskService.update_task_status(
                task_id=task_id,
                status=TaskStatus.FAILED,
                session=uow.session
            )
            await TaskService.finish_task_step(
                task_id=task_id,
                step_task_id=self.request.id,
                finished_at=finished_at,
                session=uow.session
            )

    async def _update_meta(self, task_id: UUID, message: str):
        """
        Update the task's meta with information about this step.
        """
        async with get_database_uow() as uow:
            await TaskService.add_meta_info(
                task_id=task_id,
                meta=message,
                session=uow.session
            )
