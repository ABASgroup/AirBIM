from .base import BaseRepository
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[User]):
    """Repository class for CRUD operations with User model."""
    _model = User

    @classmethod
    async def get_by_email(cls, email: str, session: AsyncSession) -> User | None:
        """
        Get a user with some email.
        """
        result = await session.execute(select(User).where(User.email == email))
        entry = result.scalar_one_or_none()
        return entry
