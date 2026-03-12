"""Service layer logic for User."""
from sqlalchemy.ext.asyncio import AsyncSession
from security import get_password_hash, verify_password
from crud.user import UserCRUD
from models.user import User
from schemas.user import UserCreate, UserRegisterRequest


async def create_user(user_data: UserRegisterRequest, session: AsyncSession):
    """
    Create a new user in the database.
    """
    try:
        # hide password!
        password_hashed = get_password_hash(user_data.password)
        user_data_db = UserCreate(username=user_data.username,
                                  password_hashed=password_hashed,
                                  email=user_data.email)
        user = await UserCRUD.create(user_data_db, session=session)
        await session.commit()
        return user
    except Exception as exc:
        await session.rollback()
        raise Exception from exc


async def is_user_registered(user_data: UserRegisterRequest, session: AsyncSession) -> bool:
    """Checks if the user already has an account"""
    user = await UserCRUD.get_by_email(user_data.email, session)
    return user is not None


async def authenticate_user(email: str, password: str, session: AsyncSession) -> User:
    """Checks user data (email, password)"""
    user = await UserCRUD.get_by_email(email, session)
    # check password
    if not verify_password(password, user.password_hashed):
        raise Exception

    return user
