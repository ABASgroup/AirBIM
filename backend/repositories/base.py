"""Base repository for CRUD operations."""
import uuid
from typing import Generic, TypeVar, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.base import BaseModel

# Type parameter bound to your SQLAlchemy models
ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """
    Base repository class for CRUD operations for any  SQLAlchemy model.

    Override '_model' property to use with some specific model.
    """
    _model: type[ModelT]

    @classmethod
    async def create(cls, data: dict, session: AsyncSession) -> ModelT:
        """Create an entry in the database.

        Args:
            data (`dict`): a dictionary with required data
            session (`AsyncSession`): an asynchronous database session
        """
        entry = cls._model(**data)
        session.add(instance=entry)
        await session.flush()
        # this makes a request to the DB when you create something
        # can we get rid of that safely?
        await session.refresh(entry)
        return entry

    @classmethod
    async def get_all(cls, session: AsyncSession, relations: list[str] | None = None) -> Sequence[ModelT]:
        """Get all model's entries in the database.

        Args:
            session (`AsyncSession`): an asynchronous database session
            relations (`list[str] | None`): a list of relationship names to load
        """
        options = []

        if relations:
            options = [selectinload(getattr(cls._model, relation))
                       for relation in relations]

        stmt = select(cls._model).options(*options)

        result = await session.execute(stmt)
        entries = result.scalars().all()
        return entries

    @classmethod
    async def get_by_id(
        cls,
        entry_id: uuid.UUID,
        session: AsyncSession,
        relations: list[str] | None = None
    ) -> None | ModelT:
        """Get a model entry by the ID/primary key.

        Args:
            entry_id (`uuid.UUID`): entry's ID OR primary key
            session (`AsyncSession`): an asynchronous database session
            relations (`list[str] | None`): a list of relationship names to load
        """
        options = []

        if relations:
            options = [selectinload(getattr(cls._model, relation))
                       for relation in relations]

        entry = await session.get(cls._model, entry_id, options=options)

        if entry is not None and relations:
            await session.refresh(entry, attribute_names=relations)

        return entry

    @classmethod
    async def get_by_ids(cls, entry_ids: list[uuid.UUID], session: AsyncSession, relations: list[str] | None = None) -> Sequence[ModelT]:
        """Get all rows by the IDs.

        Args:
            entry_ids (`list[uuid.UUID]`): entry IDs
            session (`AsyncSession`): an asynchronous database session
            relations (`list[str] | None`): a list of relationship names to load
        """
        options = []

        if relations:
            options = [selectinload(getattr(cls._model, relation))
                       for relation in relations]

        stmt = select(cls._model).where(
            cls._model.id.in_(entry_ids)).options(*options)

        result = await session.execute(stmt)

        return result.scalars().all()

    @classmethod
    async def update_by_id(
        cls,
        entry_id: uuid.UUID,
        update_data: dict,
        session: AsyncSession
    ):
        """Update an entry with new data by its ID/primary key.

        Args:
            entry_id (`uuid.UUID`): entry's ID OR primary key
            update_data (`dict`): a dictionary with new data
            session (`AsyncSession`): an asynchronous database session
        """
        entry = await cls.get_by_id(entry_id, session)

        for key, value in update_data.items():
            setattr(entry, key, value)

        await session.flush()
        await session.refresh(entry)
        return entry

    @classmethod
    async def update(
        cls,
        entry: ModelT,
        update_data: dict,
        session: AsyncSession
    ):
        """Update an entry with new data by its ID/primary key.

        Args:
            entry_id (`uuid.UUID`): entry's ID OR primary key
            update_data (`dict`): a dictionary with new data
            session (`AsyncSession`): an asynchronous database session
        """
        for key, value in update_data.items():
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
    async def delete_by_id(cls, entry_id: uuid.UUID, session: AsyncSession) -> ModelT | None:
        """Delete an entry by its ID/primary key.

        Args:
            entry_id (`uuid.UUID`): entry's ID OR primary key
            session (`AsyncSession`): an asynchronous database session
        """
        entry = await cls.get_by_id(entry_id, session)

        await session.delete(entry)
        await session.flush()
        return entry

    @classmethod
    async def refresh(
        cls,
        entry: ModelT,
        session: AsyncSession,
        relations: list[str] | None = None
    ):
        """
        Refresh model fields.

        Useful when you need to load additional fields on relationship.

        Args:
            entry_id (`uuid.UUID`): entry itself, which you need to refresh
            session (`AsyncSession`): an asynchronous database session
            relations (`list[str]`): list of relations to refresh (if None, only uploaded relations will be refreshed)
        """
        await session.refresh(entry, attribute_names=relations)
        return entry
