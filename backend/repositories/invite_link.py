import uuid
from typing import Sequence
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from models.invite_link import InviteLink
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from core.roles import Role


class InviteLinkRepository(BaseRepository[InviteLink]):
    """Repository class for CRUD operations with InviteLink model."""
    _model = InviteLink

    @classmethod
    async def delete_by_workspace_id(cls, workspace_id: uuid.UUID, session: AsyncSession):
        """Delete all invite links for the workspace."""
        stmt = delete(cls._model).where(
            cls._model.workspace_id == workspace_id)
        await session.execute(stmt)

    @classmethod
    async def get_by_token(cls, token_hashed: str, session: AsyncSession) -> InviteLink | None:
        """Get invite link using its token."""
        stmt = select(cls._model).options(
            selectinload(cls._model.created_by),
            selectinload(cls._model.workspace)
        ).where(
            cls._model.token_hashed == token_hashed)
        result = await session.execute(stmt)
        link = result.scalar_one_or_none()
        return link
    
    @classmethod
    async def get_by_workspace_id(cls, workspace_id: uuid.UUID, session: AsyncSession) -> Sequence[InviteLink]:
        """Get all invite links for the workspace."""
        stmt = select(cls._model).options(
            selectinload(cls._model.created_by),
            selectinload(cls._model.workspace)
        ).where(
            cls._model.workspace_id == workspace_id)
        result = await session.execute(stmt)
        links = result.scalars().all()
        return links