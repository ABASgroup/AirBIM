from uuid import UUID
from fastapi import APIRouter, Depends
from core.dependencies import DatabaseSessionUOW, get_database_uow

router = APIRouter(
    prefix="/tasks/{task_id}",
    tags=["tasks"]
)


@router.post(
    "",
)
async def cancel_task(
    workspace_id: UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
):
    """
    """
    return "Canceled"
