from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseRepository
from models.refresh_token import RefreshToken


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository class for CRUD operations with RefreshToken model."""
    _model = RefreshToken

    @classmethod
    async def get_by_token(
        cls,
        token: str,
        session: AsyncSession
    ):
        """Get refresh token entry using its token value."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.token == token)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_user_id(
        cls,
        user_id: UUID,
        session: AsyncSession
    ):
        """Get refresh token entry using user ID."""
        result = await session.execute(
            select(cls._model)
            .where(cls._model.user_id == user_id)
        )
        return result.scalar_one_or_none()
