from uuid import UUID
from fastapi import APIRouter, Depends
from core.dependencies import DatabaseSessionUOW, get_database_uow
from core.roles import Permission
from services.task import TaskService
from api.dependencies import require_task_permission
from schemas.task import TaskResponse

router = APIRouter(
    prefix="/tasks/{task_id}",
    tags=["tasks"]
)


@router.post(
    "/cancel",
    response_model=TaskResponse,
    dependencies=[Depends(require_task_permission(Permission.PROJECT_EDIT))]
)
async def cancel_task(
    task_id: UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    Cancel the task.

    You can call task to be canceled, it would change it's status and prevent further processing.
    """
    async with uow:
        task = await TaskService.cancel_task(task_id, uow.session)
    return task
