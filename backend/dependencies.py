"""Dependencies used in the app."""
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from config import api_config
from database import session_maker


async def get_db_session():
    """
    Provides session to an endpoint.

    Use as a dependency.

    Don't forget to use 'session.commit()' when
    making changes in database.

    Otherwise changes will be lost.
    """
    async with session_maker() as session:
        yield session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get"""
    try:
        payload = jwt.decode(token,
                             api_config.JWT_SECRET_KEY,
                             algorithms=[api_config.JWT_ALGORITHM])
    except JWTError:
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

