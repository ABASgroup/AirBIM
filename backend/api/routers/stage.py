import uuid
from fastapi import APIRouter, Depends
from infrastructure.storage import Storage
from schemas.stage import StageResponse
from services import stage as stage_service
from core.roles import Permission

from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)
from api.dependencies import (
    require_stage_permission
)

router = APIRouter(prefix="/stages", tags=["project stages"])


@router.get(
    "/{stage_id}",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_VIEW))],
)
async def get_stage(stage_id: uuid.UUID, uow: DatabaseSessionUOW = Depends(get_database_uow)):
    async with uow:
        stage = await stage_service.get_stage(stage_id, session=uow.session)
    return stage


@router.delete(
    "/{stage_id}",
    response_model=StageResponse,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_DELETE))],
)
async def delete_stage(
    stage_id: uuid.UUID,
    uow: DatabaseSessionUOW = Depends(get_database_uow),
    storage: Storage = Depends(get_storage)
):
    """
    Delete stage and all related data and files.

    Requires permission.
    """
    async with uow:
        stage = await stage_service.delete_stage(stage_id, session=uow.session, storage=storage)
    return stage
