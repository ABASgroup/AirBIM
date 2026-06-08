"""Base model of the API database."""
from datetime import datetime
import uuid
from sqlalchemy import func, UUID, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


class BaseModel(AsyncAttrs, DeclarativeBase):
    """
    Base abstract database model.

    All of the models must inherit this model.
    """
    __abstract__ = True
    
    # to correctly load default values
    __mapper_args__ = {
        "eager_defaults": True
    }

    # to correctly load default values
    __mapper_args__ = {
        "eager_defaults": True
    }

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        unique=True,
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
