from uuid import UUID
import celery
from celery.exceptions import Ignore
import logging
from core.dependencies import get_database_uow
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.task import TaskService
from models.task import TaskStatus

logger = logging.getLogger(__name__)


class BaseTask(celery_app.Task):
    """
    The base task for every Celery task in the app.

    Every single task must use this class.
    """
    abstract = True

    # base settings for every task
    # define the parameters and values you need
    autoretry_for = (ConnectionError, TimeoutError)
    retry_backoff = True
    retry_backoff_max = 600
    max_retries = 5

    def __call__(self, *args, **kwargs):
        """
        This method is called before task's execution.

        Use it for logic that should be executed before the task's main logic.

        But be careful.
        """
        # check Task status
        if run_async(self._is_canceled(*args, **kwargs)):
            # it will stop the task immediately, without calling on_success / on_failure
            raise Ignore()

        # task is found, mark as started if it's the first step in a process

        # create step

        # run the celery task's main logic (DO NOT TOUCH)
        return super().__call__(*args, **kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Executes on a complete failure (all retries have failed)."""
        logger.error(f"Task {task_id} failed permanently. Reason: {exc}")

        # mark task as failed
        async def mark_failed():
            async with get_database_uow() as uow:
                await TaskService.update_task_status(
                    task_id,
                    status=TaskStatus.FAILED,
                    session=uow.session
                )

        run_async(mark_failed())

        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Executes on a success."""
        logger.info(f"Task {task_id} completed successfully.")

        # update progress of the Task (based on amount of steps completed)

        # if all steps have passed - the task has succeed

        super().on_success(retval, task_id, args, kwargs)

    async def _is_canceled(self, parent_task_id: UUID) -> bool:
        """
        Check the status of the task in the database.
        """
        return False

    async def _update_meta(self, parent_task_id: UUID):
        """
        Update the task's meta with information about this step.
        """
