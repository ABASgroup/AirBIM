from .base import BaseCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.membership import Membership


class MembershipCRUD(BaseCRUD[Membership]):
    """DAO class for CRUD operations with Membership model."""
    _model = Membership

    @classmethod
    async def get_user_workspace_membership(
        cls,
        user_id: int,
        workspace_id: int,
        session: AsyncSession
    ):
        """Get user membership in the workspaces using their IDs"""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.workspace_id == workspace_id)
            .where(cls._model.user_id == user_id)
        )
        return result.scalars().one_or_none()
