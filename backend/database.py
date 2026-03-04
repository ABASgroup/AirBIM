"""Database related tools. Use to get sessions."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from config import db_config


# SQLAlchemy asynchronous engine
engine = create_async_engine(url=db_config.db_url, echo=True)

# use to work with database
session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session():
    """
    Provides session to an endpoint.

    Use as a dependency.

    Don't forget to use 'session.commit()' when
    making changes in database.

    Otherwise changes will be lost.
    """
    async with session_maker() as session:
        yield session
