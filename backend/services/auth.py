"""Service layer logic for User."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions import (
    InvalidLoginInfoError,
    NotFoundError,
    AlreadyExistsError,
    InvalidTokenError
)
from core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from repositories.user import UserRepository
from repositories.refresh_token import RefreshTokenRepository
from models.user import User
from schemas.user import UserModel, UserRegisterRequest
from schemas.token import RefreshTokenModel


async def register_user(user_data: UserRegisterRequest, session: AsyncSession):
    """
    Create a new user in the database.
    """
    # check if user exists
    user = await UserRepository.get_by_email(user_data.email, session)

    if user is not None:
        raise AlreadyExistsError("user")

    # hide password!
    password_hashed = get_password_hash(user_data.password)

    user_data_db = UserModel(username=user_data.username,
                             password_hashed=password_hashed,
                             email=user_data.email)
    user = await UserRepository.create(user_data_db.model_dump(exclude_unset=True), session=session)
    return user


async def authenticate_user(email: str, password: str, session: AsyncSession) -> User:
    """Checks user data (email, password)"""
    user = await UserRepository.get_by_email(email, session)

    # check email and password
    if user is None or not verify_password(password, user.password_hashed):
        raise InvalidLoginInfoError("Email or password is incorrect")

    return user


async def create_tokens(user_id: uuid.UUID, session: AsyncSession) -> tuple[str, str]:
    """
    Creates new access and refresh tokens.

    Returns both tokens respectively.
    """
    old_token = await RefreshTokenRepository.get_by_user_id(
        user_id,
        session=session
    )

    if old_token:
        await RefreshTokenRepository.delete(old_token, session=session)

    refresh_token = create_refresh_token(user_id)

    refresh_token_db = RefreshTokenModel(
        token=refresh_token,
        user_id=user_id,
    )

    await RefreshTokenRepository.create(refresh_token_db.model_dump(), session=session)
    access_token = create_access_token(user_id)

    return access_token, refresh_token


async def update_tokens(user_id: uuid.UUID, session: AsyncSession):
    """
    Creates new access and refresh tokens.

    Old refresh token validation is required.
    """
    old_token = await RefreshTokenRepository.get_by_user_id(
        user_id,
        session=session
    )

    if old_token is None:
        raise InvalidTokenError("refresh token is not found")

    await RefreshTokenRepository.delete(old_token, session=session)

    new_refresh_token = create_refresh_token(user_id)

    refresh_token_db = RefreshTokenModel(
        token=new_refresh_token,
        user_id=user_id,
    )

    await RefreshTokenRepository.create(refresh_token_db.model_dump(), session=session)
    access_token = create_access_token(user_id)

    return access_token, new_refresh_token
