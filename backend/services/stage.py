"""Service layer logic for Stage."""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions import NotFoundError
from repositories.stage import StageRepository
from models.stage import Stage
from schemas.stage import StageModel, StageUpdate


class StageService:
    @classmethod
    async def get_stage(cls, stage_id: UUID, session: AsyncSession) -> Stage:
        """Get stage using its ID."""
        stage = await StageRepository.get_by_id(stage_id, relations=["project", "point_cloud"], session=session)

        if stage is None:
            raise NotFoundError("No stage with such ID.")

        return stage

    @classmethod
    async def get_project_stages(cls, project_id: UUID, session: AsyncSession) -> list[Stage]:
        """Get all stages related to the project."""
        stages = await StageRepository.get_by_project_id(
            project_id,
            session=session,
        )
        stages = list(stages)

        return stages

    @classmethod
    async def get_project_stages_chronologically(
            cls,
            stage_1_id: UUID,
            stage_2_id: UUID,
            session: AsyncSession
    ) -> list[Stage]:
        """
        Gets two stages by their IDs chronologically.

        Returns:
            list[Stage, Stage]: old and new stage accordingly
        """
        # get both stages
        stage_1 = await cls.get_stage(stage_1_id, session)
        stage_2 = await cls.get_stage(stage_2_id, session)

        # check their projects
        if not stage_1.project_id == stage_2.project_id:
            raise ValueError("Stages don't belong to the same project.")

        return sorted((stage_1, stage_2), key=lambda stage: stage.start_date)

    @classmethod
    async def create_stage(cls, stage_data: StageModel, session: AsyncSession) -> Stage:
        """
        Create a new stage for the project.
        """
        stage = await StageRepository.create(
            stage_data.model_dump(exclude_unset=True),
            session=session,
        )
        stage = await cls.get_stage(
            stage.id,
            session=session
        )
        return stage

    @classmethod
    async def update_stage(cls, stage_id: UUID, stage_data: StageUpdate, session: AsyncSession):
        """Update stage data."""
        stage = await cls.get_stage(stage_id, session=session)
        stage = await StageRepository.update(
            stage,
            stage_data.model_dump(exclude_unset=True),
            session=session
        )

        return stage

    @classmethod
    async def delete_stage(cls, stage_id: UUID, session: AsyncSession) -> Stage:
        """Delete the stage."""
        stage = await cls.get_stage(stage_id, session=session)

        # drop entry and related entries
        await StageRepository.delete(stage, session=session)

        return stage
