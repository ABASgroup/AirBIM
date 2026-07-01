import uuid
from .base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from models.membership import Membership


class MembershipRepository(BaseRepository[Membership]):
    """Repository class for CRUD operations with Membership model."""
    _model = Membership

    @classmethod
    async def get_all_workspace_users(
        cls,
        workspace_id: uuid.UUID,
        session: AsyncSession
    ):
        """
        Get all memberships in the workspace using its ID.

        Also loads user data with membership data.
        """
        result = await session.execute(
            select(cls._model)
            .options(selectinload(cls._model.user))
            .where(cls._model.workspace_id == workspace_id)
        )
        return result.scalars().all()

    @classmethod
    async def get_user_workspace_membership(
        cls,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession
    ):
        """Get user membership in the workspaces using their IDs"""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.workspace_id == workspace_id)
            .where(cls._model.user_id == user_id)
        )
        return result.scalars().one_or_none()

    @classmethod
    async def get_all_user_memberships(cls, user_id: uuid.UUID, session: AsyncSession):
        """Get all user memberships using their ID."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.user_id == user_id)
        )
        return result.scalars().all()

    @classmethod
    async def delete_user_workspace_membership(
        cls,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        session: AsyncSession
    ) -> Membership | None:
        """Delete user's membership in the workplace, removing them from it"""
        stmt = delete(cls._model).where(cls._model.workspace_id ==
                                        workspace_id).where(cls._model.user_id == user_id)
        await session.execute(stmt)
