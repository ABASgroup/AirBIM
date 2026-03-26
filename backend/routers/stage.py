from sqlalchemy.ext.asyncio import AsyncSession
from schemas.stage import StagePublic
from services import stage as stage_service
from roles import Permission
from fastapi import APIRouter, Depends

from dependencies import (
    get_db_session,
    require_stage_permission,
)

from roles import Permission


router = APIRouter(prefix="/stage", tags=["project stages"])


@router.get(
    "/{stage_id}",
    response_model=StagePublic,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_VIEW))],
)
async def get_stage(stage_id: int, session: AsyncSession = Depends(get_db_session)):
    stage = await stage_service.get_stage(stage_id, session=session)
    return stage


@router.delete(
    "/{stage_id}",
    response_model=StagePublic,
    dependencies=[
        Depends(require_stage_permission(Permission.STAGE_DELETE))],
)
async def delete_project(
    stage_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    projestagect = await stage_service.delete_stage(stage_id, session=session)
    return stage
