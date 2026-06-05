"""Service layer logic for Stage."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.storage import Storage
from core.exceptions import NotFoundError
from repositories.stage import StageRepository
from models.stage import Stage
from schemas.stage import StageModel


async def get_stage(stage_id: uuid.UUID, session: AsyncSession) -> Stage:
    """Get stage using its ID."""
    stage = await StageRepository.get_by_id(stage_id, session=session)

    if stage is None:
        raise NotFoundError("No stage with this ID.")

    return stage


async def get_stage_with_project(stage_id: uuid.UUID, session: AsyncSession) -> Stage:
    """Get stage using its ID, additionally loading the project."""
    stage = await StageRepository.get_by_id_with_project(stage_id, session=session)

    if stage is None:
        raise NotFoundError("No stage with this ID.")

    return stage


async def get_project_stages(project_id: uuid.UUID, session: AsyncSession) -> list[Stage]:
    """Get all stages related to the project."""
    stages = await StageRepository.get_by_project_id(project_id, session=session)
    stages = list(stages)

    if len(stages) == 0:
        raise NotFoundError("Project doesn't have any stages")

    return stages


async def create_stage(stage_data: StageModel, session: AsyncSession) -> Stage:
    """
    Create a new stage for the project.
    """
    stage = await StageRepository.create(stage_data.model_dump(exclude_unset=True), session=session)
    return stage


async def delete_stage(stage_id: uuid.UUID, session: AsyncSession, storage: Storage) -> Stage:
    try:
        stage = await StageRepository.get_by_id_with_project(stage_id, session=session)

        if stage is None:
            raise NotFoundError("Stage was not found.")

        # drop entry and related entries
        await StageRepository.delete(stage, session=session)

        return stage
    except AttributeError as exc:
        raise NotFoundError("Stage was not found.") from exc
