"""Service layer logic for User."""
from sqlalchemy.ext.asyncio import AsyncSession
from core.exceptions.exceptions import (
    InvalidLoginInfoError,
    NotFoundError,
    AlreadyExistsError)
from core.security import get_password_hash, verify_password
from repositories.user import UserRepository
from models.user import User
from schemas.user import UserModel, UserRegisterRequest


async def register_user(user_data: UserRegisterRequest, session: AsyncSession):
    """
    Create a new user in the database.


    """
    try:
        # check if user exists
        user = await UserRepository.get_by_email(user_data.email, session)

        if user is not None:
            raise AlreadyExistsError("user")

        # hide password!
        password_hashed = get_password_hash(user_data.password)

        user_data_db = UserModel(username=user_data.username,
                                 password_hashed=password_hashed,
                                 email=user_data.email)
        user = await UserRepository.create(user_data_db, session=session)
        await session.commit()
        return user
    except Exception:
        await session.rollback()
        raise


async def authenticate_user(email: str, password: str, session: AsyncSession) -> User:
    """Checks user data (email, password)"""
    user = await UserRepository.get_by_email(email, session)

    # check if user exists
    if user is None:
        raise NotFoundError("No user with this email")

    # check password
    if not verify_password(password, user.password_hashed):
        raise InvalidLoginInfoError("Email or password is incorrect")

    return user
