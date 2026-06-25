from pydantic import BaseModel, AwareDatetime
import uuid


class Response(BaseModel):
    """
    Base API Response schema.

    Use as a mixin for response schemas.
    """
    id: uuid.UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime
