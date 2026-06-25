"""Database related tools."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from core.configs.database import database_config


# SQLAlchemy asynchronous engine
# for efficiency we use async engine and sessions
engine = create_async_engine(url=database_config.db_url)

# use to work with database in services
session_maker = async_sessionmaker(engine, expire_on_commit=False)
