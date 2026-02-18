"""Dependencies used in the app."""
from fastapi.security import OAuth2PasswordBearer
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

