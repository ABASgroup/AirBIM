"""Service layer logic for Stage."""
from sqlalchemy.ext.asyncio import AsyncSession
from storage import Storage
from services.file import FileService
from exceptions.exceptions import NotFoundError
from repositories.stage import StageRepository
from models.stage import Stage
from schemas.stage import StageCreate


async def get_stage(stage_id: int, session: AsyncSession) -> Stage:
    """Get stage using its ID."""
    stage = await StageRepository.get_by_id(stage_id, session=session)

    if stage is None:
        raise NotFoundError("No stage with this ID.")

    return stage


async def get_stage_with_project(stage_id: int, session: AsyncSession) -> Stage:
    """Get stage using its ID, additionally loading the project."""
    stage = await StageRepository.get_by_id_with_project(stage_id, session=session)

    if stage is None:
        raise NotFoundError("No stage with this ID.")

    return stage


async def get_project_stages(project_id: int, session: AsyncSession) -> list[Stage]:
    """Get all stages related to the project."""
    stages = await StageRepository.get_by_project_id(project_id, session=session)
    stages = list(stages)

    if len(stages) == 0:
        raise NotFoundError("Project doesn't have any stages")

    return stages


async def create_stage(stage_data: StageCreate, session: AsyncSession) -> Stage:
    """
    Create a new stage for the project.
    """
    try:
        stage = await StageRepository.create(stage_data, session=session)
        await session.commit()
        return stage
    except Exception:
        await session.rollback()
        raise


async def delete_stage(stage_id: int, session: AsyncSession, storage: Storage) -> Stage:
    """
    Delete stage using its ID.
    """
    try:
        stage = await StageRepository.get_by_id_with_project(stage_id, session=session)

        if stage is None:
            raise NotFoundError("Stage was not found.")

        # clear stage files first
        FileService.clear_stage_files(
            stage.project.workspace_id,
            stage.project.id,
            stage.id,
            storage)

        # drop entry and related entries
        await StageRepository.delete(stage, session=session)

        await session.commit()
        return stage
    except AttributeError as exc:
        await session.rollback()
        raise NotFoundError("Stage was not found.") from exc
    except Exception:
        await session.rollback()
        raise
