from uuid import UUID
from core.configs.api import api_config
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """API response schema."""
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RefreshTokenModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    token: str
    user_id: UUID
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc) + timedelta(minutes=api_config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str
