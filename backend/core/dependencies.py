"""
Dependencies used in the app.

Common dependencies for different purposes.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from infrastructure.database import session_maker
from infrastructure.storage import Storage


storage_client = Storage()


def get_session_maker():
    """Get database session maker."""
    return session_maker


class DatabaseSessionUOW:
    """
    Async database session manager for use as a Unit of Work.

    Fully controls transactions, handles rollbacks, commits and closes sessions.

    Thus you don't need to write code to handle exceptions or control transaction.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()
        return self

    async def __aexit__(self, exc_type, *args):
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.session.close()

    async def commit(self):
        """Commit changes in the database."""
        if self.session is None:
            raise RuntimeError("DatabaseSessionManager is not active")
        await self.session.commit()

    async def rollback(self):
        """Rollback changes in the database."""
        if self.session is None:
            raise RuntimeError("DatabaseSessionManager is not active")
        await self.session.rollback()


def get_database_uow() -> DatabaseSessionUOW:
    """Get a Unit of Work database session manager bound to the shared session factory."""
    return DatabaseSessionUOW(session_maker)


def get_storage():
    """Get storage."""
    return storage_client
