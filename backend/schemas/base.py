from pydantic import BaseModel
from datetime import datetime
import uuid


class Response(BaseModel):
    """
    Base API Response schema.
    
    Use as a mixin for response schemas.
    """
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
