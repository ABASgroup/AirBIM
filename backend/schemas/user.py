from pydantic import BaseModel, EmailStr, Field
from .base import Response


class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    workspace_name: str = Field(
        default_factory=lambda data: f"{data['username']} workspace")


class UserResponse(Response):
    """API response schema."""
    username: str
    email: EmailStr


class UserModel(BaseModel):
    """Schema in DB. Use to create in DB."""
    username: str
    email: EmailStr
    password_hashed: str


class UserUpdate(BaseModel):
    """Update schema."""
    username: str | None = None
    email: EmailStr | None = None
