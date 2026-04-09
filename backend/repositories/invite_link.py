import uuid
from .base import BaseRepository
from models.invite_link import InviteLink
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from roles import Role


class InviteLinkRepository(BaseRepository[InviteLink]):
    """Repository class for CRUD operations with InviteLink model."""
    _model = InviteLink

    @classmethod
    async def delete_by_workspace_id(cls, workspace_id: uuid.UUID, session: AsyncSession):
        """Delete all invite links for the workspace"""
        stmt = delete(cls._model).where(
            cls._model.workspace_id == workspace_id)
        await session.execute(stmt)

    @classmethod
    async def get_by_workspace_id_and_role(
            cls, workspace_id: uuid.UUID, role: Role, session: AsyncSession) -> InviteLink | None:
        """Get invite link by workspace ID and role"""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.workspace_id == workspace_id)
            .where(cls._model.role == role)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_token(cls, token_hashed: str, session: AsyncSession) -> InviteLink | None:
        """Get invite link using its token"""
        stmt = select(cls._model).where(
            cls._model.token_hashed == token_hashed)
        result = await session.execute(stmt)
        link = result.scalar_one_or_none()
        return link
