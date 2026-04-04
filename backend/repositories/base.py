"""Base repository for CRUD operations."""
from typing import Generic, TypeVar, Iterable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel as BaseScheme
from models.base import BaseModel

# type parameter for BaseModel children
ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """
    Base repository class for CRUD operations for any model.

    Override '_model' property to use with some specific model.
    """
    _model: type[ModelT]

    @classmethod
    async def create(cls, data: BaseScheme, session: AsyncSession) -> ModelT:
        """Create an entry in the database.

        Args:
            data (`pydantic.BaseScheme`): pydantic scheme instance with required data
            session (`AsyncSession`): an asynchronous database session
        """
        data_dict = data.model_dump(exclude_unset=True)
        entry = cls._model(**data_dict)
        session.add(instance=entry)
        await session.flush()
        return entry

    @classmethod
    async def get_all(cls, session: AsyncSession) -> Iterable[ModelT] | None:
        """Get all model's entries in the database.

        Args:
            session (`AsyncSession`): an asynchronous database session
        """
        result = await session.execute(select(cls._model))
        entries = result.scalars().all()
        return entries

    @classmethod
    async def get_by_id(cls, entry_id: int, session: AsyncSession) -> None | ModelT:
        """Get a model entry by the ID/primary key.

        Args:
            entry_id (`int`): entry's ID OR primary key
            session (`AsyncSession`): an asynchronous database session
        """
        entry = await session.get(cls._model, entry_id)
        return entry

    @classmethod
    async def update_by_id(
        cls,
        entry_id: int,
        update_data: BaseScheme,
        session: AsyncSession
    ):
        """Update an entry with new data by its ID/primary key.

        Args:
            entry_id (`int`): entry's ID OR primary key
            update_data (`pydantic.BaseScheme`): a pydantic scheme instance with new data
            session (`AsyncSession`): an asynchronous database session
        """
        update_data_dict = update_data.model_dump(exclude_unset=True)
        entry = await session.get(cls._model, entry_id)

        for key, value in update_data_dict.items():
            setattr(entry, key, value)

        await session.flush()
        await session.refresh(entry)
        return entry

    @classmethod
    async def delete(cls, entry: ModelT, session: AsyncSession):
        """Delete entry using its object"""
        await session.delete(entry)
        await session.flush()
        return entry

    @classmethod
    async def delete_by_id(cls, entry_id: int, session: AsyncSession) -> ModelT | None:
        """Delete an entry by its ID/primary key.

        Args:
            entry_id (`int`): entry's ID OR primary key
            session (`AsyncSession`): an asynchronous database session
        """
        entry = await session.get(cls._model, entry_id)

        await session.delete(entry)
        await session.flush()
        return entry
