"""Service layer logic for Stage."""
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exceptions import NotFoundError
from crud.stage import StageCRUD
from models.stage import Stage
from schemas.stage import StageCreate


async def get_stage(stage_id: int, session: AsyncSession) -> Stage:
    """Get stage using its ID."""
    stage = await StageCRUD.get_by_id(stage_id, session=session)

    if stage is None:
        raise NotFoundError("No stage with this ID.")

    return stage


async def get_stage_with_project(stage_id: int, session: AsyncSession) -> Stage:
    """Get stage using its ID, additionally loading the project."""
    stage = await StageCRUD.get_by_id_with_project(stage_id, session=session)

    if stage is None:
        raise NotFoundError("No stage with this ID.")

    return stage


async def get_project_stages(project_id: int, session: AsyncSession) -> list[Stage]:
    """Get all stages related to the project."""
    stages = await StageCRUD.get_by_project_id(project_id, session=session)
    stages = list(stages)

    if len(stages) == 0:
        raise NotFoundError("Project doesn't have any stages")

    return stages


async def create_stage(stage_data: StageCreate, session: AsyncSession) -> Stage:
    """
    Create a new stage for the project.
    """
    try:
        stage = await StageCRUD.create(stage_data, session=session)
        await session.commit()
        return stage
    except Exception:
        await session.rollback()
        raise


async def delete_stage(stage_id: int, session: AsyncSession) -> Stage:
    """
    Delete stage using its ID.
    """
    try:
        stage = await StageCRUD.delete_by_id(stage_id, session=session)
        await session.commit()
        return stage
    except AttributeError as exc:
        await session.rollback()
        raise NotFoundError("Stage was not found.") from exc
    except Exception:
        await session.rollback()
        raise
