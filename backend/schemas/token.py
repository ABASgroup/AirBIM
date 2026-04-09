from pydantic import BaseModel


class TokenResponse(BaseModel):
    """API response schema."""
    access_token: str
    token_type: str = 'bearer'
