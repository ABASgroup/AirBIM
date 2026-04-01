from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    workspace_name: str = Field(
        default_factory=lambda data: f"{data['username']} workspace")


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password_hashed: str


class UserPublic(BaseModel):
    """API response schema."""   
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime