from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    workspace_name: str = Field(
        default_factory=lambda data: f"{data['username']} workspace")


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password_hashed: str
