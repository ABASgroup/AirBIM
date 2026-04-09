"""Database related tools."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from configs import db_config


# SQLAlchemy asynchronous engine
# for efficiency we use async engine and sessions
engine = create_async_engine(url=db_config.db_url, echo=True)

# use to work with database in services
session_maker = async_sessionmaker(engine, expire_on_commit=False)
